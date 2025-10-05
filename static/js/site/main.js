// ARQUIVO: static/js/site/main.js (VERSÃO FINAL COMPLETA)

document.addEventListener('DOMContentLoaded', () => {

    /**
     * Função auxiliar para pegar o CSRF token.
     * Tenta 3 métodos em ordem de prioridade para máxima compatibilidade.
     */
    function getCsrfToken() {
        // 1. Tenta pegar da meta tag (método preferido e mais confiável)
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');
        
        // 2. Fallback: Tenta pegar do cookie
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        if (cookie) return cookie.split('=')[1];

        console.warn('CSRF token não encontrado.');
        return null;
    }

    const body = document.body;

    // ========================================================================
    // LÓGICA DO PAINEL DE BUSCA
    // ========================================================================
    const searchOverlay = document.getElementById('searchOverlay');
    const openBtn = document.getElementById('open-search');
    const openBtnMobile = document.getElementById('open-search-mobile');
    const closeBtn = document.getElementById('close-search');
    const qInput = document.getElementById('f-q');
    
    if (searchOverlay) {
        function openSearch() {
            searchOverlay.classList.add('open');
            searchOverlay.setAttribute('aria-hidden', 'false');
            body.classList.add('no-scroll');
            setTimeout(() => qInput && qInput.focus(), 180);
        }

        function closeSearch() {
            searchOverlay.classList.remove('open');
            searchOverlay.setAttribute('aria-hidden', 'true');
            body.classList.remove('no-scroll');
            if (openBtn) openBtn.focus();
        }

        if (openBtn) openBtn.addEventListener('click', openSearch);
        if (openBtnMobile) openBtnMobile.addEventListener('click', openSearch);
        if (closeBtn) closeBtn.addEventListener('click', closeSearch);

        document.addEventListener('keydown', e => {
            if (e.key === 'Escape' && searchOverlay.classList.contains('open')) {
                closeSearch();
            }
        });

        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) {
                closeSearch();
            }
        });

        // Lógica de seleção de múltiplas tags
        const filterForm = document.getElementById('filter-form');
        const tagSelectionArea = document.getElementById('tag-selection-area');
        const categoriaList = document.getElementById('categoria-list');
        
        if (filterForm && tagSelectionArea && categoriaList) {
            const placeholderText = tagSelectionArea.querySelector('span');
            
            function loadInitialTags() {
                const params = new URLSearchParams(window.location.search);
                const tagIds = params.getAll('tag');
                if (tagIds.length > 0) {
                    tagIds.forEach(tagId => {
                        const item = categoriaList.querySelector(`.dropdown-item[data-value="${tagId}"]`);
                        if (item) addTag(item.dataset.value, item.textContent);
                    });
                }
            }
            
            function addTag(value, name) {
                if (filterForm.querySelector(`input[name="tag"][value="${value}"]`)) return;
                if (placeholderText) placeholderText.style.display = 'none';
                const tagPill = document.createElement('div');
                tagPill.className = 'selected-tag';
                tagPill.innerHTML = `<span>${name}</span><button type="button" class="remove-tag" data-value="${value}" aria-label="Remover ${name}">&times;</button>`;
                tagSelectionArea.appendChild(tagPill);
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'tag';
                hiddenInput.value = value;
                filterForm.appendChild(hiddenInput);
            }

            function removeTag(value) {
                const inputToRemove = filterForm.querySelector(`input[name="tag"][value="${value}"]`);
                if (inputToRemove) inputToRemove.remove();
                const pillToRemove = tagSelectionArea.querySelector(`.remove-tag[data-value="${value}"]`);
                if (pillToRemove) pillToRemove.parentElement.remove();
                if (tagSelectionArea.querySelectorAll('.selected-tag').length === 0) {
                    if (placeholderText) placeholderText.style.display = 'inline';
                }
            }

            tagSelectionArea.addEventListener('click', () => {
                categoriaList.classList.toggle('show');
                tagSelectionArea.setAttribute('aria-expanded', String(categoriaList.classList.contains('show')));
            });

            categoriaList.addEventListener('click', (e) => {
                const item = e.target.closest('.dropdown-item');
                if (item) addTag(item.dataset.value, item.textContent);
            });

            tagSelectionArea.addEventListener('click', (e) => {
                const removeBtn = e.target.closest('.remove-tag');
                if (removeBtn) {
                    e.stopPropagation();
                    removeTag(removeBtn.dataset.value);
                }
            });
            
            document.addEventListener('click', (e) => {
                if (!tagSelectionArea.contains(e.target) && !categoriaList.contains(e.target)) {
                    categoriaList.classList.remove('show');
                    tagSelectionArea.setAttribute('aria-expanded', 'false');
                }
            });

            loadInitialTags();
        }
    }

    // ========================================================================
    // LÓGICA DO SELETOR DE TEMA DE ACESSIBILIDADE
    // ========================================================================
    const themeRadios = document.querySelectorAll('.theme-switcher__radio');

    if (themeRadios.length > 0) {
        function applyTheme(theme) {
            body.classList.remove('dark-mode', 'high-contrast');
            if (theme === 'dark') body.classList.add('dark-mode');
            else if (theme === 'contrast') body.classList.add('high-contrast');
        }

        async function saveThemePreference(theme) {
            const csrfToken = getCsrfToken();
            if (!csrfToken) return;

            try {
                await fetch('/perfil/salvar-tema/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                    body: JSON.stringify({ theme: theme })
                });
            } catch (error) {
                console.error('Erro ao salvar preferência de tema:', error);
            }
        }
        
        function syncRadioState() {
            let currentTheme = 'light';
            if (body.classList.contains('dark-mode')) currentTheme = 'dark';
            else if (body.classList.contains('high-contrast')) currentTheme = 'contrast';
            
            const activeRadio = document.getElementById(`theme-${currentTheme}`);
            if (activeRadio) activeRadio.checked = true;
        }
        
        themeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.checked) {
                    const newTheme = radio.value;
                    applyTheme(newTheme); 
                    saveThemePreference(newTheme);
                }
            });
        });

        syncRadioState();
    }

    // ========================================================================
    // LÓGICA DE FAVORITAR EMPRESAS (EVENT DELEGATION)
    // ========================================================================
    function updateFavoriteButton(button, isFavorito) {
        button.setAttribute('aria-pressed', String(isFavorito));
        button.setAttribute('aria-label', isFavorito ? 'Remover dos favoritos' : 'Adicionar aos favoritos');
        button.classList.toggle('btn-danger', isFavorito);
        button.classList.toggle('btn-outline-light', !isFavorito && button.classList.contains('btn-lg'));
        button.classList.toggle('btn-light', !isFavorito && !button.classList.contains('btn-lg'));
        const icon = button.querySelector('i');
        if (icon) {
            icon.classList.toggle('bi-heart-fill', isFavorito);
            icon.classList.toggle('bi-heart', !isFavorito);
        }
    }

    body.addEventListener('click', async (event) => {
        const favButton = event.target.closest('#btn-favorito, [data-action="toggle-favorito"]');
        if (!favButton) return;
        const url = favButton.dataset.url;
        const csrfToken = getCsrfToken();
        if (!url || !csrfToken) return;
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!response.ok) throw new Error('Falha na requisição ao servidor.');
            const data = await response.json();
            if (data.status === 'ok') {
                updateFavoriteButton(favButton, data.is_favorito);
            }
        } catch (error) {
            console.error("Erro ao favoritar:", error);
            alert("Ocorreu um erro ao tentar favoritar. Tente novamente.");
        }
    });
});