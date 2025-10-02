// Em static/js/site/editar_empresa.js

// Garante que o script só execute após o HTML estar pronto
document.addEventListener('DOMContentLoaded', function () {

    // Função para cuidar do preview da imagem
    function initImagePreview() {
        const fileInput = document.querySelector('input[type="file"][name$="imagem"]');
        const previewEl = document.getElementById('img-preview');

        if (fileInput && previewEl) {
            fileInput.addEventListener('change', function () {
                const file = this.files && this.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = e => previewEl.src = e.target.result;
                reader.readAsDataURL(file);
            });
        }
    }

    // Função para inicializar o mapa Leaflet
    function initLeafletMap() {
        const mapContainer = document.getElementById('map');
        // Só continua se o mapa existir e não tiver sido inicializado
        if (!mapContainer || !window.L || mapContainer._leaflet_id) {
            return;
        }

        const latInput = document.getElementById('id_latitude');
        const lngInput = document.getElementById('id_longitude');
        const DEFAULT_COORDS = { lat: -28.937100, lng: -49.484000 };

        let lat = parseFloat(latInput?.value);
        let lng = parseFloat(lngInput?.value);

        if (Number.isNaN(lat)) lat = DEFAULT_COORDS.lat;
        if (Number.isNaN(lng)) lng = DEFAULT_COORDS.lng;

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

        // Permite ajuste fino com as setas do teclado
        mapContainer.addEventListener('keydown', e => {
            const step = 0.0005;
            const currentPos = marker.getLatLng();
            let moved = true;

            if (e.key === 'ArrowUp') marker.setLatLng([currentPos.lat + step, currentPos.lng]);
            else if (e.key === 'ArrowDown') marker.setLatLng([currentPos.lat - step, currentPos.lng]);
            else if (e.key === 'ArrowLeft') marker.setLatLng([currentPos.lat, currentPos.lng - step]);
            else if (e.key === 'ArrowRight') marker.setLatLng([currentPos.lat, currentPos.lng + step]);
            else moved = false;

            if (moved) {
                updateInputs(marker.getLatLng());
                e.preventDefault();
            }
        });

        // Força o mapa a se redimensionar corretamente
        setTimeout(() => map.invalidateSize(), 0);
    }

    // Chama as funções de inicialização
    initImagePreview();
    initLeafletMap();

    // A lógica de envio AJAX pode ser mantida aqui, se você planeja usá-la.
    // Lembre-se de remover as tags Django do código, passando os valores necessários
    // via atributos data-*, como fizemos anteriormente.
});