// service_list.js

document.addEventListener('DOMContentLoaded', function () {
    const servicesGrid = document.getElementById('servicesGrid');
    const serviceModal = document.getElementById('serviceModal');
    const closeModal = document.getElementById('closeModal');
    let map = null;

    // Service name click event
    servicesGrid.addEventListener('click', function (e) {
        if (e.target.classList.contains('service-name')) {
            const serviceId = e.target.dataset.serviceId;
            openServiceModal(serviceId);
        }
    });

    // Close modal event
    closeModal.addEventListener('click', function () {
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
                    ${data.announcement ? `
                      <div class="mb-3 flex items-center space-x-2 text-yellow-700 bg-yellow-50 border-l-2 border-yellow-400 px-3 py-2 rounded-lg">
                        <svg class="h-4 w-4 flex-shrink-0 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/>
                        </svg>
                        <p class="text-sm">
                          ${data.announcement}
                        </p>
                      </div>
                    ` : ''}
                    <div class="mt-4">
                        <h4 class="font-semibold text-gray-100">Description:</h4>
                        <dl class="mt-2 space-y-1">
                            ${Object.entries(data.description).map(([key, value]) => `
                                <div class="flex">
                                    <dt class="text-sm font-medium text-gray-400 w-1/3">${key}:</dt>
                                    <dd class="text-sm text-gray-300 ml-2">${value}</dd>
                                </div>
                            `).join('')}
                        </dl>
                    </div>
                `;

                // Populate reviews
                const reviewsContainer = document.getElementById('modalReviews');
                reviewsContainer.innerHTML = '<h4 class="font-semibold mt-4 text-gray-100">Reviews:</h4>';

                if (data.reviews && data.reviews.length > 0) {
                    data.reviews.forEach(review => {
                        const hasResponseText = review.ResponseText && review.ResponseText.trim() !== "";
                        let respondedAtDate = "Responded just now";
                        if (review.RespondedAt) {
                            respondedAtDate = formatDateTime(review.RespondedAt);
                        }

                        reviewsContainer.innerHTML += `
                            <div class="review mb-2 p-2 bg-gray-700 rounded">
                                <div class="flex justify-between items-start">
                                    <p class="text-gray-100"><strong>${review.Username}</strong> - ${review.RatingStars} stars</p>
                                    
                                    <!-- Add the flag button here -->
                                    ${hasResponseText ? `
                                    ` : `
                                        <div class="flag-status-container" data-review-id="${review.ReviewId}">
                                            <button onclick="openFlagModal('REVIEW', '${review.ReviewId}')" 
                                                    class="flag-button text-gray-400 hover:text-red-400 transition-colors duration-200"
                                                    title="Report this review">
                                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                                                </svg>
                                            </button>
                                        </div>
                                    `}
                                </div>
                                
                                <p class="text-sm text-gray-300">${review.RatingMessage}</p>
                                ${hasResponseText ? `
                                    <div class="mt-3 p-3 bg-gray-600 rounded" id="reviewResponse-${review.ReviewId}">
                                        <p class="font-semibold text-gray-100">Provider Response:</p>
                                        <p class="text-gray-300">${review.ResponseText}</p>
                                        <p class="text-sm text-gray-400">Responded on ${respondedAtDate}</p>
                                    </div>
                                ` : `
                                    <button class="respond-button bg-blue-600 text-white py-1 px-3 rounded mt-2 hover:bg-blue-700" 
                                            onclick="showResponseForm('${serviceId}', '${review.ReviewId}')">
                                        Respond
                                    </button>
                                    <div id="responseForm-${review.ReviewId}" class="response-form hidden mt-2">
                                        <textarea id="responseText-${review.ReviewId}" class="w-full p-2 border rounded focus:outline-none focus:border-blue-700 focus:ring-4 bg-gray-600 text-gray-100 border-gray-500" rows="2" placeholder="Write your response here..."></textarea>
                                        <button class="send-response bg-green-600 text-white py-1 px-3 rounded mt-2 hover:bg-green-700"
                                                onclick="sendResponse('${serviceId}', '${review.ReviewId}')">
                                            Send Response
                                        </button>
                                    </div>
                                `}
                            </div>
                        `;
                        checkFlagStatus('REVIEW', review.ReviewId);

                    });
                } else {
                    reviewsContainer.innerHTML += '<p class="text-gray-400">No reviews yet.</p>';
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

    const searchInput = document.getElementById('serviceSearch');
    const serviceCards = document.querySelectorAll('.service-box');

    searchInput.addEventListener('input', function (e) {
        const searchTerm = e.target.value.toLowerCase();

        serviceCards.forEach(card => {
            const serviceName = card.querySelector('.service-name').textContent.toLowerCase();
            const serviceCategory = card.querySelector('.bg-blue-900').textContent.toLowerCase().trim();

            // Check if either the service name or category contains the search term
            if (serviceName.includes(searchTerm) || serviceCategory.includes(searchTerm)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

async function checkFlagStatus(contentType, objectId) {
    try {
        const response = await fetch(`/moderation/check_flag_status/${contentType}/${objectId}/`);
        const data = await response.json();

        const container = document.querySelector(`.flag-status-container[data-review-id="${objectId}"]`);
        if (!container) return;

        if (data.hasPendingFlags) {
            // Replace the flag button with a pending icon
            container.innerHTML = `
                <div class="text-yellow-500" title="This review has been reported and is pending moderation">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
            `;
        } else if (data.userHasFlagged) {
            // Show flagged state
            const flagButton = container.querySelector('.flag-button');
            if (flagButton) {
                flagButton.classList.add('text-red-400');
                flagButton.classList.remove('text-gray-400');
                flagButton.title = 'You have reported this review';
                flagButton.disabled = true;
            }
        }
    } catch (error) {
        console.error('Error checking flag status:', error);
    }
}

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
        body: new URLSearchParams({responseText: responseText}),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                // Update the response container
                responseContainer.innerHTML = `
                <div class="mt-3 p-3 bg-gray-600 rounded">
                    <p class="font-semibold text-gray-100">Provider Response:</p>
                    <p class="text-gray-300">${responseText}</p>
                    <p class="text-sm text-gray-400">Responded just now</p>
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
