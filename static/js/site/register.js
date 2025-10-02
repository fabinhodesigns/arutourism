$(document).ready(function () {
    function formatCpfCnpj(value) {
        if ($("#cpf").prop('checked')) {
            return value.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
        }
        if ($("#cnpj").prop('checked')) {
            return value.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
        }
        return value;
    }

    $("#cpf_cnpj").on('input', function () {
        var value = $(this).val().replace(/\D/g, '');
        $(this).val(formatCpfCnpj(value));
    });

    $("form").submit(function (event) {
        var cpfCnpjValue = $("#cpf_cnpj").val();
        if (cpfCnpjValue === "") {
            event.preventDefault();
            alert("O campo CPF ou CNPJ é obrigatório!");
        }
    });

    $(function () {
        $("#close-message").on("click", function () {
            $("#message-overlay").fadeOut();
        });

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
});