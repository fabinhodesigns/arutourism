document.addEventListener('DOMContentLoaded', function () {

  const overlay = document.getElementById('searchOverlay');
  if (overlay) {
    const panel = overlay.querySelector('.search-panel');
    const openBtn = document.getElementById('open-search');
    const closeBtn = document.getElementById('close-search');
    const qInput = document.getElementById('f-q');

    function openSearch() {
      overlay.classList.add('open');
      overlay.setAttribute('aria-hidden', 'false');
      document.body.classList.add('no-scroll');
      setTimeout(() => qInput && qInput.focus(), 30);
    }
    function closeSearch() {
      overlay.classList.remove('open');
      overlay.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('no-scroll');
      openBtn && openBtn.focus();
    }

    if (openBtn) openBtn.addEventListener('click', openSearch);
    if (closeBtn) closeBtn.addEventListener('click', closeSearch);

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && overlay.classList.contains('open')) {
        closeSearch();
      }
    });

    overlay.addEventListener('click', (e) => {
      if (!panel.contains(e.target)) closeSearch();
    });
  }

  function wireFilter(inputId, listId, hiddenId, selectedValue) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);
    const hidden = document.getElementById(hiddenId);
    if (!input || !list || !hidden) return;

    if (selectedValue) {
      const el = list.querySelector(`.dropdown-item[data-value="${CSS.escape(selectedValue)}"]`);
      if (el) { input.placeholder = el.textContent.trim(); }
      hidden.value = selectedValue;
    }

    input.addEventListener('focus', () => list.classList.add('show'));
    input.addEventListener('click', () => list.classList.toggle('show'));

    input.addEventListener('input', () => {
      const q = input.value.toLowerCase();
      list.querySelectorAll('.dropdown-item').forEach(it => {
        const txt = it.textContent.toLowerCase();
        it.style.display = txt.includes(q) ? '' : 'none';
      });
      list.classList.add('show');
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') { e.preventDefault(); const first = list.querySelector('.dropdown-item:not([style*="display: none"])'); (first || input).focus(); }
      if (e.key === 'Escape') { list.classList.remove('show'); }
    });

    list.addEventListener('click', (e) => {
      const item = e.target.closest('.dropdown-item'); if (!item) return;
      hidden.value = item.dataset.value;
      input.value = '';
      input.placeholder = item.textContent.trim();
      list.classList.remove('show');
    });

    list.addEventListener('keydown', (e) => {
      const items = [...list.querySelectorAll('.dropdown-item')].filter(i => i.style.display !== 'none');
      const idx = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); (items[idx + 1] || items[0]).focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); (items[idx - 1] || items[items.length - 1]).focus(); }
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); document.activeElement.click(); }
      if (e.key === 'Escape') { e.preventDefault(); list.classList.remove('show'); input.focus(); }
    });

    document.addEventListener('click', (e) => {
      if (!list.contains(e.target) && e.target !== input) { list.classList.remove('show'); }
    });
  }

  const initialCategoria = document.getElementById('categoria-hidden')?.value;
  const initialCidade = document.getElementById('cidade-hidden')?.value;

  wireFilter('categoria-input', 'categoria-list', 'categoria-hidden', initialCategoria);
  wireFilter('cidade-input', 'cidade-list', 'cidade-hidden', initialCidade);
});