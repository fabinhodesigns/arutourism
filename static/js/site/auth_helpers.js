
$(document).ready(function () {
    $(".message-box .btn-close").on("click", function () {
        $(this).closest("li").fadeOut(function () {
            $(this).remove();
            if ($(".message-box ul li").length === 0) {
                $("#message-overlay").fadeOut();
            }
        });
    });

    $("#id_username").on("input", function () {
        let value = $(this).val();
        if (/\s/.test(value)) {
            $(this).val(value.replace(/\s/g, '')); 
            $(this).attr("placeholder", "Usuário não pode conter espaços");
        } else {
            $(this).attr("placeholder", "Digite seu usuário");
        }
    });
});