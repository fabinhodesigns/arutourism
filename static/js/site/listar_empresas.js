
document.addEventListener('DOMContentLoaded', function() {

    document.addEventListener('keydown', function(e) {
        const card = e.target.closest('.empresa-card');
        if (card && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            const href = card.dataset.href;
            if (href) {
                window.location.href = href;
            }
        }
    });

    document.addEventListener('click', function(e) {
        const card = e.target.closest('.empresa-card');
        if (card) {
            const link = card.querySelector('.card-link-overlay');
            if (link && link.href) {
                window.location.href = link.href;
            }
        }
    });

    document.addEventListener('keydown', function(e) {
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
    }

    loadMoreBtn.addEventListener('click', async function() {
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
            if (!response.ok) throw new Error('Network response was not ok.');
            
            const data = await response.json();
            
            if (container) {
                container.insertAdjacentHTML('beforeend', data.html);
            }

            if (data.has_next) {
                nextPage = data.next_page_number;
            } else {
                nextPage = null;
                loadMoreBtn.classList.add('disabled');
                loadMoreBtn.setAttribute('aria-disabled', 'true');
                loadMoreBtn.querySelector('span:last-child').textContent = 'Não há mais resultados';
            }
        } catch (error) {
            console.error('Erro ao carregar mais empresas:', error);
            alert('Erro ao carregar mais empresas. Tente novamente.');
        } finally {
            setLoading(false);
        }
    });
});