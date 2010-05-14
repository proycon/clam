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
   $("#openeditor").click(function(event){ $("#mask").show(); $("#editor").slideDown(); })
   $("#uploadform").attr("target","_blank"); //would not be valid xhtml strict
   $("#editorform").attr("target","_blank");
   $("#submiteditor").click(function(event){ 
        $("#editor").slideUp(400, function(){ $("#mask").hide(); } ); 
        return true;
   });
   $("#canceleditor").click(function(event){  $("#editor").slideUp(400, function(){ $("#mask").hide(); } ); return false; });
   $('#inputfiles').dataTable( {
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
});    

