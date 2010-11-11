

$(document).ready(function(){

   //Download parameters.xsl so it's available to javascript for file-parameters
   $.ajax({ 
        type: "GET", 
        url: baseurl + "/static/parameters.xsl",
        dataType: "xml", 
        complete: function(xml){ 
            parametersxsl = xml;
        },
   });
    
   //Create lists of all possible inputtemplates (aggregated over all profiles)
   var inputtemplates_options = "";
   for (var i = 0; i < inputtemplate.length; i++) {
        inputtemplate_options += '<option value="">Select a filetype...</option><option value="' + inputtemplate.id + '">' + inputtemplate.label + '</option>';
   }
   $(".inputtemplates").html(inputtemplate_options);

   //Tying events to trigger rendering of file-parameters when an inputtemplate is selected:
   $("#uploadinputtemplate").change(function(event){renderfileparameters($('#uploadinputtemplate').val(),'#uploadparameters');};
   $("#urluploadinputtemplate").change(function(event){renderfileparameters($('#urluploadinputtemplate').val(),'#urluploadparameters');};
   $("#editorinputtemplate").change(function(event){renderfileparameters($('#editorinputtemplate').val(),'#editorparameters');};


   //Create a new project
   if ($("#startprojectbutton").length) {
       $("#startprojectbutton").click(function(event){
         $.ajax({ 
            type: "PUT", 
            url: $("#projectname").val() + "/", 
            dataType: "xml", 
            complete: function(xml){ 
                window.location.href = $("#projectname").val() + "/";
            },
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
            dataType: "xml", 
            complete: function(xml){ 
                window.location.href = "/"; /* back to index - TODO: FIX, doesn't work with urlprefix! */
            },
         });         
       });
   }    

   //Restart a project (deleting only its output)
   if ($("#restartbutton").length) {
       $("#restartbutton").click(function(event){
         $.ajax({ 
            type: "DELETE", 
            url: "output", 
            dataType: "xml", 
            complete: function(xml){ 
                window.location.href = ""; /* refresh */
            },
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
        //TODO: Validate filename against inputtemplate!     
        var filename = $('#editorfilename').val();
        var d = new Date();    
        if (!filename) {
            filename = d.getTime();        
        }
        $.ajax({ 
            type: "POST", 
            url: "input/" + filename, 
            dataType: "xml", 
            data: {'contents': $('#editorcontents').val(), 'inputtemplate': $('#editorinputtemplate').val(), 'uploadeditorfilename': filename }, 
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
            $('#urlupload').hide();
            $('#urluploadprogress').show();
            //TODO: Determine filename using inputtemplate!     
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
   $('#uploadbutton').click(function(){
       //TODO: Extract filename (check if inputtemplate specified filename/extension first!)
       filename = $('#uploadfile').val().match(/[\/|\\]([^\\\/]+)$/); //VERIFY!
       
       uploader = new AjaxUpload('uploadfile', {action: 'input/' + filename, name: 'uploadfile', data: {'inputtemplate': $('#uploadinputtemplate').val()} , 
            onSubmit: function(){
                $('#clientupload').hide();
                $('#uploadprogress').show();           
            },  onComplete: function(file, response){
                processuploadresponse(response);
                $('#uploadprogress').hide();
                $('#clientupload').show();
            }       
        }); 
   });


});  //ready

function processuploadresponse(response) {
      $(response).find('upload').each(function(){       //for each uploaded file
        var children = $(this).children();
        metadataerror = parametererrors = false;
        for (var i = 0; i < children.length; i++) {
            if ($(children[i]).is('parameters')) { //see if parameters validate
                if ($(children[i]).attr('errors') == 'no') {
                    parametererrors = false;
                } else {
                    parametererrors = true;
                }
            } else if ($(children[i]).is('metadataerror')) { //see if there is no metadata error
                metadataerror = true;
            } else if ($(children[i]).is('valid')) {
                if ($(children[i]).val() == "yes") {
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
                tableinputfiles.fnAddData( [  '<a href="input/' + $(this).attr('target') + '">' + $(this).attr('target') + '</a>', $(this).attr('templatelabel'), '<img src="/static/delete.png" title="Delete this file" onclick="deleteinputfile(\'' +$(this).attr('target') + '\');" />' ] )
            }
            
            
        } else {
            //bad!
            //TODO: propagate error feedback to interface
        }
    
    });  
}


function getinputtemplate(id) {
    for (var i = 0; i <= inputtemplates.length; i++) {
        if (inputtemplates[i].id == id) {
           return inputtemplates[i]
        }
    }
    return null;
}

function getfilename(, filenamefield = null) {
    if (filenamefield) {
        
    }
}



function renderfileparameters(id, target) {
    inputtemplate = getinputtemplate(id);
    if (inputtemplate) {
        if (document.implementation && document.implementation.createDocument)
            //For decent browsers (Firefox, Opera, Chromium, etc...)    
            xsltProcessor=new XSLTProcessor();
            xsltProcessor.importStylesheet(parametersxsl); //parametersxsl global, automatically loaded at start
            result = xsltProcessor.transformToFragment(inputtemplate.parametersxml,document);
        } else if (window.ActiveXObject) { //For evil sucky non-standard compliant browsers ( == Internet Explorer)
            result = inputtemplate.parametersxml.transformNode(xsl); //VERIFY
        } else {
            result = "<strong>Error: Unable to render parameter form!</strong>";
        }
        $(target).html(result);
    } else {
        $(target).html("<strong>Error: Selected input template is invalid!</strong>");
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

function inputtemplate(label, div) {
    for (var i = 0; i < inputtemplates.length; i++) {
        if (inputtemplates[i].label == label) {
            //TODO: Generate inputtemplate form
            form = '<table class="inputtemplate">'
            for (var j = 0; j < inputtemplates[i].metafields.length; j++) {
                form += '<tr><th>' + ' </th></tr>'
            }
            form += '</table>'
            div.innerHTML = div
        }
    }
}

