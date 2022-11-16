/***********************************************************
 * CLAM: Computational Linguistics Application Mediator
 *
 *       by Maarten van Gompel (proycon)
 *       https://proycon.github.io/clam
 *
 *       Centre for Language and Speech Technology / Language Machines
 *       Radboud University Nijmegen
 *
 *       Licensed under GPLv3
 ***********************************************************/

/*eslint-env browser,jquery */
/*global stage,progress:true,user,accesstoken,oauth_access_token, preselectinputtemplate,baseurl,project, inputtemplates,parametersxsl:true, tableinputfiles:true */
//global but not used: systemid
/*eslint-disable quotes, no-alert,complexity,curly,eqeqeq */

var uploader;

/*
function oauthheader(req) {
  if (oauth_access_token !== "") {
    req.setRequestHeader("Authorization", "Bearer " + oauth_access_token);
 }
}
*/

function getinputtemplate(id) {
    for (var i = 0; i < inputtemplates.length; i++) {
        if (inputtemplates[i].id === id) {
           return inputtemplates[i];
        }
    }
    return null;
}

function validateuploadfilename(filename, inputtemplate_id) {
    var inputtemplate = getinputtemplate(inputtemplate_id);
    if (inputtemplate === null) {
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
        //if the desired extension is not provided yet (server will take care of case mismatch), add it:
        if (filename.substr(filename.length - l - 1, l+1).toLowerCase() !== '.' + inputtemplate.extension.toLowerCase()) {
            filename = filename + '.' + inputtemplate.extension;
        }
    }
    return filename;
}

function sort_options(selector) {
    //adapted from https://stackoverflow.com/questions/12073270/sorting-options-elements-alphabetically-using-jquery
    var options = $(selector + ' option');
    if (options) {
        var arr = options.map(function(_, o) { return { t: $(o).text(), v: o.value, s: $(o).prop('selected') }; }).get();
        arr.sort(function(o1, o2) {
          var t1 = o1.t.toLowerCase(), t2 = o2.t.toLowerCase();
          return t1 > t2 ? 1 : t1 < t2 ? -1 : 0;
        });
        options.each(function(i, o) {
          o.value = arr[i].v;
          $(o).text(arr[i].t);
          $(o).prop('selected', arr[i].s);
        });
    }
}




function renderfileparameters(id, target, enableconverters, parametersxmloverride) {
    if (id === "") {
        $(target).html("");
    } else {
        $(target).find('.error').each(function(){ $(this).html(''); });
        var inputtemplate = getinputtemplate(id);
        if (inputtemplate) {
            var xmldoc;
            var result;
            var parametercount = 0;
            if (document.implementation && document.implementation.createDocument) {
                //For decent browsers (Firefox, Opera, Chromium, etc...)
                if (parametersxmloverride === undefined) { //eslint-disable-line no-undefined
                    xmldoc = $(inputtemplate.parametersxml);
                } else {
                    xmldoc = $(parametersxmloverride);
                }
                var found = false;
                for (var i = 0; i < xmldoc.length; i++) {
                    if (xmldoc[i].nodeName.toLowerCase() === "parameters") {
                        xmldoc = xmldoc[i];
                        found = true;
                        parametercount = xmldoc.children.length;
                    }
                }
                if (!found) {
                    alert("You browser was unable render the metadata parameters...");
                    return false;
                }


                var xsltProcessor=new XSLTProcessor();
                xsltProcessor.importStylesheet(parametersxsl); //parametersxsl global, automatically loaded at start

                result = xsltProcessor.transformToFragment(xmldoc, document);
            } else if (window.ActiveXObject) { //For evil sucky non-standard compliant browsers ( == Internet Explorer)
                xmldoc=new ActiveXObject("Microsoft.XMLDOM"); //eslint-disable-line no-undef
                xmldoc.async="false";
                xmldoc.loadXML(inputtemplate.parametersxml);
                parametercount = 1; //TODO: determine real count
                result = xmldoc.transformNode(parametersxsl);
            } else {
                result = "<div class=\"alert alert-danger\">Error: Unable to render parameter form!</div>";
            }
            $(target).html(result);

            if (parametercount === 0) {
                $(target + "wrapper").hide();
                $(target + "step").html("2");
                $(target + "step2").html("3");
            } else {
                $(target + "wrapper").show();
                $(target + "step").html("3");
                $(target + "step2").html("4");
            }

            if ((enableconverters) && ($(inputtemplate.converters)) && (inputtemplate.converters.length > 0) ) {
                var s = "Automatic conversion from other format? <select name=\"converter\" class=\"form-control\">";
                s += "<option value=\"\" selected=\"selected\">No</option>";
                for (var j = 0; j < inputtemplate.converters.length; j++) {
                    s += "<option value=\"" + inputtemplate.converters[j].id + "\">" + inputtemplate.converters[j].label + "</option>";
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


function deleteinputfile(filename) {   //eslint-disable-line no-unused-vars
    var found = -1;
    var data = tableinputfiles.fnGetData();
    for (var i = 0; i < data.length; i++) {
        if (data[i][0].match('>' + filename + '<') !== null) {
            found = i;
            break;
        }
    }
    if (found >= 0) tableinputfiles.fnDeleteRow(found);
    $.ajax({
        type: "DELETE",
        //beforeSend: oauthheader,
        crossDomain: true,
        xhrFields: {
          withCredentials: true
        },
        url: baseurl + '/' + project + "/input/" + filename,
        dataType: "xml"
    });
}

function setinputsource(tempelement) { //eslint-disable-line no-unused-vars
    var src = tempelement.value;
    $('#usecorpus').val(src);
    if (src === '') {
        $('#inputfilesarea').show();
        $('#uploadarea').show();
    } else {
        $('#inputfilesarea').hide();
        $('#uploadarea').hide();
    }
}

function setlocalinputsource(selector, target) {//eslint-disable-line no-unused-vars
    var value = selector.val();
    if (value !== "") {
        $(target+'_form').show();
    } else {
        $(target+'_form').hide();
    }
}

function pollstatus() {
    $.ajax({
        type: 'GET',
        url: baseurl + '/' + project + "/status/",
        //beforeSend: oauthheader,
        crossDomain: true,
        xhrFields: {
          withCredentials: true
        },
        dataType: 'json',
        data: {accesstoken: accesstoken, user: user},
        success: function(response){
                if (response.statuscode !== 1) {
                    window.location.href = baseurl + '/' + project + '/'; /* refresh */
                } else {
                    if (response.completion > 0) {
                        progress = response.completion;
                        $('#progress .progress-bar').css("style", "width: " + progress + "%" );
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
        error: function(response,errortype){ //eslint-disable-line no-unused-vars
            alert("Error obtaining status");
        },
    });
}


function processuploadresponse(response, paramdiv) {
      //Processes CLAM Upload XML

      //Clear all previous errors
      $(paramdiv).find('div.error').each(function(){ $(this).html(''); });

      $(response).find('upload').each(function(){       //for each uploaded file
        //var children = $(this).children();
        var inputtemplate = $(this).attr('inputtemplate');

        var errors = false;
        $(this).find('error').each(function() {
                errors = true;
                alert($(this).text());
        });
        $(this).find('parameters').each(function(){
             if ($(this).attr('errors') === 'no') {
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
                if (data[i][0].match('>' + $(this).attr('name') + '<') !== null) {
                    found = true;
                    break;
                }
            }

            //Add this file to the input table if it doesn't exist yet
            if (!found) {
                tableinputfiles.fnAddData( [  '<a class="text-primary" href="' + baseurl + '/' + project + '/input/' + $(this).attr('filename') + '">' + $(this).attr('filename') + '</a>', $(this).attr('templatelabel'), $(this).attr('format') ,'<span class="oi oi-circle-x deletefile" title="Delete this file" onclick="deleteinputfile(\'' + $(this).attr('filename') + '\');"></span>' ] );
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


function showquickdelete() {//eslint-disable-line no-unused-vars
    $('.quickdelete').show();
}

function quickdelete(projectname) {//eslint-disable-line no-unused-vars
        $.ajax({
        type: "DELETE",
        url: baseurl + '/' + projectname + '/',
        dataType: "text",
        //beforeSend: oauthheader,
        crossDomain: true,
        xhrFields: {
            withCredentials: true
        },
        success: function(){
            $('#projectrow_' + projectname).hide();
            $('#projects_info').html("Deleted project " + projectname);
            $('.diskusage span').html("(Reload page to see total disk use)");
        }});
}

function addformdata(parent, data) {
    var fields = $(parent).find(':input');
    $(fields).each(function(){ //also works on textarea, select, button!
        if (this.name !== undefined) { //eslint-disable-line no-undefined
            data[this.name] = $(this).val();
        }
    });
}

function initclam() { //eslint-disable-line no-unused-vars, complexity
   if (typeof(inputtemplates) === "undefined") {
        //something went wrong during loading, probably authentication issues, reload page
        window.location.reload(); //alert("System error: data.js not properly loaded?");
   }

   $('[data-toggle="popover"]').popover();

   //set custom text, this hack is needed because XSLT 1.0 can't get the job
   //done alone in all browsers
   if (($("#customhtml").length > 0) && $("#customhtml").html().search("&lt;") != 1) {
       var lt = new RegExp("&lt;", 'g');
       var gt = new RegExp("&gt;", 'g');
       var s = $("#customhtml").html();
       s = s.replace(lt,'<');
       s = s.replace(gt,'>');
       $("#customhtml").html(s);
   }

   if ($("#projectname").length) {
    $( "#projectname" ).keydown(function( event ) {
         if ( event.which === 32 ) {
            $("#projectname").val($("#projectname").val() + '_');
            event.preventDefault();
         }
    });
   }

   /*
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
    */

   //Create lists of all possible inputtemplates (aggregated over all profiles)
   var inputtemplate_options = [];
   var processed = [];
   if (inputtemplates.length === 1) {
       preselectinputtemplate = true; //there is only one so we select it
   } else {
       inputtemplate_options.push( ['',"<option value=\"\">---&gt; Select a filetype...</option>"]);
   }
   for (var i = 0; i < inputtemplates.length; i++) {
        var duplicate = false;
        for (var j = 0; j < processed.length; j++) {
            if (inputtemplates[i].id  ===  inputtemplates[j].id) {
                duplicate = true;
                break;
            }
        }
        if (duplicate) continue;
        processed.push(inputtemplates[i].id);
        var selected;
        if ((i === 0) && (preselectinputtemplate) ) {
            selected='selected="selected"';
        } else {
            selected="";
        }
        inputtemplate_options.push([inputtemplates[i].label.toLowerCase(),  '<option value="' + inputtemplates[i].id + '" ' + selected + '>' + inputtemplates[i].label + '</option>']);
   }
   inputtemplate_options.sort(function(a,b){ return (a[0]<b[0]?-1:(a[0]>b[0]?1:0)); } );
   var inputtemplate_options_string = "";
   for (var i = 0; i < inputtemplate_options.length; i++) {
       inputtemplate_options_string += inputtemplate_options[i][1];
   }
   $(".inputtemplates").html(inputtemplate_options_string);

   //Tying events to trigger rendering of file-parameters when an inputtemplate is selected:
   $("#uploadinputtemplate").change(function(){renderfileparameters($('#uploadinputtemplate').val(),'#uploadparameters',true); });
   $("#urluploadinputtemplate").change(function(){renderfileparameters($('#urluploadinputtemplate').val(),'#urluploadparameters',true);});
   $("#editorinputtemplate").change(function(){
        renderfileparameters($('#editorinputtemplate').val(),'#editorparameters',false);
        var inputtemplate = getinputtemplate($('#editorinputtemplate').val());
        if (inputtemplate !== null) {
            if (inputtemplate.filename) {
                $('#editorfilename').val(inputtemplate.filename);
                $('.editorfilenamerow').hide();
            } else {
                $('.editorfilenamerow').show();
            }
        } else {
            $('.editorfilenamerow').show();
        }
    });

   if (typeof(stage) != 'undefined') {
       //Download parameters.xsl so it's available to javascript for file-parameters
       $.ajax({
            type: "GET",
            url: baseurl + "/static/parameters.xsl",
            dataType: "xml",
            //beforeSend: oauthheader,
            crossDomain: true,
            xhrFields: {
              withCredentials: true
            },
            success: function(xml){
                parametersxsl = xml;
                if (preselectinputtemplate) {
                  //we have a preselection, trigger
                  $("#uploadinputtemplate").trigger('change');
                  $("#urluploadinputtemplate").trigger('change');
                  $("#editorinputtemplate").trigger('change');
                }
            }
       });
      if (stage === 1) {
            $('#progress .progress-bar').css( "style", "width: " + progress + "%" );
            setTimeout(pollstatus,2000);
       }
    }


   //Create a new project'
    if ($("#startprojectbutton").length) {
       $("#projectname").keypress(function(e){ if (e.which === 13) $('#startprojectbutton').focus().click(); });

       $("#startprojectbutton").click(function(){
         if ($("#projectname").val() === "") {
             alert("No project ID specified");
             return;
         }
         $.ajax({
            type: "PUT",
            url: baseurl + "/" + $("#projectname").val() + "/",
            dataType: "text",
            //beforeSend: oauthheader,
            crossDomain: true,
            xhrFields: {
              withCredentials: true
            },
            success: function(){
                window.location.href = baseurl + "/" + $("#projectname").val() + "/";
            },
            error: function(response){
                if ((response.status < 200) || (response.status > 299)) { //patch
                    if (response.responseText) {
                        alert(response.responseText);
                    } else {
                        alert("Unable to create project, the server returned an error (HTTP " + response.status + "):  Did you perhaps use spaces or special characters in the ID? Only underscores and alphanumeric characters are allowed.");
                    }
                }
            }
         });
         //$("#startprojectform").attr("action",$("#projectname").val());
       });
   }

   //Abort execution without deleting project
   if ($("#abortbutton").length) {
       $("#abortbutton").click(function(){
         $.ajax({
            type: "DELETE",
            url: baseurl + '/' + project + '/?abortonly=true',
            dataType: "text",
            //beforeSend: oauthheader,
            crossDomain: true,
            xhrFields: {
              withCredentials: true
            },
            success: function(){
                window.location.href = baseurl + '/'; /* back to index */
            },
            error: function(response){
                if ((response.status < 200) || (response.status > 299)) { //patch
                    if (response.responseText) {
                        alert(response.responseText);
                    } else {
                        alert("Unable to delete project (" + response.status + ")");
                    }
                }
            }
         });
       });
   }


   //Abort and delete a project
   if ($("#deletebutton").length) {
       $("#deletebutton").click(function(){
         $.ajax({
            type: "DELETE",
            url: baseurl + '/' + project + '/',
            dataType: "text",
            //beforeSend: oauthheader,
            crossDomain: true,
            xhrFields: {
              withCredentials: true
            },
            success: function(response){
                window.location.href = baseurl + '/'; /* back to index */
            },
            error: function(response){
                if ((response.status < 200) || (response.status > 299)) { //patch
                    if (response.responseText) {
                        alert(response.responseText);
                    } else {
                        alert("Unable to delete project (" + response.status + ")");
                    }
                }
            }
         });
       });
   }

   //Restart a project (deleting only its output)
   if ($("#restartbutton").length) {
       $("#restartbutton").click(function(){
         $.ajax({
            type: "DELETE",
            url: baseurl + '/' + project + "/output/" ,
            dataType: "text",
            //beforeSend: oauthheader,
            crossDomain: true,
            xhrFields: {
              withCredentials: true
            },
            success: function(){
                window.location.href = ""; /* refresh */
            },
            error: function(response){
                if ((response.status < 200) || (response.status > 299)) { //patch
                    if (response.responseText) {
                        alert(response.responseText);
                    } else {
                        alert("Unable to delete output files (" + status + ")");
                    }
                }
            }
         });
       });
   }

   //Return to index
   if ($("#indexbutton").length) {
       $("#indexbutton").click(function(){
            window.location.href = baseurl + '/'; /* back to index */
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
   $("#openeditor").click(function(){  $("#editormask").show(); window.scroll(0,0); $("#editor").slideDown(); });

   $('#toggleinputfiles').click(function() {
       $('#inputfilesarea').show();
       $('#toggleinputfiles').hide();
    } );

   //Submit data through in-browser editor
   $("#editorsubmit").click(function(){
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
            //beforeSend: oauthheader,
            crossDomain: true,
            xhrFields: {
              withCredentials: true
            },
            success: function(response){
                processuploadresponse(response, '#editorparameters');
                $('#editorcontents').val('');
                $('#editorfilename').val('');
                $(document).scrollTop( $("#input").offset().top );
                //$("#editor").slideUp(400, function(){ $("#editormask").hide(); } );
            },
            error: function(response, errortype){ //eslint-disable-line no-unused-vars
                processuploadresponse(response.responseXML, '#editorparameters');
            }
        });
        return true;
   });
   //$("#canceleditor").click(function(event){  $("#editor").slideUp(400, function(){ $("#editormask").hide(); } ); return false; });

   //Download and add from URL
   $('#urluploadsubmit').click(function(){
            var filename = validateuploadfilename($('#urluploadfile').val().split('/').reverse()[0] ,$('#urluploadinputtemplate').val());
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
                //beforeSend: oauthheader,
                crossDomain: true,
                xhrFields: {
                  withCredentials: true
                },
                success: function(response){
                    processuploadresponse(response, '#urluploadparameters');
                    $('#urluploadprogress').hide();
                    $('#urlupload').show();
                },
                error: function(response, errortype){ //eslint-disable-line no-unused-vars
                    processuploadresponse(response.responseXML, '#urluploadparameters');
                    $('#urluploadprogress').hide();
                    $('#urlupload').show();
                }
            });
    });

   //Upload through browser
   if ( (typeof($('#fineuploadarea')[0]) != 'undefined') && (typeof(project) != 'undefined') ) {
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
            failedUploadTextDisplay: {
                mode: 'custom',
                maxChars: 1024,
                responseProperty: 'error',
            },
            debug: true
        }).on('submit', function(e, id, fileName) { //eslint-disable-line no-unused-vars
                var inputtemplate_id = $('#uploadinputtemplate').val();
                if (inputtemplate_id === "") {
                    alert("Please select a desired input type first");
                    return false;
                }
                var params = {inputtemplate: inputtemplate_id, user:user, accesstoken:accesstoken };
                addformdata( '#uploadparameters', params );
                $(this).fineUploader('setParams',params);

                return true;
        }).on('complete', function(e, id, fileName, responseJSON) { //eslint-disable-line no-unused-vars
                if (responseJSON.isarchive) {
                    window.location.href = baseurl + '/' + project + "/";
                    return true;
                }
                var xml;
                try {
                    xml = window.atob(responseJSON.xml); //was base64 encoded
                } catch {
                    xml = responseJSON.xml;
                }
                processuploadresponse(xml, '#uploadparameters');

        }).on('click',function(){
                var inputtemplate_id = $('#uploadinputtemplate').val();
                if (inputtemplate_id === "") {
                    alert("Please select a desired input type first");
                    return false;
                }
        });
   }

   //simpleupload:
   if ( (typeof($('#uploadbutton')[0]) != 'undefined') && (typeof(project) != 'undefined') ) {
       uploader = new AjaxUpload('uploadbutton', {action: baseurl + "/" + project + "/input/", name: "file", data: {"inputtemplate": $("#uploadinputtemplate").val()} ,
            onChange: function(uploadfilename,extension){ //eslint-disable-line no-unused-vars
                 var inputtemplate_id = $('#uploadinputtemplate').val();
                 var filename = validateuploadfilename(uploadfilename,inputtemplate_id);
                 if (!filename) {
                    return false;
                 } else {
                     uploader._settings.action = baseurl + "/" + project + "/input/" + filename;
                     uploader._settings.data.inputtemplate = inputtemplate_id;
                     addformdata( '#uploadparameters', uploader._settings.data );
                 }
            },
            onSubmit: function(){
                $('#clientupload').hide();
                $('#uploadprogress').show();
            },
            onComplete: function(file, response){ //eslint-disable-line no-unused-vars
                processuploadresponse(response, "#uploadparameters");
                $('#uploadprogress').hide();
                $('#clientupload').show();
            }
        });
   }



   $('#inputsourceselect').click(function(){ /* Doesn't exist???? */
        $.ajax({
                type: "POST",
                url: baseurl + '/' + project + "/input/",
                //dataType: "xml",
                data: {'inputsource': $('#inputsource').val() },
                //beforeSend: oauthheader,
                crossDomain: true,
                xhrFields: {
                  withCredentials: true
                },
                success: function(response){
                    window.location.href = baseurl + '/' + project + "/";
                },
                error: function(response, errortype){
                    alert(response.responseText);
                }
        });
   });

   $('#uploadinputsourcebutton').click(function(){
       $('#inputsourceupload').hide();
       $('#inputsourceprogress').show();
       $.ajax({
            type: "POST",
            url: baseurl + '/' + project + "/input/",
            data: {'inputsource': $('#uploadinputsource').val() },
            //beforeSend: oauthheader,
            crossDomain: true,
            xhrFields: {
              withCredentials: true
            },
            success: function(response){//eslint-disable-line no-unused-vars
                //processuploadresponse(response, '#nonexistant');
               window.location.href = baseurl + '/' + project + "/";
          },
            error: function(response,errortype){//eslint-disable-line no-unused-vars
                $('#inputsourceprogress').hide();
                $('#inputsourceupload').show();
                if ((response.status >= 200) && (response.status <= 299)) { //patch
                   window.location.href = baseurl + '/' + project + "/";
                } else {
                    if (response.responseText) {
                        alert(response.responseText);
                    } else {
                        alert("Error, unable to add file ("+response.status+")");
                    }
                }
                //processuploadresponse(response.responseXML, '#nonexistant');
            }
       });
   });

}  //initclam


