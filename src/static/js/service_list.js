// service_list.js

document.addEventListener('DOMContentLoaded', function() {
    const servicesGrid = document.getElementById('servicesGrid');
    const serviceModal = document.getElementById('serviceModal');
    const closeModal = document.getElementById('closeModal');
    let map = null;

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

    function openServiceModal(serviceId) {
        fetch(`/services/${serviceId}/details/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('modalServiceName').textContent = data.name;
                document.getElementById('modalDetails').innerHTML = `
                    <p><strong>Category:</strong> ${data.category}</p>
                    <p><strong>Address:</strong> ${data.address}</p>
                    ${data.is_active ? '' : '<p class="text-red-500">This service is currently unavailable.</p>'}
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
                        const hasResponseText = review.ResponseText && review.ResponseText.trim() !== "";
                        let respondedAtDate = "Responded just now";
                        if (review.RespondedAt) {
                            const date = new Date(review.RespondedAt);
                            const day = String(date.getDate()).padStart(2, '0');
                            const month = date.toLocaleString('default', { month: 'long' });
                            const year = date.getFullYear();
                            respondedAtDate = `${day} ${month} ${year}`;
                        }

                        reviewsContainer.innerHTML += `
                            <div class="review mb-2 p-2 bg-gray-100 rounded">
                                <p><strong>${review.Username}</strong> - ${review.RatingStars} stars</p>
                                <p class="text-sm text-gray-600">${review.RatingMessage}</p>
                                ${hasResponseText ? `
                                    <div class="mt-3 p-3 bg-blue-50 rounded" id="reviewResponse-${review.ReviewId}">
                                        <p class="font-semibold">Provider Response:</p>
                                        <p>${review.ResponseText}</p>
                                        <p class="text-sm text-gray-600">Responded at: ${respondedAtDate}</p>
                                    </div>
                                ` : `
                                    <button class="respond-button bg-blue-500 text-white py-1 px-3 rounded mt-2" 
                                            onclick="showResponseForm('${serviceId}', '${review.ReviewId}')">
                                        Respond
                                    </button>
                                    <div id="responseForm-${review.ReviewId}" class="response-form hidden mt-2">
                                        <textarea id="responseText-${review.ReviewId}" class="w-full p-2 border rounded" rows="2" placeholder="Write your response here..."></textarea>
                                        <button class="send-response bg-green-500 text-white py-1 px-3 rounded mt-2" 
                                                onclick="sendResponse('${serviceId}', '${review.ReviewId}')">
                                            Send Response
                                        </button>
                                    </div>
                                `}
                            </div>
                        `;
                    });
                } else {
                    reviewsContainer.innerHTML += '<p>No reviews yet.</p>';
                }

                serviceModal.classList.remove('hidden');
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
        mapContainer.style.height = '300px';
        map = L.map('modalMap').setView([latitude, longitude], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        L.marker([latitude, longitude]).addTo(map);
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
    }
});

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to toggle response form visibility
function showResponseForm(serviceId, reviewId) {
    const form = document.getElementById(`responseForm-${reviewId}`);
    form.classList.toggle('hidden');
}

// Function to send a response to a review
function sendResponse(serviceId, reviewId) {
    const responseText = document.getElementById(`responseText-${reviewId}`).value;
    if (responseText.trim() === '') {
        alert('Response cannot be empty.');
        return;
    }

    let responseContainer = document.getElementById(`reviewResponse-${reviewId}`);
    if (!responseContainer) {
        // Create the container if it doesn't exist
        responseContainer = document.createElement('div');
        responseContainer.id = `reviewResponse-${reviewId}`;
        // Insert it after the response form
        const responseForm = document.getElementById(`responseForm-${reviewId}`);
        responseForm.parentNode.insertBefore(responseContainer, responseForm.nextSibling);
    }

    const csrfToken = getCookie('csrftoken');
    fetch(`/services/${serviceId}/reviews/${reviewId}/respond/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
        },
        body: new URLSearchParams({ responseText: responseText }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            // Update the response container
            responseContainer.innerHTML = `
                <div class="mt-3 p-3 bg-blue-50 rounded">
                    <p class="font-semibold">Provider Response:</p>
                    <p>${responseText}</p>
                    <p class="text-sm text-gray-600">Responded just now</p>
                </div>
            `;

            const form = document.getElementById(`responseForm-${reviewId}`);
            if (form) {
                form.remove();
            }
        } else {
            alert(`Failed to send response: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(error.message);
    });
}
