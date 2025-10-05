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
    const importErrors = document.getElementById('import-errors'); // Usado para mostrar o relatório

    // ======================================
    // MAPA (LEAFLET)
    // ======================================

    const mapContainer = document.getElementById('map');
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

    const inputImg = document.getElementById('id_imagem');
    const imgPrev = document.getElementById('img-preview');
    if (inputImg && imgPrev) {
        inputImg.addEventListener('change', () => {
            const file = inputImg.files && inputImg.files[0];
            if (!file) return;
            const url = URL.createObjectURL(file);
            imgPrev.src = url;
            imgPrev.onload = () => URL.revokeObjectURL(url);
        });
    }

    $('#id_cep').on('input', function () {
        $(this).val($(this).val().replace(/\D/g, '').slice(0, 8));
    });

    function toggleFields() {
        $('#id_telefone').prop('disabled', $('#id_sem_telefone').is(':checked'));
        $('#id_email').prop('disabled', $('#id_sem_email').is(':checked'));
    }
    $('#id_sem_telefone, #id_sem_email').on('change', toggleFields);
    toggleFields();

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

        $('#notification-container').empty();
        hideOverlay();

        if (response.ok) {
            let data = {};
            try { data = await response.json(); } catch (_) { }
            toast(data.message || 'Salvo com sucesso!');
            if (data.action === 'redirect' && data.redirect_url) {
                setTimeout(() => location.href = data.redirect_url, 900);
            } else {
                form.reset();
                if (marker) {
                    map.removeLayer(marker);
                    marker = null;
                }
                if (imgPrev && imgPrev.dataset.defaultSrc) {
                    imgPrev.src = imgPrev.dataset.defaultSrc;
                }
            }
            return;
        }

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

    // --- BLOCO DE SUBMISSÃO DO UPLOAD - ATUALIZADO ---
    $('#form-import').on('submit', async function (e) {
        e.preventDefault();
        if (!fileInput || !fileInput.files.length) {
            drop?.classList.add('border-danger');
            showImportReport(['Selecione um arquivo primeiro.'], 'Erro', 'alert-danger');
            return;
        }

        if (loading) loading.style.display = 'flex';
        hideImportErrors();
        drop?.classList.remove('border-danger');

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
            showImportReport(['Falha de conexão com o servidor. Tente novamente.'], 'Erro de Conexão', 'alert-danger');
            return;
        }

        if (loading) loading.style.display = 'none';
        
        let data = {};
        try {
            data = await response.json();
        } catch (err) {
            showImportReport(['Ocorreu um erro inesperado ao processar a resposta do servidor.'], 'Erro Crítico', 'alert-danger');
            return;
        }

        if (response.ok && data.ok) {
            // SUCESSO: Monta a mensagem do relatório
            let reportTitle = 'Importação Concluída!';
            let reportMessages = [
                `<strong>${data.criados || 0}</strong> registros novos foram criados.`,
                `<strong>${data.atualizados || 0}</strong> registros existentes foram atualizados.`,
                `<strong>${data.sem_alteracao || 0}</strong> registros permaneceram sem alterações.`
            ];
            let alertClass = 'alert-success';

            if (data.erros > 0) {
                reportTitle = `Importação Parcialmente Concluída com ${data.erros} Erros`;
                alertClass = 'alert-warning';
                reportMessages.push(`<strong>${data.erros}</strong> linhas continham erros:`);
                const errorList = data.mensagens.map(msg => `<li><small>${msg}</small></li>`).join('');
                reportMessages.push(`<ul class="mt-1 mb-0" style="max-height: 150px; overflow-y: auto;">${errorList}</ul>`);
            }
            
            showImportReport(reportMessages, reportTitle, alertClass);

            if (fileInput) fileInput.value = '';
            if (fileNameEl) fileNameEl.textContent = '';
        } else {
            // ERRO GERAL
            drop?.classList.add('border-danger');
            const messages = data.mensagens?.length ? data.mensagens : [data.error || 'Falha ao importar. Verifique o console para mais detalhes.'];
            showImportReport(messages, 'Falha na Importação', 'alert-danger');
        }
    });

    // ======================================
    // FUNÇÕES AUXILIARES (HELPERS)
    // ======================================

    let escListener = null;
    function showOverlay(innerHtml) { /* ... (sem alterações) ... */ }
    function hideOverlay() { /* ... (sem alterações) ... */ }
    function sanitizeOverlayHtml(html) { /* ... (sem alterações) ... */ }

    // --- FUNÇÃO DE RELATÓRIO DE IMPORTAÇÃO - ATUALIZADA ---
    function showImportReport(list, title = 'Ocorreram erros na importação:', alertClass = 'alert-danger') {
        if (!importErrors) return;
        importErrors.className = 'mt-4 alert alert-dismissible fade show'; // Reseta as classes
        importErrors.classList.add(alertClass);

        importErrors.innerHTML = `
            <div class="d-flex justify-content-between">
                <h5 class="alert-heading">${title}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            </div>
            <hr>
            <ul class="mb-0">${Array.isArray(list) ? list.map(m => `<li>${m}</li>`).join('') : list}</ul>
        `;
        
        importErrors.setAttribute('tabindex', '-1');
        importErrors.focus();

        const closeButton = importErrors.querySelector('.btn-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                hideImportErrors();
            });
        }
    }

    function hideImportErrors() {
        if (!importErrors) return;
        importErrors.classList.add('d-none');
        importErrors.innerHTML = '';
    }

    function toast(message, isDanger = false) { /* ... (sem alterações) ... */ }

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