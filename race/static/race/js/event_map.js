document.addEventListener('DOMContentLoaded', function() {
    var mapElement = document.getElementById('map');
    var latitude = mapElement.getAttribute('data-latitude');
    var longitude = mapElement.getAttribute('data-longitude');

    if (latitude && longitude) {
        var map = L.map('map').setView([latitude, longitude], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        var marker = L.marker([latitude, longitude]).addTo(map);
    } else {
        console.log("Координаты местоположения не доступны.");
    }
});
