document.addEventListener('DOMContentLoaded', function () {
    const openBtn = document.getElementById('open-search');
    const openBtnMobile = document.getElementById('open-search-mobile');
    const closeBtn = document.getElementById('close-search');
    const searchOverlay = document.getElementById('searchOverlay');
    const body = document.body;
    const qInput = document.getElementById('f-q');

    function openSearch() {
        if (searchOverlay) {
            searchOverlay.classList.add('open');
            searchOverlay.setAttribute('aria-hidden', 'false');
            body.classList.add('no-scroll');
            setTimeout(() => qInput && qInput.focus(), 180);
        }
    }

    function closeSearch() {
        if (searchOverlay) {
            searchOverlay.classList.remove('open');
            searchOverlay.setAttribute('aria-hidden', 'true');
            body.classList.remove('no-scroll'); // <<-- Bug corrigido aqui (era 'add')
            
            // CORREÇÃO DE ACESSIBILIDADE: Devolve o foco para o botão que abriu a busca
            openBtn && openBtn.focus();
        }
    }

    if (openBtn) openBtn.addEventListener('click', openSearch);
    if (openBtnMobile) openBtnMobile.addEventListener('click', openSearch);
    if (closeBtn) closeBtn.addEventListener('click', closeSearch);

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && searchOverlay && searchOverlay.classList.contains('open')) {
            closeSearch();
        }
    });

    if (searchOverlay) {
        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) {
                closeSearch();
            }
        });
    }

    // --- LÓGICA PARA SELEÇÃO DE MÚLTIPLAS TAGS (continua igual e correta) ---
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
                    if (item) {
                        addTag(item.dataset.value, item.textContent);
                    }
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
            const isExpanded = tagSelectionArea.getAttribute('aria-expanded') === 'true';
            tagSelectionArea.setAttribute('aria-expanded', String(!isExpanded));
            categoriaList.classList.toggle('show');
        });

        categoriaList.addEventListener('click', (e) => {
            const item = e.target.closest('.dropdown-item');
            if (!item) return;
            addTag(item.dataset.value, item.textContent);
        });

        tagSelectionArea.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.remove-tag');
            if (!removeBtn) return;
            e.stopPropagation();
            removeTag(removeBtn.dataset.value);
        });
        
        document.addEventListener('click', (e) => {
            if (!tagSelectionArea.contains(e.target) && !categoriaList.contains(e.target)) {
                categoriaList.classList.remove('show');
                tagSelectionArea.setAttribute('aria-expanded', 'false');
            }
        });

        loadInitialTags();
    }
});