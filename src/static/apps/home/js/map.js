// map.js

// Initialize the map
const map = L.map('map').setView([40.7128, -74.0060], 12);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

// Initialize markers array
const markers = [];

// Iterate over itemsData to create markers
itemsData.forEach((item, index) => {
    if (item.Lat && item.Log) {
        const marker = L.marker([item.Lat, item.Log])
            .addTo(map)
            .bindPopup(`<b>${item.Name}</b><br>${item.Address}<br>Rating: ${item.Ratings}`)
            .on('click', () => {
                showServiceDetails(index); // Use index as identifier
            }); 
        markers.push(marker);
    }
});

// Adjust map view based on markers
if (markers.length > 0) {
    const group = L.featureGroup(markers);
    map.fitBounds(group.getBounds());
} else {
    map.setView([40.7128, -74.0060], 10);
}

// Update radius value display (if applicable)
const radiusInput = document.getElementById('radius');
const radiusValue = document.getElementById('radiusValue');
if (radiusInput && radiusValue) {
    radiusInput.addEventListener('input', function() {
        radiusValue.textContent = this.value + ' miles';
    });
}

// Function to show service details
async function showServiceDetails(index) {
    const service = itemsData[index];
    if (!service) {
        console.error(`Service with index ${index} not found.`);
        return;
    }

    // Populate service details
    document.getElementById('serviceId').textContent = service.Id || 'No id';
    document.getElementById('serviceName').textContent = service.Name || 'No Name';
    document.getElementById('serviceAddress').textContent = service.Address || 'N/A';
    document.getElementById('serviceType').textContent = service.Category || 'Unknown';
    document.getElementById('serviceRating').textContent = parseFloat(service.Ratings).toFixed(2) || 'N/A';
    document.getElementById('serviceDistance').textContent = service.Distance ? service.Distance + ' miles' : 'N/A';
    document.getElementById('serviceDescription').textContent = service.Description || 'No description available.';

    const getDirectionsBtn = document.getElementById('getDirections');
    
    if (service.MapLink) {
        getDirectionsBtn.href = service.MapLink;
        getDirectionsBtn.style.display = 'inline-block'; // Ensure the button is visible
    } else {
        getDirectionsBtn.href = '#';
        getDirectionsBtn.style.display = 'none'; // Hide the button if no MapLink
    }

    fetchAndDisplayReviews(service.Id, 1);

    const serviceDetailsDiv = document.getElementById('serviceDetails');
    if (serviceDetailsDiv) {
    serviceDetailsDiv.classList.remove('hidden');
    serviceDetailsDiv.classList.add('block');
    }
}

// Function to hide service details
document.getElementById('closeDetails').addEventListener('click', () => {
    const serviceDetailsDiv = document.getElementById('serviceDetails');
    if (serviceDetailsDiv) {
        serviceDetailsDiv.classList.add('hidden');
        serviceDetailsDiv.classList.remove('block'); // Optionally remove 'block'
    }
});

// Event listeners for service list buttons
const serviceButtons = document.querySelectorAll('.service-button, .service-row');
serviceButtons.forEach(button => {
    button.addEventListener('click', () => {
        const serviceId = parseInt(button.getAttribute('data-id'), 10);
        if (!isNaN(serviceId)) {
            showServiceDetails(serviceId);
        } else {
            console.error(`Invalid service ID: ${serviceId}`);
        }
    });
});

// Handle Review Submission (Example)
document.getElementById('submitReview').addEventListener('click', () => {
    const rating = document.getElementById('reviewRating').value;
    const reviewText = document.getElementById('reviewText').value;

    if (rating === 'Select a rating' || reviewText.trim() === '') {
        alert('Please provide a rating and review text.');
        return;
    }

    // TODO: Implement AJAX request to submit the review to the server
    alert('Review submitted successfully!');

    // Reset the review form
    document.getElementById('reviewRating').value = 'Select a rating';
    document.getElementById('reviewText').value = '';
});
