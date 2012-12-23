

$(document).ready(function(){
   if (typeof(inputtemplates) == 'undefined') {
   		//something went wrong during loading, probably authentication issues, reload page
        window.location.reload(); //alert("System error: data.js not properly loaded?");
   }

   if (typeof(stage) != 'undefined') {
       //Download parameters.xsl so it's available to javascript for file-parameters
       $.ajax({ 
            type: "GET", 
            url: baseurl + "/static/parameters.xsl",
            dataType: "xml", 
            success: function(xml){ 
                parametersxsl = xml;
            }
       });
      if (stage == 1) {
       		$('#progressbar').progressbar({value: progress});
       		setTimeout(pollstatus,2000);
       }
    }

   
   //set custom text
   if ($('#customtextindex').length > 0) {
       $.ajax({
            type: "GET",
            url: baseurl + "/static/custom/" + systemid + '_index.html',
            dataType: "html",
            success: function(data) {
                $('#customtextindex').html(data);
            },
            error: function() {
                $('#customtextindex').hide();
            }
       });
   } 
   if ($('#customtextprojectstart').length > 0) {
        $.ajax({
            type: "GET",
            url: baseurl + "/static/custom/" + systemid + '_projectstart.html',
            dataType: "html",
            success: function(data) {
                $('#customtextprojectstart').html(data);
            },
            error: function() {
                $('#customtextprojectstart').hide();
            }
       });       
   }
   if ($('#customtextprojectdone').length > 0) {
        $.ajax({
            type: "GET",
            url: baseurl + "/static/custom/" + systemid + '_projectdone.html',
            dataType: "html",
            success: function(data) {
                $('#customtextprojectdone').html(data);
            },
            error: function() {
                $('#customtextprojectdone').hide();
            }
       });              
   }
    
    
   //Create lists of all possible inputtemplates (aggregated over all profiles)
   var inputtemplate_options = "<option value=\"\">Select a filetype...</option>";
   var processed = [];
   for (var i = 0; i < inputtemplates.length; i++) {
        var duplicate = false;
        for (var j = 0;j < processed.length; j++) {
            if (inputtemplates[i].id  ==  inputtemplates[j].id) {
                duplicate = true;
                break;
            }
        }
        if (duplicate) continue;
        processed.push(inputtemplates[i].id);     
        inputtemplate_options += '<option value="' + inputtemplates[i].id + '">' + inputtemplates[i].label + '</option>';
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
            url: baseurl + '/' + $("#projectname").val() + "/", 
            dataType: "text", 
            success: function(response){ 
                window.location.href = baseurl + '/' + $("#projectname").val() + "/";
            },
            error: function(response){
                if ((response.status < 200) || (response.status > 299)) { //patch
                    alert("Unable to create project. Do not use spaces or special characters in the ID, only underscores and alphanumeric characters are allowed (" +  response.status +")");   
                }
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
            url: baseurl + '/' + project + '/', 
            dataType: "text", 
            success: function(response){ 
                window.location.href = baseurl + '/'; /* back to index */
            },
            error: function(response){
                if ((response.status < 200) || (response.status > 299)) { //patch
                    alert("Unable to delete project (" + response.status + ")");   
                }
            }
         });         
       });
   }    

   //Restart a project (deleting only its output)
   if ($("#restartbutton").length) {
       $("#restartbutton").click(function(event){
         $.ajax({ 
            type: "DELETE", 
            url: baseurl + '/' + project + "/output/" , 
            dataType: "text", 
            success: function(xml){ 
                window.location.href = ""; /* refresh */
            },
            error: function(response){
                if ((response.status < 200) || (response.status > 299)) { //patch
                    alert("Unable to delete output files (" + status + ")");   
                }
            }
         });         
       });
   }    

   //Return to index
   if ($("#indexbutton").length) {
       $("#indexbutton").click(function(event){
            window.location.href = baseurl + '/'; /* refresh */
       });
   }  
   
   
   //PATCH: Remove duplicates from inputsources list (not the most elegant, but works)
   if ($('#inputsourceupload')) {
    var found = [];
    $("#inputsourceupload option").each(function() {
        if($.inArray(this.value, found) != -1) $(this).remove();
        found.push(this.value);
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
   $("#openeditor").click(function(event){  $("#editormask").show(); window.scroll(0,0); $("#editor").slideDown(); })

   $('#toggleinputfiles').click(function(event) { 
       $('#inputfilesarea').show(); 
       $('#toggleinputfiles').hide();
    } );

   //Submit data through in-browser editor
   $("#editorsubmit").click(function(event){         
        var filename = validateuploadfilename($('#editorfilename').val(), $('#editorinputtemplate').val());
        if (!filename) {
             alert("Please specify a filename");
             return false;
        }
        

        var data = {'contents': $('#editorcontents').val(), 'inputtemplate': $('#editorinputtemplate').val() };
        addformdata('#editorparameters', data );
        $.ajax({ 
            type: "POST", 
            url: baseurl + '/' + project + "/input/" + filename, 
            dataType: "xml", 
            data: data, 
            success: function(response){            
                processuploadresponse(response, '#editorparameters');
                $('#editorcontents').val('');
                $('#editorfilename').val('');
                $(document).scrollTop( $("#header").offset().top ); 
                //$("#editor").slideUp(400, function(){ $("#editormask").hide(); } ); 
            },            
            error: function(response, errortype){
                processuploadresponse(response.responseXML, '#editorparameters');
            }            
        });            
        return true;
   });
   //$("#canceleditor").click(function(event){  $("#editor").slideUp(400, function(){ $("#editormask").hide(); } ); return false; });

   //Download and add from URL
   $('#urluploadsubmit').click(function(event){
            var filename = validateuploadfilename($('#urluploadfile').val(),$('#urluploadinputtemplate').val());
            if (!filename) {
               alert("Please specify a filename");
               return false;
            }

            $('#urlupload').hide();
            $('#urluploadprogress').show();
            
            $.ajax({ 
                type: "POST", 
                url: baseurl + '/' + project + "/input/" + filename, 
                dataType: "xml", 
                data: {'url': $('#urluploadfile').val(), 'inputtemplate': $('#urluploadinputtemplate').val() }, 
                success: function(response){
                    processuploadresponse(response, '#urluploadparameters');
                    $('#urluploadprogress').hide();                     
                    $('#urlupload').show();
                },
                error: function(response, errortype){
                    processuploadresponse(response.responseXML, '#urluploadparameters');
                    $('#urluploadprogress').hide();                     
                    $('#urlupload').show();
                }                
            });              
    });

   //Upload through browser
   if ($('#fineuploadarea') && (typeof(project) != 'undefined') ) {		
        $('#fineuploadarea').fineUploader({        
        	//element: $('#fineuploadarea')[0],     
            request: {
            	endpoint:  baseurl + '/' + project + '/upload/',
            	inputName: 'filename',
            },  
            text: { uploadButton: "Upload a file" } ,            
            multiple: true,
            //forceMultipart: true,
            autoUpload: true, 
            debug: true
        }).on('submit', function(event, id, fileName) {
		    	var inputtemplate_id = $('#uploadinputtemplate').val();
		    	if (inputtemplate_id == "") {
		    		alert("Please select a desired input type first");
		    		return false;
		    	}		    		
		    	var params = {inputtemplate: inputtemplate_id, user:user, accesstoken:accesstoken  }		    		
		    	addformdata( '#uploadparameters', params );		 
		    	$(this).fineUploader('setParams',params); 		    			    	
		         
		        return true;
		}).on('complete', function(event, id, fileName, responseJSON) {
				if (responseJSON.isarchive) {
					window.location.href = baseurl + '/' + project + '/'; /* just refresh page */
					return true;
				} 
		        processuploadresponse(responseJSON.xml, '#uploadparameters');
			
		}).on('click',function(){
		    	var inputtemplate_id = $('#uploadinputtemplate').val();
		    	if (inputtemplate_id == "") {
		    		alert("Please select a desired input type first");
		    		return false;
		    	}		
		});       
   }


   $('#inputsourceselect').click(function(event){ /* Doesn't exist???? */
        $.ajax({ 
                type: "POST", 
                url: baseurl + '/' + project + "/input/", 
                //dataType: "xml", 
                data: {'inputsource': $('#inputsource').val() }, 
                success: function(response){
                    window.location.href = baseurl + '/' + project + '/'; /* refresh */   
                },
                error: function(response, errortype){
                    alert(response);
                }          
        });     
   });
   
   $('#uploadinputsourcebutton').click(function(event){
       $('#inputsourceupload').hide();
       $('#inputsourceprogress').show();
       $.ajax({
            type: "POST",
            url: baseurl + '/' + project + "/input/",
            data: {'inputsource': $('#uploadinputsource').val() }, 
            success: function(response){
                //processuploadresponse(response, '#nonexistant');
                window.location.href = baseurl + '/' + project + '/'; /* refresh */   
            },
            error: function(response,errortype){
                $('#inputsourceprogress').hide();
                $('#inputsourceupload').show();
                if ((response.status >= 200) && (response.status <= 299)) { //patch
                    window.location.href = baseurl + '/' + project + '/'; /* refresh */   
                } else {
                    alert("Error, unable to add file ("+response.status+")");
                }
                //processuploadresponse(response.responseXML, '#nonexistant');                
            }
       });
   });

});  //ready


function addformdata(parent, data) {
    var fields = $(parent).find(':input');    
    $(fields).each(function(){ //also works on textarea, select, button!
        if (this.name != undefined) {
            data[this.name] = $(this).val();
        }
    });
}

function processuploadresponse(response, paramdiv) {
      //Processes CLAM Upload XML
      
      //Clear all previous errors
      $(paramdiv).find('.error').each(function(){ $(this).html('') }); 
      
      $(response).find('upload').each(function(){       //for each uploaded file
        //var children = $(this).children();
        var inputtemplate = $(this).attr('inputtemplate');
        
        var errors = false;
        $(this).find('error').each(function() {
                errors = true;
                alert($(this).text());
        });
        $(this).find('parameters').each(function(){ 
             if ($(this).attr('errors') == 'no') {
                    errors = false;
             } else {
                    errors = true;
                    //propagate the parameter errors to the interface
                    renderfileparameters(inputtemplate, paramdiv, true, this );
             }
        });        
        
        /*var metadataerror = false;
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
          
        if ((valid) && (!parametererrors) && (!metadataerror)) {*/
            //good! 
        
        if (!errors) {
        
            
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
                tableinputfiles.fnAddData( [  '<a href="' + baseurl + '/' + project + '/input/' + $(this).attr('filename') + '">' + $(this).attr('filename') + '</a>', $(this).attr('templatelabel'), '' ,'<img src="' + baseurl + '/static/delete.png" title="Delete this file" onclick="deleteinputfile(\'' + $(this).attr('filename') + '\');" />' ] )
            }
            
        }
        
        /* //TODO: Make errors nicer, instead of alerts, propagate to interface
        } else if (metadataerror) {
            alert("A metadata error occured, contact the service provider");
        } else if (conversionerror) {
            alert("The file you uploaded could not be converted with the specified converter");
        } else if (parametererrors) {
            alert("There were parameter errors");
            //TODO: Specify what parameter errors occured
        } else if (!valid) {
            alert("The file you uploaded did not validate, it's probably not of the type you specified");
        }*/
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




function renderfileparameters(id, target, enableconverters, parametersxmloverride) {
    if (id == "") {
        $(target).html("");
    } else {
        $(target).find('.error').each(function(){ $(this).html(''); }); 
        var inputtemplate = getinputtemplate(id);
        if (inputtemplate) {
            var xmldoc;
            var result;
            if (document.implementation && document.implementation.createDocument) {
                //For decent browsers (Firefox, Opera, Chromium, etc...)                
                if (parametersxmloverride == undefined) {
                    xmldoc = $(inputtemplate.parametersxml);                    
                } else {
                    xmldoc = $(parametersxmloverride);
                }
                var found = false;
                for (var i = 0; i < xmldoc.length; i++) {
                    if (xmldoc[i].nodeName.toLowerCase() == "parameters") {
                        xmldoc = xmldoc[i];
                        found = true;
                    }                    
                }
                if (!found) {
                    alert("You browser was unable render the metadata parameters...");
                    return false;
                }     

                
                xsltProcessor=new XSLTProcessor();
                xsltProcessor.importStylesheet(parametersxsl); //parametersxsl global, automatically loaded at start            
                            
                result = xsltProcessor.transformToFragment(xmldoc, document);
            } else if (window.ActiveXObject) { //For evil sucky non-standard compliant browsers ( == Internet Explorer)            
                xmldoc=new ActiveXObject("Microsoft.XMLDOM");
                xmldoc.async="false";
                xmldoc.loadXML(inputtemplate.parametersxml);
                result = xmldoc.transformNode(parametersxsl);
            } else {
                result = "<strong>Error: Unable to render parameter form!</strong>";
            }
            $(target).html(result);

            if ((enableconverters) && ($(inputtemplate.converters)) && (inputtemplate.converters.length > 0) ) {                
                var s = "Automatic conversion from other format? <select name=\"converter\">";
                s += "<option value=\"\">No</option>";
                for (var i = 0; i < inputtemplate.converters.length; i++) {
                    s += "<option value=\"" + inputtemplate.converters[i].id + "\">" + inputtemplate.converters[i].label + "</option>";
                }
                s += "</select><br />";
                $(target).prepend(s);
            }
            if (inputtemplate.acceptarchive) {
            	$(target).prepend("For easy mass upload, this input template also accepts <strong>archives</strong> (<tt>zip, tar.gz, tar.bz2</tt>) containing multiple files of exactly this specific type.<br />");
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
        url: baseurl + '/' + project + "/input/" + filename, 
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

function setlocalinputsource(selector, target) {
    var value = selector.val()
    if (value != "") { 
        $(target+'_form').show();
    } else {
        $(target+'_form').hide();
    }
}

function pollstatus() {
	$.ajax({
		type: 'GET',
		url: baseurl + '/' + project + "/status/",
		dataType: 'json', 
		data: {accesstoken: accesstoken, user: user},
		success: function(response){
                if (response.statuscode != 1) {
                	window.location.href = baseurl + '/' + project + '/'; /* refresh */
                } else {
                	if (response.completion > 0) {
                		progress = response.completion;
                		$('#progressbar').progressbar( "option", "value", progress );        
                	}        		
            		var statuslogcontent = "";
            		for (var i = 0; i < response.statuslog.length - 1; i++) {
            			var msg = response.statuslog[i][0];
            			var t = response.statuslog[i][1];
            			statuslogcontent += '<tr><td class="time">' + t + '</td><td class="message">' + msg + '</td></tr>';
            		}                 		                		
            		$('#statuslogtable').html(statuslogcontent);
                }
                setTimeout(pollstatus,2000);                   
        },
        error: function(response,errortype){
        	alert("Error obtaining status");
        },        
	});	
}

