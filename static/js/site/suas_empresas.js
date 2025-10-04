// Em static/js/site/suas_empresas.js

document.addEventListener('DOMContentLoaded', function () {

    // --- Lógica para tornar os cards clicáveis (clique do mouse) ---
    document.body.addEventListener('click', function (e) {
        const card = e.target.closest('.empresa-card');
        if (card) {
            const link = card.querySelector('.card-link-overlay');
            if (link && link.href) {
                // Previne que o clique em botões dentro do card (se houver) redirecione
                if (!e.target.closest('button, .btn')) {
                    e.preventDefault();
                    window.location.href = link.href;
                }
            }
        }
    });

    // --- Lógica para acessibilidade dos cards (teclas Enter/Espaço) ---
    document.body.addEventListener('keydown', function (e) {
        const card = e.target.closest('.empresa-card');
        if (card && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            const link = card.querySelector('.card-link-overlay');
            if (link && link.href) {
                window.location.href = link.href;
            }
        }
    });

    // --- Lógica do botão "Carregar mais" ---
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (!loadMoreBtn) return; // Se o botão não existir, para aqui

    const url = loadMoreBtn.dataset.url;
    let nextPage = loadMoreBtn.dataset.nextPage;
    const container = document.getElementById('empresas-container');

    loadMoreBtn.addEventListener('click', async function () {
        if (!nextPage || !url) return;

        loadMoreBtn.disabled = true;
        loadMoreBtn.textContent = 'Carregando...';

        try {
            const fetchUrl = new URL(url, window.location.origin);
            fetchUrl.searchParams.set('page', nextPage);

            const response = await fetch(fetchUrl);
            if (!response.ok) throw new Error('A resposta da rede não foi OK.');

            const data = await response.json();

            if (container) {
                // Adiciona o novo HTML ao final do container
                container.insertAdjacentHTML('beforeend', data.html);
            }

            if (data.has_next) {
                nextPage = data.next_page_number;
                loadMoreBtn.dataset.nextPage = nextPage;
                loadMoreBtn.disabled = false;
                loadMoreBtn.textContent = 'Carregar mais';
            } else {
                nextPage = null;
                loadMoreBtn.style.display = 'none'; // Esconde o botão se não houver mais páginas
            }
        } catch (error) {
            console.error('Erro ao carregar mais empresas:', error);
            alert('Erro ao carregar mais empresas. Tente novamente.');
            loadMoreBtn.disabled = false;
            loadMoreBtn.textContent = 'Tentar Novamente';
        }
    });
});