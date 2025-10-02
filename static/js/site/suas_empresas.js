$(function() {
    const $btn = $('#load-more-btn');
    if (!$btn.length) return;

    const url = $btn.data('url');
    let nextPage = $btn.data('next-page');

    $btn.on('click', function() {
        if (!nextPage || !url) return;

        $btn.prop('disabled', true).text('Carregando...');

        $.ajax({
            url: url,
            data: { page: nextPage },
            dataType: 'json',
            success: function(data) {
                $('#empresas-container').append(data.html);

                if (data.has_next) {
                    nextPage = data.next_page_number;
                    $btn.prop('disabled', false).text('Carregar mais');
                } else {
                    nextPage = null;
                    $btn.hide();
                }
            },
            error: function() {
                alert('Erro ao carregar mais empresas.');
                $btn.prop('disabled', false).text('Tentar novamente');
            }
        });
    });
});