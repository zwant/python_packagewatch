$(document).ready(function(){
    $(".remove-button").click(function(){
        $.ajax({
            type: "DELETE",
            url: $(this).parent("td").parent("tr").data("url")
        }).done(function( msg ) {
            location.reload();
        });
    });
});

$(document).on("click", ".open-edit-modal", function () {
    $("#openEditModal .modal-header #package_name").text( $(this).parent("td").parent("tr").data('package-name') );
    $("#openEditModal .modal-body form").attr("action", $(this).parent("td").parent("tr").data('url') );
});

$(document).on("click", "#openEditModal .modal-footer button[type='submit']", function () {
    $("#openEditModal .modal-body form").submit();
});


$("#openRegisterModal .modal-footer button[type='submit']").on("click", function () {
    $.ajax({
      url: $('#registration_form').attr('action'),
      type: 'POST',
      dataType: 'json',
      data : $('#registration_form').serialize(),
      success: function(data, status){
        if (data.result === 'SUCCESS') {
            document.location.href = '/';
        }

      }
    });
});

$("#openLoginModal .modal-footer button[type='submit']").on("click", function () {
    $.ajax({
      url: $('#login_form').attr('action'),
      type: 'POST',
      dataType: 'json',
      data : $('#login_form').serialize(),
      success: function(data, status){
        if (data.result === 'SUCCESS') {
            document.location.href = '/';
        }
      }
    });
});

$("#uploadFileModal .modal-footer button[type='submit']").on("click", function () {
    $('#upload_file_form').submit();
});