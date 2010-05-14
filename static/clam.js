$(document).ready(function(){
   if ($("#startprojectbutton").length) {
       $("#startprojectbutton").click(function(event){
         $.ajax({ 
            type: "PUT", 
            url: "/" + $("#projectname").val() + "/", 
            dataType: "xml", 
            complete: function(xml){ 
                window.location.href = $("#projectname").val() + "/";
            },
         });
         //$("#startprojectform").attr("action",$("#projectname").val());
       });
   }
   if ($("#abortbutton").length) {
       $("#abortbutton").click(function(event){
         $.ajax({ 
            type: "DELETE", 
            url: window.location.href, 
            dataType: "xml", 
            complete: function(xml){ 
                window.location.href = "/"; /* back to index */
            },
         });         
       });
   }    
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



   inputfiles = $('#inputfiles').dataTable( {
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




   $("#openeditor").click(function(event){ $("#mask").show(); $("#editor").slideDown(); })
   $("#uploadform").attr("target","_blank"); //would not be valid xhtml strict
   $("#editorform").attr("target","_blank");

   $("#submiteditor").click(function(event){ 
        $("#editor").slideUp(400, function(){ $("#mask").hide(); } ); 
        var filename = $('#uploadfilename1').val();
        var d = new Date();    
        if (!filename) {
            filename = d.getTime();        
        }
        $.ajax({ 
            type: "POST", 
            url: "upload/", 
            dataType: "xml", 
            data: {'uploadcount':1, 'uploadtext1': $('#uploadtext1').val(), 'uploadformat1': $('#editoruploadformat').val(), 'uploadfilename1': filename }, 
            success: function(response){ 
                $(response).find('file').each(function(){
                    if (($(this).attr('archive') != 'yes') && ($(this).attr('validated') == 'yes')) {
                        inputfiles.fnAddData( [ $(this).attr('name'), $(this).attr('formatlabel'), $(this).attr('encoding') ] );
                    }
                });
            },
        });            
        return true;
   });
   $("#canceleditor").click(function(event){  $("#editor").slideUp(400, function(){ $("#mask").hide(); } ); return false; });



   uploader = new AjaxUpload('upload1', {action: 'upload/', name: 'upload1', data: {'uploadformat1': $('#uploadformat1').val() , 'uploadcount': 1 } , onSubmit: function(){
            $('#complexupload').hide();
            $('#uploadprogress').show();           
        },  onComplete: function(file, response){
            $(response).find('file').each(function(){
                if (($(this).attr('archive') != 'yes') && ($(this).attr('validated') == 'yes')) {
                    inputfiles.fnAddData( [ $(this).attr('name'), $(this).attr('formatlabel'), $(this).attr('encoding') ] );
                }
            });
            //window.alert($(response).text()); //DEBUG
            $('#uploadprogress').hide();
            $('#complexupload').show();
        }       
    }); 
   $('#uploadformat1').change(function(){
        uploader.setData({'uploadformat1': $('#uploadformat1').val() , 'uploadcount': 1} );
   });


});    

