document.addEventListener('DOMContentLoaded', function() {

    function initDetailMap() {
        const mapContainer = document.getElementById('map');
        if (!mapContainer || !window.L || mapContainer._leaflet_id) return;

        const lat = parseFloat(mapContainer.dataset.lat);
        const lon = parseFloat(mapContainer.dataset.lon);
        const nomeEmpresa = mapContainer.dataset.nome;

        if (Number.isNaN(lat) || Number.isNaN(lon)) return;

        const map = L.map(mapContainer, { scrollWheelZoom: false }).setView([lat, lon], 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
            maxZoom: 19
        }).addTo(map);
        L.marker([lat, lon], { title: nomeEmpresa }).addTo(map);
    }

    function initLightGallery() {
        const gallery = document.getElementById('lightgallery');
        if (gallery && typeof lightGallery !== 'undefined') {
            lightGallery(gallery, { selector: '.gallery-item', download: false });
        }
    }

    function initStarRating() {
        const starRatingForm = document.querySelector('.star-rating-form');
        if (!starRatingForm) return;

        const stars = Array.from(starRatingForm.querySelectorAll('label'));
        const radios = starRatingForm.querySelectorAll('input[type="radio"]');

        function updateStarAppearance() {
            let selectedValue = 0;
            radios.forEach(radio => { if (radio.checked) { selectedValue = parseInt(radio.value, 10); } });
            stars.forEach((star, index) => {
                if (index < selectedValue) { star.classList.add('selected'); } 
                else { star.classList.remove('selected'); }
            });
        }
        
        stars.forEach((star, index) => {
            star.addEventListener('mouseover', () => { stars.forEach((s, i) => { if (i <= index) { s.classList.add('hover'); } else { s.classList.remove('hover'); } }); });
            star.addEventListener('click', updateStarAppearance);
        });

        starRatingForm.addEventListener('mouseleave', () => { stars.forEach(s => s.classList.remove('hover')); });
        updateStarAppearance();
    }

    function initDeleteReview() {
        const reviewList = document.getElementById('review-list');
        const csrfTokenInput = document.getElementById('csrf-token-for-js');
        const csrfToken = csrfTokenInput ? csrfTokenInput.value : null;

        if (reviewList && csrfToken) {
            reviewList.addEventListener('click', async function (event) {
                const deleteButton = event.target.closest('.btn-delete-review');
                if (!deleteButton) return;
                
                const reviewId = deleteButton.dataset.id;
                const url = `/avaliacao/deletar/${reviewId}/`;

                const result = await Swal.fire({
                    title: 'Tem certeza?',
                    text: "Você não poderá reverter esta ação!",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#d33',
                    cancelButtonColor: '#6c757d',
                    confirmButtonText: 'Sim, remover!',
                    cancelButtonText: 'Cancelar'
                });

                if (result.isConfirmed) {
                    try {
                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': csrfToken,
                                'X-Requested-With': 'XMLHttpRequest',
                                'Content-Type': 'application/json'
                            }
                        });

                        if (!response.ok) { throw new Error('Falha na requisição.'); }
                        const data = await response.json();

                        if (data.status === 'success') {
                            await Swal.fire('Removida!', 'Sua avaliação foi removida.', 'success');
                            location.reload();
                        } else {
                            throw new Error(data.message || 'Não foi possível remover a avaliação.');
                        }
                    } catch (error) {
                        console.error('Erro:', error);
                        Swal.fire('Erro!', error.message || 'Ocorreu um erro ao tentar remover.', 'error');
                    }
                }
            });
        }
    }

    initDetailMap();
    initLightGallery();
    initStarRating();
    initDeleteReview();
});