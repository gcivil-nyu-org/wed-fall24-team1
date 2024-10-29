document.addEventListener('DOMContentLoaded', function() {
    const servicesGrid = document.getElementById('servicesGrid');
    const serviceSearch = document.getElementById('serviceSearch');
    const serviceModal = document.getElementById('serviceModal');
    const closeModal = document.getElementById('closeModal');
    let map = null;

    // Search functionality
    serviceSearch.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const serviceBoxes = servicesGrid.querySelectorAll('.service-box');

        serviceBoxes.forEach(box => {
            const serviceName = box.querySelector('.service-name').textContent.toLowerCase();
            const serviceCategory = box.querySelector('p').textContent.toLowerCase();
            if (serviceName.includes(searchTerm) || serviceCategory.includes(searchTerm)) {
                box.style.display = '';
            } else {
                box.style.display = 'none';
            }
        });
    });

    // Service name click event
    servicesGrid.addEventListener('click', function(e) {
        if (e.target.classList.contains('service-name')) {
            const serviceId = e.target.dataset.serviceId;
            openServiceModal(serviceId);
        }
    });

    // Close modal event
    closeModal.addEventListener('click', function() {
        serviceModal.classList.add('hidden');
    });

    // Function to open service modal
    function openServiceModal(serviceId) {
        fetch(`/services/${serviceId}/details/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('modalServiceName').textContent = data.name;
                document.getElementById('modalDetails').innerHTML = `
                    <p><strong>Category:</strong> ${data.category}</p>
                    <p><strong>Address:</strong> ${data.address}</p>
                    <div class="mt-4">
                        <h4 class="font-semibold">Description:</h4>
                        <dl class="mt-2 space-y-1">
                            ${Object.entries(data.description).map(([key, value]) => `
                                <div class="flex">
                                    <dt class="text-sm font-medium text-gray-500 w-1/3">${key}:</dt>
                                    <dd class="text-sm text-gray-900 ml-2">${value}</dd>
                                </div>
                            `).join('')}
                        </dl>
                    </div>
                `;

                // Populate reviews
                const reviewsContainer = document.getElementById('modalReviews');
                reviewsContainer.innerHTML = '<h4 class="font-semibold mt-4">Reviews:</h4>';
                if (data.reviews && data.reviews.length > 0) {
                    data.reviews.forEach(review => {
                        reviewsContainer.innerHTML += `
                            <div class="review mb-2 p-2 bg-gray-100 rounded">
                                <p><strong>${review.Username}</strong> - ${review.RatingStars} stars</p>
                                <p class="text-sm text-gray-600">${review.RatingMessage}</p>
                            </div>
                        `;
                    });
                } else {
                    reviewsContainer.innerHTML += '<p>No reviews yet.</p>';
                }

                serviceModal.classList.remove('hidden');

                // Initialize map after modal is visible
                setTimeout(() => {
                    initializeMap(data.latitude, data.longitude);
                }, 100);
            })
            .catch(error => console.error('Error:', error));
    }

    function initializeMap(latitude, longitude) {
        if (map) {
            map.remove();
        }
        const mapContainer = document.getElementById('modalMap');
        mapContainer.style.height = '300px'; // Set a fixed height
        map = L.map('modalMap').setView([latitude, longitude], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        L.marker([latitude, longitude]).addTo(map);

        // Force a resize event on the map
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
    }

});