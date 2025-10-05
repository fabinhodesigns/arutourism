document.addEventListener('DOMContentLoaded', function () {

    document.body.addEventListener('click', function (e) {
        const card = e.target.closest('.empresa-card');
        if (card) {
            const link = card.querySelector('.card-link-overlay');
            if (link && link.href) {
                if (!e.target.closest('button, .btn')) {
                    e.preventDefault();
                    window.location.href = link.href;
                }
            }
        }
    });

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

    const loadMoreBtn = document.getElementById('load-more-btn');
    if (!loadMoreBtn) return;

    const url = loadMoreBtn.dataset.url;
    let nextPage = loadMoreBtn.dataset.nextPage;

    const spinner = loadMoreBtn.querySelector('.spinner-border');
    const statusEl = document.getElementById('load-status');
    const container = document.getElementById('empresas-container');

    function setLoading(isLoading) {
        loadMoreBtn.disabled = isLoading;
        if (spinner) {
            spinner.classList.toggle('d-none', !isLoading);
        }
        if (statusEl) {
            statusEl.textContent = isLoading ? 'Carregando mais resultados…' : '';
        }
        if (isLoading) {
            loadMoreBtn.querySelector('span:last-child').textContent = 'Carregando...';
        }
    }

    loadMoreBtn.addEventListener('click', async function () {
        if (!nextPage || !url) return;
        setLoading(true);

        try {
            const fetchUrl = new URL(url, window.location.origin);
            fetchUrl.searchParams.set('page', nextPage);
            fetchUrl.searchParams.set('ajax', '1');

            const currentParams = new URLSearchParams(window.location.search);
            currentParams.forEach((value, key) => {
                if (key !== 'page' && key !== 'ajax') {
                    fetchUrl.searchParams.set(key, value);
                }
            });

            const response = await fetch(fetchUrl);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`O servidor respondeu com um erro: ${errorText.substring(0, 200)}...`);
            }

            const data = await response.json();

            if (container) {
                container.insertAdjacentHTML('beforeend', data.html);
            }

            if (data.has_next) {
                nextPage = data.next_page_number;
                loadMoreBtn.querySelector('span:last-child').textContent = 'Carregar mais';
            } else {
                nextPage = null;
                loadMoreBtn.classList.add('disabled');
                loadMoreBtn.setAttribute('aria-disabled', 'true');
                loadMoreBtn.querySelector('span:last-child').textContent = 'Não há mais resultados';
            }
        } catch (error) {
            console.error('Erro ao carregar mais empresas:', error);
            alert('Ocorreu um erro ao carregar mais empresas. Verifique o console para mais detalhes.');
            loadMoreBtn.querySelector('span:last-child').textContent = 'Tentar Novamente';
        } finally {
            setLoading(false);
        }
    });

    const form = document.getElementById('delete-form');
    const checkboxes = form.querySelectorAll('input[type="checkbox"]');
    const toolbar = document.getElementById('actions-toolbar');
    const countSpan = document.getElementById('selection-count');

    function updateToolbar() {
        const selectedCount = form.querySelectorAll('input[type="checkbox"]:checked').length;
        if (selectedCount > 0) {
            toolbar.classList.remove('d-none');
            countSpan.textContent = selectedCount;
        } else {
            toolbar.classList.add('d-none');
        }
    }

    checkboxes.forEach(cb => cb.addEventListener('change', updateToolbar));

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (confirm('Tem certeza que deseja deletar as empresas selecionadas? Esta ação não pode ser desfeita.')) {
            // Lógica AJAX para enviar o formulário sem recarregar a página
            // (Pode ser implementada com fetch, similar aos outros formulários)
            this.submit(); // Versão simples: recarrega a página
        }
    });
});