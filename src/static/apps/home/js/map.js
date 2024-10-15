// map.js

// Data passed from Django template
const itemsData = window.itemsData || [];

const map = L.map('map').setView([40.7128, -74.0060], 12);

// Load OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

const markers = [];

itemsData.forEach(item => {
    if (item.Lat && item.Log) {
        const marker = L.marker([item.Lat, item.Log])
            .addTo(map)
            .bindPopup(`<b>${item.Name}</b><br>${item.Address}<br>Rating: ${item.Ratings}`);
        markers.push(marker);
    }
});

if (markers.length > 0) {
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds());
} else {
    map.setView([40.7128, -74.0060], 10);
}



