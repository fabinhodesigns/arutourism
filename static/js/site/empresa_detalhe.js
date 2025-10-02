// Em static/js/site/empresa_detalhe.js

document.addEventListener('DOMContentLoaded', function() {

    // Função para inicializar o mapa de visualização
    function initDetailMap() {
        const mapContainer = document.getElementById('map');
        // Só continua se o mapa existir, a biblioteca Leaflet estiver carregada,
        // e o mapa ainda não tiver sido inicializado.
        if (!mapContainer || !window.L || mapContainer._leaflet_id) {
            return;
        }

        // Pega os dados do próprio container do mapa
        const lat = parseFloat(mapContainer.dataset.lat);
        const lon = parseFloat(mapContainer.dataset.lon);
        const nomeEmpresa = mapContainer.dataset.nome;

        // Verifica se as coordenadas são válidas
        if (Number.isNaN(lat) || Number.isNaN(lon)) {
            console.error("Coordenadas inválidas para o mapa.");
            return;
        }

        // Cria o mapa, desativando o zoom com o scroll do mouse
        const map = L.map(mapContainer, { scrollWheelZoom: false }).setView([lat, lon], 15);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
            maxZoom: 19
        }).addTo(map);

        // Adiciona o marcador (pin) no mapa
        L.marker([lat, lon], { title: nomeEmpresa }).addTo(map);
    }

    // Chama a função de inicialização
    initDetailMap();
});