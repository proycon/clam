

$(document).ready(function(){
   if (inputtemplates == undefined) {
        alert("System error: data.js not properly loaded?");
   }

   //Download parameters.xsl so it's available to javascript for file-parameters
   $.ajax({ 
        type: "GET", 
        url: baseurl + "/static/parameters.xsl",
        dataType: "xml", 
        success: function(xml){ 
            parametersxsl = xml;
        },
   });
    
   //Create lists of all possible inputtemplates (aggregated over all profiles)
   var inputtemplate_options = "";
   for (var i = 0; i < inputtemplates.length; i++) {
        inputtemplate_options += '<option value="">Select a filetype...</option><option value="' + inputtemplates[i].id + '">' + inputtemplates[i].label + '</option>';
   }
   $(".inputtemplates").html(inputtemplate_options);

   //Tying events to trigger rendering of file-parameters when an inputtemplate is selected:
   $("#uploadinputtemplate").change(function(event){renderfileparameters($('#uploadinputtemplate').val(),'#uploadparameters',true); });
   $("#urluploadinputtemplate").change(function(event){renderfileparameters($('#urluploadinputtemplate').val(),'#urluploadparameters',true);});
   $("#editorinputtemplate").change(function(event){
        renderfileparameters($('#editorinputtemplate').val(),'#editorparameters',false);
        var inputtemplate = getinputtemplate('#editorinputtemplate');
        if (inputtemplate != null) {
            if (inputtemplate.filename) {
                $('#editorfilename').val(inputtemplate.filename);
            }
        }
    });


   //Create a new project
       if ($("#startprojectbutton").length) {
       $("#startprojectbutton").click(function(event){
         $.ajax({ 
            type: "PUT", 
            url: $("#projectname").val() + "/", 
            dataType: "text", 
            success: function(response){ 
                window.location.href = $("#projectname").val() + "/";
            },
            error: function(response){
                alert("Unable to create project");   
            }
         });
         //$("#startprojectform").attr("action",$("#projectname").val());
       });
   }

   //Abort and delete a project
   if ($("#abortbutton").length) {
       $("#abortbutton").click(function(event){
         $.ajax({ 
            type: "DELETE", 
            url: window.location.href, 
            dataType: "text", 
            success: function(response){ 
                window.location.href = "/"; /* back to index - TODO: FIX, doesn't work with urlprefix! */
            },
            error: function(response){
                alert("Unable to delete project");   
            }
         });         
       });
   }    

   //Restart a project (deleting only its output)
   if ($("#restartbutton").length) {
       $("#restartbutton").click(function(event){
         $.ajax({ 
            type: "DELETE", 
            url: "output/" , 
            dataType: "text", 
            success: function(xml){ 
                window.location.href = ""; /* refresh */
            },
            error: function(response){
                alert("Unable to delete output files");   
            }
         });         
       });
   }    

   //Return to index
   if ($("#indexbutton").length) {
       $("#indexbutton").click(function(event){
            window.location.href = "../"; /* refresh */
       });
   }  


   //Tables for input files and output files
   tableinputfiles = $('#inputfiles').dataTable( {
                                "bJQueryUI": false,
                                "sPaginationType": "full_numbers"
                         });
   
   $('#outputfiles').dataTable( {
				"bJQueryUI": false,
				"sPaginationType": "full_numbers"
			});
   $('#projects').dataTable( {
				"bJQueryUI": false,
				"sPaginationType": "full_numbers"
			});


   //Open in-browser editor
   $("#openeditor").click(function(event){ $("#mask").show(); $("#editor").slideDown(); })


   //Submit data through in-browser editor
   $("#editorsubmit").click(function(event){ 
        $("#editor").slideUp(400, function(){ $("#mask").hide(); } ); 
        var filename = validateuploadfilename($('#editorfilename').val(), $('#editorinputtemplate').val());
        if (!filename) {
             //alert already produced by getuploadfilename()
             return false;
        }
        

        var data = {'contents': $('#editorcontents').val(), 'inputtemplate': $('#editorinputtemplate').val() };
        addformdata('#editorparameters', data );
        $.ajax({ 
            type: "POST", 
            url: "input/" + filename, 
            dataType: "xml", 
            data: data, 
            success: function(response){ 
                processuploadresponse(response);
            },
            error: function(response, errortype){
                alert("An error occured while attempting to upload the text: " + errortype + "\n" + response);
            }            
        });            
        return true;
   });
   $("#canceleditor").click(function(event){  $("#editor").slideUp(400, function(){ $("#mask").hide(); } ); return false; });

   //Download and add from URL
   $('#urluploadsubmit').click(function(event){
            var filename = validateuploadfilename($('#urluploadfile').val(),$('#urluploadinputtemplate').val());
            if (!filename) {
               //alert already produced by getuploadfilename()
               return false;
            }

            $('#urlupload').hide();
            $('#urluploadprogress').show();
            
            $.ajax({ 
                type: "POST", 
                url: "input/" + filename, 
                dataType: "xml", 
                data: {'url': $('#urluploadfile').val(), 'inputtemplate': $('#urluploadinputtemplate').val() }, 
                success: function(response){
                    processuploadresponse(response);
                    $('#urluploadprogress').hide();                     
                    $('#urlupload').show();
                },
                error: function(response, errortype){
                    alert("An error occured while attempting to fetch this file. Please verify the URL is correct and up: " + errortype);
                    $('#urluploadprogress').hide();                     
                    $('#urlupload').show();
                }                
            });              
    });

   //Upload through browser
   if ($('#uploadbutton')) {    
       uploader = new AjaxUpload('uploadbutton', {action: 'input/', name: 'file', data: {'inputtemplate': $('#uploadinputtemplate').val()} , 
            onChange: function(filename,extension){
                 var inputtemplate_id = $('#uploadinputtemplate').val();
                 var filename = validateuploadfilename(filename,inputtemplate_id);
                 if (!filename) {
                    return false;
                 } else {
                     uploader._settings.action = 'input/' + filename
                     uploader._settings.data.inputtemplate = inputtemplate_id;
                     addformdata( '#uploadparameters', uploader._settings.data );
                 }
            },
            onSubmit: function(){
                $('#clientupload').hide();
                $('#uploadprogress').show();           
            },  
            onComplete: function(file, response){
                processuploadresponse(response);
                $('#uploadprogress').hide();
                $('#clientupload').show();
            }       
        }); 
   }



});  //ready


function addformdata(parent, data) {
    var fields = $(parent).find(':input');    
    $(fields).each(function(){ //also works on textarea, select, button!
        if (this.name != undefined) {
            data[this.name] = $(this).val();
        }
    });
}

function processuploadresponse(response) {
      //Processes CLAM Upload XML
      
      $(response).find('upload').each(function(){       //for each uploaded file
        var children = $(this).children();
        var inputtemplate = $(this).attr('inputtemplate');
        var metadataerror = false;
        var conversionerror = false;
        var parametererrors = false;
        var valid = false;
        for (var i = 0; i < children.length; i++) {
            if ($(children[i]).is('parameters')) { //see if parameters validate
                if ($(children[i]).attr('errors') == 'no') {
                    parametererrors = false;
                } else {
                    parametererrors = true;
                }
            } else if ($(children[i]).is('metadataerror')) { //see if there is no metadata error
                metadataerror = true;
            } else if ($(children[i]).is('conversionerror')) { //see if there is no conversion error
                conversionerror = true;
            } else if ($(children[i]).is('valid')) {
                if ($(children[i]).text() == "yes") {
                    valid = true;
                } else {
                    valid = false;
                }                
            }
        }
          
        if ((valid) && (!parametererrors) && (!metadataerror)) {
            //good! 
            
            //Check if file already exists in input table
            var found = false;
            var data = tableinputfiles.fnGetData();
            for (var i = 0; i < data.length; i++) {
                if (data[i][0].match('>' + $(this).attr('name') + '<') != null) {
                    found = true;
                    break;
                }
            }
            
            //Add this file to the input table if it doesn't exist yet
            if (!found) {
                tableinputfiles.fnAddData( [  '<a href="input/' + $(this).attr('filename') + '">' + $(this).attr('filename') + '</a>', $(this).attr('templatelabel'), '' ,'<img src="/static/delete.png" title="Delete this file" onclick="deleteinputfile(\'' +$(this).attr('target') + '\');" />' ] )
            }
            
         //TODO: Make errors nicer, instead of alerts, propagate to interface
        } else if (metadataerror) {
            alert("A metadata error occured, contact the service provider");
        } else if (conversionerror) {
            alert("The file you uploaded could not be converted with the specified converter");
        } else if (parametererrors) {
            alert("There were parameter errors");
            //TODO: Specify what parameter errors occured
        } else if (!valid) {
            alert("The file you uploaded did not validate, it's probably not of the type you specified");
        }
    
    });  
}


function getinputtemplate(id) {
    for (var i = 0; i < inputtemplates.length; i++) {
        if (inputtemplates[i].id == id) {
           return inputtemplates[i]
        }
    }
    return null;
}

function validateuploadfilename(filename, inputtemplate_id) {
    var inputtemplate = getinputtemplate(inputtemplate_id)
    if (inputtemplate == null) {
        alert('Select a valid input type first!');
        return false;
    }
    //var filename = sourcefilename.match(/[\/|\\]([^\\\/]+)$/); //os.path.basename
    
    if (inputtemplate.filename) {
        //inputtemplate forces a filename:
        filename = inputtemplate.filename;
    } else if (inputtemplate.extension) {
        //inputtemplate forces an extension:
        var l = inputtemplate.extension.length;
        var tmp = filename.substr(filename.length - l, l);
        //if the desired extension is not provided yet (server will take care of case mismatch), add it:
        if (!(filename.substr(filename.length - l - 1, l+1).toLowerCase() == '.' + inputtemplate.extension.toLowerCase())) {
            filename = filename + '.' + inputtemplate.extension
        }
    }
    return filename;
}




function renderfileparameters(id, target, enableconverters) {
    if (id == "") {
        $(target).html("");
    } else {
        inputtemplate = getinputtemplate(id);
        if (inputtemplate) {
            if (document.implementation && document.implementation.createDocument) {
                //For decent browsers (Firefox, Opera, Chromium, etc...)    
                xsltProcessor=new XSLTProcessor();
                xsltProcessor.importStylesheet(parametersxsl); //parametersxsl global, automatically loaded at start            
                var xmldoc = $(inputtemplate.parametersxml)[0];
                //var s = (new XMLSerializer()).serializeToString(xmldoc);
                //alert(s);
                
                result = xsltProcessor.transformToFragment(xmldoc, document);
                //var s = (new XMLSerializer()).serializeToString(result);
                //alert(s);
            } else if (window.ActiveXObject) { //For evil sucky non-standard compliant browsers ( == Internet Explorer)
                result = inputtemplate.parametersxml.transformNode(xsl); //VERIFY
            } else {
                result = "<strong>Error: Unable to render parameter form!</strong>";
            }
            $(target).html(result);
            if ((enableconverters) && ($(inputtemplate.converters))) {
                var s = "Automatic conversion: <select name=\"converter\">";
                s += "<option value=\"\">No</option>";
                for (var i = 0; i < inputtemplate.converters.length; i++) {
                    s += "<option value=\"" + inputtemplate.converters[i].id + "\">" + inputtemplate.converters[i].label + "</option>";
                }
                s += "</select><br />";
                $(target).prepend(s);
            }
        } else {
            $(target).html("<strong>Error: Selected input template is invalid!</strong>");
        }
    }
}


function deleteinputfile(filename) {   
    var found = -1;
    var data = tableinputfiles.fnGetData();
    for (var i = 0; i < data.length; i++) {
        if (data[i][0].match('>' + filename + '<') != null) {
            found = i;
            break;
        }
    }   
    if (found >= 0) tableinputfiles.fnDeleteRow(found);
    $.ajax({ 
        type: "DELETE", 
        url: "input/" + filename, 
        dataType: "xml"
    });    
}

function setinputsource(tempelement) {
    var src = tempelement.value;
    $('#usecorpus').val(src);
    if (src == '') {
        $('#inputfilesarea').show();
        $('#uploadarea').show();
    } else {
        $('#inputfilesarea').hide();
        $('#uploadarea').hide();
    }
}

