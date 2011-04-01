$(function(){
  var isValid = false;

  // validate and submit form
  $('#frmLinkAdd').submit(function() {
    $("#message").removeClass("validation-error").text("").hide();

    if (isValid == false) {
      var data = $("#frmLinkAdd").serialize();
      data += "&validate=validate";
   
      event.preventDefault();
      $.post("create", data,
      function(data){
        if (data!="valid") {
          isValid = false;
          $("#message").addClass("validation-error").text(data).show();
        } else {
          isValid = true;
          $("#frmLinkAdd").submit();
        }
      });
    
      return false;
    }
  });

});
