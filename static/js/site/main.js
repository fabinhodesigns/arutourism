document.addEventListener('DOMContentLoaded', function () {
    const csrfTokenInput = document.getElementById('csrf-token-for-js');
    const csrfToken = csrfTokenInput ? csrfTokenInput.value : null;

    function updateFavoriteButton(button, isFavorito) {
        button.setAttribute('aria-pressed', isFavorito);
        button.setAttribute('aria-label', isFavorito ? 'Remover dos favoritos' : 'Adicionar aos favoritos');
        
        button.classList.toggle('btn-danger', isFavorito);
        button.classList.toggle('btn-outline-light', !isFavorito && button.classList.contains('btn-lg'));
        button.classList.toggle('btn-light', !isFavorito && button.classList.contains('btn-sm'));
        
        const icon = button.querySelector('i');
        if (icon) {
            icon.classList.toggle('bi-heart-fill', isFavorito);
            icon.classList.toggle('bi-heart', !isFavorito);
        }
    }

    document.body.addEventListener('click', async function (event) {
        const favButton = event.target.closest('#btn-favorito, [data-action="toggle-favorito"]');

        if (!favButton || !csrfToken) {
            return; 
        }

        const url = favButton.dataset.url;
        if (!url) return;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error('Falha na comunicação com o servidor.');
            }

            const data = await response.json();
            
            if (data.status === 'ok') {
                updateFavoriteButton(favButton, data.is_favorito);
            }

        } catch (error) {
            console.error("Erro ao favoritar:", error);
            alert("Ocorreu um erro. Tente novamente.");
        }
    });
});