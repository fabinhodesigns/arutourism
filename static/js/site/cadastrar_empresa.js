// Garante que todo o código só execute após o carregamento completo do HTML.
document.addEventListener('DOMContentLoaded', function () {

    // ======================================
    // INICIALIZAÇÃO GERAL E VARIÁVEIS
    // ======================================

    // Variáveis globais para o mapa
    let map;
    let marker;

    // Constantes para elementos da aba de importação
    const drop = document.getElementById('drop');
    const fileInput = document.getElementById('arquivo');
    const btnSelect = document.getElementById('btn-select');
    const fileNameEl = document.getElementById('fn');
    const loading = document.getElementById('loading-overlay');
    const importErrors = document.getElementById('import-errors');

    // ======================================
    // MAPA (LEAFLET)
    // ======================================

    const mapContainer = document.getElementById('map');
    // VERIFICAÇÃO: Só inicializa o mapa se o container existir e não tiver sido inicializado antes.
    // Isso corrige o erro 'Map container is already initialized' no recarregamento.
    if (mapContainer && !mapContainer._leaflet_id) {
        map = L.map('map').setView([-28.9371, -49.4840], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        map.on('click', function (e) {
            if (marker) {
                map.removeLayer(marker);
            }
            marker = L.marker(e.latlng, { keyboard: true }).addTo(map);
            document.getElementById('id_latitude').value = e.latlng.lat.toFixed(6);
            document.getElementById('id_longitude').value = e.latlng.lng.toFixed(6);
        });
    }

    // ======================================
    // FORMULÁRIO INDIVIDUAL
    // ======================================

    // Preview da imagem
    const inputImg = document.getElementById('id_imagem');
    const imgPrev = document.getElementById('img-preview');
    if (inputImg && imgPrev) {
        inputImg.addEventListener('change', () => {
            const file = inputImg.files && inputImg.files[0];
            if (!file) return;
            const url = URL.createObjectURL(file);
            imgPrev.src = url;
            // Libera a memória do objeto URL após o carregamento da imagem
            imgPrev.onload = () => URL.revokeObjectURL(url);
        });
    }

    // Máscaras e toggles de campos (usando jQuery como no original)
    $('#id_cep').on('input', function () {
        $(this).val($(this).val().replace(/\D/g, '').slice(0, 8));
    });

    function toggleFields() {
        $('#id_telefone').prop('disabled', $('#id_sem_telefone').is(':checked'));
        $('#id_email').prop('disabled', $('#id_sem_email').is(':checked'));
    }
    $('#id_sem_telefone, #id_sem_email').on('change', toggleFields);
    toggleFields(); // Executa uma vez no carregamento da página

    // Submissão do formulário individual via AJAX
    $('#empresa-form').on('submit', async function (e) {
        e.preventDefault();
        const form = this;
        const formData = new FormData(form);
        const submitter = e.originalEvent?.submitter;
        if (submitter && submitter.name) {
            formData.append(submitter.name, submitter.value);
        }

        let response;
        try {
            response = await fetch(form.action || window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: { 'Accept': 'application/json' }
            });
        } catch (err) {
            return toast('Falha de conexão com o servidor. Tente novamente.', true);
        }

        // Limpa notificações antigas
        $('#notification-container').empty();
        hideOverlay();

        if (response.ok) {
            let data = {};
            try { data = await response.json(); } catch (_) { }

            toast(data.message || 'Salvo com sucesso!');

            const action = data.action || 'redirect';
            const redirectUrl = data.redirect_url; // O template Django não é processado aqui

            if (action === 'redirect' && redirectUrl) {
                setTimeout(() => location.href = redirectUrl, 900);
            } else { // 'save_and_add'
                form.reset();
                if (marker) {
                    map.removeLayer(marker);
                    marker = null;
                }
                // Reseta a imagem para a padrão (o path precisa ser passado do Django)
                if (imgPrev && imgPrev.dataset.defaultSrc) {
                    imgPrev.src = imgPrev.dataset.defaultSrc;
                }
            }
            return;
        }

        // Tratamento de erros
        const contentType = (response.headers.get('content-type') || '').toLowerCase();
        if (contentType.includes('application/json')) {
            let payload = null;
            try { payload = await response.clone().json(); } catch (_) { }
            if (payload) {
                if (payload.html) { showOverlay(payload.html); return; }
                if (payload.error) { toast(payload.error, true); return; }
            }
        }

        const htmlText = await response.text();
        const doc = new DOMParser().parseFromString(htmlText, 'text/html');
        const errorSource = doc.querySelector('#errors-from-server');
        showOverlay(errorSource ? errorSource.innerHTML : '<p>Ocorreu um erro desconhecido.</p>');
    });

    // ======================================
    // UPLOAD DE ARQUIVO EM LOTE (ABA 2)
    // ======================================

    if (btnSelect) {
        btnSelect.addEventListener('click', () => fileInput && fileInput.click());
    }
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            fileNameEl.textContent = fileInput.files[0] ? fileInput.files[0].name : '';
        });
    }

    if (drop) {
        ['dragenter', 'dragover'].forEach(eventName => {
            drop.addEventListener(eventName, e => {
                e.preventDefault();
                e.stopPropagation();
                drop.classList.add('drag');
            });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            drop.addEventListener(eventName, e => {
                e.preventDefault();
                e.stopPropagation();
                drop.classList.remove('drag');
            });
        });
        drop.addEventListener('drop', e => {
            const file = e.dataTransfer.files && e.dataTransfer.files[0];
            if (file && fileInput) {
                fileInput.files = e.dataTransfer.files;
                fileNameEl.textContent = file.name;
            }
        });
    }

    $('#form-import').on('submit', async function (e) {
        e.preventDefault();
        if (!fileInput || !fileInput.files.length) {
            drop?.classList.add('border-danger');
            showImportErrors(['Selecione um arquivo primeiro.']);
            return;
        }

        if (loading) loading.style.display = 'flex';

        let response;
        try {
            const formData = new FormData(this);
            response = await fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: { 'Accept': 'application/json' }
            });
        } catch (err) {
            if (loading) loading.style.display = 'none';
            drop?.classList.add('border-danger');
            showImportErrors(['Falha de conexão com o servidor. Tente novamente.']);
            return;
        }

        if (loading) loading.style.display = 'none';
        drop?.classList.remove('border-danger');
        hideImportErrors();

        if (response.ok) {
            const data = await response.json();
            toast(`Importação concluída: ${data.importados} registro(s).`);
            if (data.redirect && data.redirect_url) {
                setTimeout(() => location.href = data.redirect_url, 900);
            }
        } else {
            drop?.classList.add('border-danger');
            let payload = null;
            try { payload = await response.json(); } catch (_) { }

            if (payload) {
                const messages = payload.mensagens?.length ? payload.mensagens : [payload.error || 'Falha ao importar.'];
                showImportErrors(messages);
            } else {
                showImportErrors(['Falha ao importar. Verifique o arquivo e tente novamente.']);
            }
        }
    });

    // ======================================
    // FUNÇÕES AUXILIARES (HELPERS)
    // ======================================

    // Overlay de erros do formulário individual
    let escListener = null;
    function showOverlay(innerHtml) {
        const wrap = document.createElement('div');
        wrap.id = 'form-errors-overlay';
        wrap.className = 'message-overlay';
        wrap.setAttribute('role', 'dialog');
        wrap.setAttribute('aria-modal', 'true');
        wrap.innerHTML = `
            <div class="message-box position-relative" role="document">
                <button type="button" class="btn-close" aria-label="Fechar" data-dismiss-overlay style="position:absolute;top:.5rem;right:.5rem;"></button>
                ${sanitizeOverlayHtml(innerHtml)}
            </div>
        `;
        wrap.addEventListener('click', e => { if (e.target === wrap) hideOverlay(); });
        wrap.querySelector('[data-dismiss-overlay]').addEventListener('click', hideOverlay);

        escListener = e => { if (e.key === 'Escape') hideOverlay(); };
        document.addEventListener('keydown', escListener);

        document.getElementById('notification-container').appendChild(wrap);
    }

    function hideOverlay() {
        const overlay = document.getElementById('form-errors-overlay');
        if (overlay) {
            overlay.remove();
            if (escListener) document.removeEventListener('keydown', escListener);
        }
    }

    function sanitizeOverlayHtml(html) {
        const tmp = document.createElement('div');
        tmp.innerHTML = (html || '').trim();
        const innerBox = tmp.querySelector('.message-box');
        // Pega o conteúdo de dentro do .message-box se ele existir
        const content = innerBox ? innerBox.innerHTML : tmp.innerHTML;

        const finalDiv = document.createElement('div');
        finalDiv.innerHTML = content;
        if (!finalDiv.querySelector('h1,h2,h3,h4,h5,h6')) {
            const title = document.createElement('h5');
            title.className = 'mb-2';
            title.textContent = 'Por favor, corrija os seguintes erros:';
            finalDiv.prepend(title);
        }
        return finalDiv.innerHTML;
    }

    // Erros do formulário de importação
    function showImportErrors(list) {
        if (!importErrors) return;
        importErrors.classList.remove('d-none');
        importErrors.innerHTML = `
            <strong>Ocorreram erros na importação:</strong>
            <ul class="mt-2 mb-0">${list.slice(0, 100).map(m => `<li>${m}</li>`).join('')}</ul>
            <p class="mt-2 mb-0 text-muted">Se o problema persistir, contate o suporte.</p>
        `;
        importErrors.focus();
    }

    function hideImportErrors() {
        if (!importErrors) return;
        importErrors.classList.add('d-none');
        importErrors.innerHTML = '';
    }

    // Notificações Toast
    function toast(message, isDanger = false) {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const toastEl = document.createElement('div');
        toastEl.className = 'toast-notification' + (isDanger ? ' bg-danger' : '');
        toastEl.innerHTML = `<span>${message}</span>`;

        container.appendChild(toastEl);

        setTimeout(() => toastEl.classList.add('show'), 30);
        setTimeout(() => {
            if (toastEl.isConnected) {
                toastEl.classList.remove('show');
                setTimeout(() => toastEl.remove(), 300);
            }
        }, 4200);
    }

    const tagSearchInput = document.getElementById('tag-search-input');
    if (tagSearchInput) {
        tagSearchInput.addEventListener('input', function () {
            const searchTerm = this.value.toLowerCase();
            const allTags = document.querySelectorAll('.tag-list-container .form-check');

            allTags.forEach(function (tagElement) {
                const label = tagElement.querySelector('label');
                if (label) {
                    const labelText = label.innerText.toLowerCase();
                    if (labelText.includes(searchTerm)) {
                        tagElement.style.display = 'block';
                    } else {
                        tagElement.style.display = 'none';
                    }
                }
            });
        });
    }

});