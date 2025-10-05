// ARQUIVO: static/js/site/editar_empresa.js (VERSÃO FINAL E COMPLETA)

document.addEventListener('DOMContentLoaded', function () {

    // --- INICIALIZA O SELETOR DE TAGS MODERNO ---
    if (typeof TomSelect !== 'undefined') {
        const el = document.getElementById('tom-select-tags');
        if (el) {
            new TomSelect(el, {
                plugins: ['remove_button'],
                create: false,
                sortField: { field: "text", direction: "asc" }
            });
        }
    }

    // --- LÓGICA PARA DELETAR IMAGENS DA GALERIA ---
    const galleryContainer = document.getElementById('image-gallery-container');
    if (galleryContainer) {
        galleryContainer.addEventListener('click', function (event) {
            const deleteButton = event.target.closest('.btn-delete-image');
            if (!deleteButton) return;

            const imageId = deleteButton.dataset.imageId;
            const csrfToken = deleteButton.dataset.csrf;
            const url = `/imagem-empresa/deletar/${imageId}/`;

            Swal.fire({
                title: 'Tem certeza?', text: 'Deseja realmente deletar esta imagem?', icon: 'warning',
                showCancelButton: true, confirmButtonColor: '#d33', cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sim, deletar!', cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    fetch(url, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            const imageCard = document.getElementById(`imagem-card-${imageId}`);
                            if (imageCard) imageCard.remove();
                            Swal.fire('Deletada!', data.message || 'A imagem foi removida.', 'success');
                        } else {
                            Swal.fire('Erro!', data.message || 'Não foi possível deletar a imagem.', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Erro ao deletar imagem:', error);
                        Swal.fire('Erro!', 'Ocorreu um erro de conexão.', 'error');
                    });
                }
            });
        });
    }

    // --- LÓGICA PARA DELETAR A EMPRESA INTEIRA COM CONFIRMAÇÃO ---
    const deleteEmpresaForm = document.getElementById('delete-empresa-form');
    if (deleteEmpresaForm) {
      deleteEmpresaForm.addEventListener('submit', function(e) {
        e.preventDefault();
        Swal.fire({
            title: 'Você tem certeza?',
            text: "Excluir uma empresa é uma ação irreversível. Todos os dados, imagens e avaliações serão perdidos para sempre.",
            icon: 'error',
            showCancelButton: true, confirmButtonColor: '#d33', cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sim, tenho certeza e quero excluir!', cancelButtonText: 'Cancelar'
          }).then((result) => {
            if (result.isConfirmed) {
              e.target.submit();
            }
          });
      });
    }

    // --- LÓGICA PARA DELETAR AVALIAÇÕES INDIVIDUAIS (COM ATUALIZAÇÃO DA UI) ---
    const reviewListContainer = document.getElementById('review-list-moderation');
    const reviewCountSpan = document.getElementById('review-count'); // Pega o span da contagem

    if (reviewListContainer && reviewCountSpan) {
      reviewListContainer.addEventListener('click', function(event) {
          const deleteButton = event.target.closest('.btn-delete-review');
          if (!deleteButton) return;

          const url = deleteButton.dataset.url;
          const csrfToken = document.querySelector('form#empresa-form [name=csrfmiddlewaretoken]').value;
          const reviewCard = deleteButton.closest('[id^="review-card-"]');

          Swal.fire({
            title: 'Confirmar exclusão?', text: "Esta avaliação será removida permanentemente.", icon: 'warning',
            showCancelButton: true, confirmButtonColor: '#d33', cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sim, remover!', cancelButtonText: 'Cancelar'
          }).then((result) => {
            if (result.isConfirmed) {
              fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' }
              })
              .then(response => response.json())
              .then(data => {
                if (data.status === 'success') {
                  Swal.fire('Removida!', 'A avaliação foi removida com sucesso.', 'success');

                  if(reviewCard) {
                    reviewCard.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    reviewCard.style.opacity = '0';
                    reviewCard.style.transform = 'translateX(-20px)';
                    setTimeout(() => {
                        reviewCard.remove();
                        
                        // --- INÍCIO DAS NOVAS LINHAS ---

                        // 1. ATUALIZA A CONTAGEM NO TÍTULO
                        let currentCount = parseInt(reviewCountSpan.textContent, 10);
                        reviewCountSpan.textContent = Math.max(0, currentCount - 1);

                        // 2. VERIFICA SE A LISTA FICOU VAZIA
                        const remainingReviews = reviewListContainer.querySelectorAll('[id^="review-card-"]');
                        if (remainingReviews.length === 0) {
                            // Cria e adiciona a mensagem de "nenhuma avaliação"
                            const emptyMessage = document.createElement('p');
                            emptyMessage.className = 'text-muted';
                            emptyMessage.textContent = 'Esta empresa ainda não recebeu nenhuma avaliação.';
                            reviewListContainer.appendChild(emptyMessage);
                        }
                        // --- FIM DAS NOVAS LINHAS ---

                    }, 500); // Espera a animação terminar para atualizar o resto
                  }
                } else {
                  Swal.fire('Erro!', data.message || 'Não foi possível remover a avaliação.', 'error');
                }
              })
              .catch(error => {
                console.error('Erro:', error);
                Swal.fire('Erro!', 'Ocorreu um problema de comunicação com o servidor.', 'error');
              });
            }
          });
      });
    }

    // --- FUNÇÃO DO MAPA (LEAFLET) ---
    function initLeafletMap() {
        const mapContainer = document.getElementById('map');
        if (!mapContainer || !window.L || mapContainer._leaflet_id) return;

        const latInput = document.getElementById('id_latitude');
        const lngInput = document.getElementById('id_longitude');
        const DEFAULT_COORDS = { lat: -28.937100, lng: -49.484000 };
        let lat = parseFloat(latInput?.value) || DEFAULT_COORDS.lat;
        let lng = parseFloat(lngInput?.value) || DEFAULT_COORDS.lng;

        const map = L.map(mapContainer, { keyboard: true }).setView([lat, lng], 14);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
        const marker = L.marker([lat, lng], { keyboard: true }).addTo(map);

        function updateInputs(latlng) {
            if (latInput) latInput.value = latlng.lat.toFixed(6);
            if (lngInput) lngInput.value = latlng.lng.toFixed(6);
        }

        map.on('click', e => {
            marker.setLatLng(e.latlng);
            updateInputs(e.latlng);
        });
    }

    initLeafletMap();
});