function toggleEdit() {
    var viewSection = document.getElementById('view-profile');
    var editSection = document.getElementById('edit-profile');
    viewSection.classList.toggle('hidden');
    editSection.classList.toggle('hidden');
}

function formatTimestamp(utcTimestamp) {
    if (!utcTimestamp) {
        return 'N/A';
    }

    try {
        // Remove the timezone offset if it exists
        const cleanTimestamp = utcTimestamp.replace(/([+-]\d{2}:\d{2}|Z)$/, '');
        const date = new Date(cleanTimestamp + 'Z');

        if (isNaN(date.getTime())) {
            console.log('Invalid date created for:', utcTimestamp);
            return 'Invalid Date';
        }

        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
        };

        return date.toLocaleString(undefined, options);
    } catch (error) {
        console.error('Error formatting date:', error);
        return 'Error formatting date';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    async function fetchAndDisplayReviews(serviceId, page = 1) {
        try {
            const response = await fetch(`/home/get_reviews/${serviceId}/?page=${page}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch reviews. Status: ${response.status}`);
            }

            const {reviews, has_next, has_previous, current_page} = await response.json();

            const reviewsContainer = document.getElementById('reviewsContainer');
            reviewsContainer.innerHTML = '';

            if (reviews.length === 0) {
                reviewsContainer.innerHTML = '<p class="text-sm text-gray-500">No reviews yet.</p>';
                return;
            }

            reviews.forEach(review => {
                const reviewDiv = document.createElement('div');
                reviewDiv.classList.add('bg-white', 'rounded-lg', 'shadow', 'p-2', 'mb-2');

                const rating = parseFloat(review.RatingStars).toFixed(2);

                const ratingElement = document.createElement('p');
                ratingElement.classList.add('text-yellow-400', 'font-semibold');
                ratingElement.textContent = `${rating} ★`;
                reviewDiv.appendChild(ratingElement);

                const reviewText = document.createElement('p');
                reviewText.classList.add('text-sm');
                reviewText.textContent = review.RatingMessage;
                reviewDiv.appendChild(reviewText);

                const timestamp = formatTimestamp(review.Timestamp);
                const meta = document.createElement('p');
                meta.classList.add('text-xs', 'text-gray-500');
                meta.textContent = `By ${review.Username} on ${timestamp}`;
                reviewDiv.appendChild(meta);

                if (review.ResponseText) {
                    const responseDiv = document.createElement('div');
                    responseDiv.classList.add('mt-3', 'p-3', 'bg-blue-50', 'rounded');

                    const responseHeader = document.createElement('p');
                    responseHeader.classList.add('font-semibold', 'text-sm', 'text-blue-600');
                    responseHeader.textContent = "Provider Response:";
                    responseDiv.appendChild(responseHeader);

                    const responseText = document.createElement('p');
                    responseText.classList.add('text-sm');
                    responseText.textContent = review.ResponseText;
                    responseDiv.appendChild(responseText);

                    const respondedAt = formatTimestamp(review.RespondedAt);
                    console.log(review.RespondedAt)
                    const responseMeta = document.createElement('p');
                    responseMeta.classList.add('text-xs', 'text-gray-500');
                    responseMeta.textContent = `Responded on ${respondedAt}`;
                    responseDiv.appendChild(responseMeta);

                    reviewDiv.appendChild(responseDiv);
                }

                reviewsContainer.appendChild(reviewDiv);
            });

            // Pagination controls
            const paginationDiv = document.createElement('div');
            paginationDiv.classList.add('flex', 'justify-between', 'mt-4');

            if (has_previous) {
                const prevButton = document.createElement('button');
                prevButton.classList.add('bg-blue-500', 'text-white', 'px-4', 'py-2', 'rounded');
                prevButton.textContent = 'Previous';
                prevButton.addEventListener('click', () => fetchAndDisplayReviews(serviceId, current_page - 1));
                paginationDiv.appendChild(prevButton);
            }

            if (has_next) {
                const nextButton = document.createElement('button');
                nextButton.classList.add('bg-blue-500', 'text-white', 'px-4', 'py-2', 'rounded');
                nextButton.textContent = 'Next';
                nextButton.addEventListener('click', () => fetchAndDisplayReviews(serviceId, current_page + 1));
                paginationDiv.appendChild(nextButton);
            }

            reviewsContainer.appendChild(paginationDiv);
        } catch (error) {
            console.error('Error fetching reviews:', error);
            alert('Failed to load reviews. Please try again.');
        }
    }

    let map = null;
    let marker = null;

    function showServiceDetails(serviceId) {
        const service = itemsData.find(item => item.Id === serviceId);
        if (!service) {
            console.error(`Service with ID ${serviceId} not found.`);
            return;
        }

        document.getElementById('serviceName').textContent = service.Name || 'No Name';
        document.getElementById('serviceAddress').textContent = service.Address || 'N/A';
        document.getElementById('serviceType').textContent = service.Category || 'Unknown';
        document.getElementById('serviceRating').textContent = service.Ratings && service.Ratings !== 0 ? parseFloat(service.Ratings).toFixed(2) : 'N/A';

        const getDirectionsBtn = document.getElementById('getDirections');
        if (service.MapLink) {
            getDirectionsBtn.href = service.MapLink;
            getDirectionsBtn.style.display = 'inline-block';
        } else {
            getDirectionsBtn.href = '#';
            getDirectionsBtn.style.display = 'none';
        }

        // Initialize or update map
        if (!map) {
            map = L.map('serviceMap').setView([service.Lat, service.Log], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            marker = L.marker([service.Lat, service.Log]).addTo(map);
        } else {
            map.setView([service.Lat, service.Log], 15);
            marker.setLatLng([service.Lat, service.Log]);
        }

        const descriptionElement = document.getElementById('serviceDescription');
        descriptionElement.innerHTML = '';
        if (service.Description && typeof service.Description === 'object') {
            let hasDescription = false;
            const table = document.createElement('table');
            for (const [key, value] of Object.entries(service.Description)) {
                if (value !== null && value !== '') {
                    hasDescription = true;
                    const tr = document.createElement('tr');

                    const th = document.createElement('th');
                    th.textContent = `${key.replace(/_/g, ' ')}:`;

                    const td = document.createElement('td');
                    td.innerHTML = value.replace(/\n/g, '<br>');

                    tr.appendChild(th);
                    tr.appendChild(td);
                    table.appendChild(tr);
                }
            }

            if (hasDescription) {
                descriptionElement.appendChild(table);
            } else {
                descriptionElement.textContent = 'No description available.';
            }
        } else {
            descriptionElement.textContent = 'No description available.';
        }

        // Show the modal
        const serviceDetailsDiv = document.getElementById('serviceDetails');
        if (serviceDetailsDiv) {
            serviceDetailsDiv.classList.remove('hidden');
            serviceDetailsDiv.classList.add('block');
            // Invalidate map size after modal is shown
            setTimeout(() => {
                map.invalidateSize();
            }, 100);
        }

        // Fetch and display reviews
        fetchAndDisplayReviews(service.Id, 1);
    }

    // Expose the function globally
    window.showServiceDetails = showServiceDetails;

    // Close modal event listener
    document.getElementById('closeDetails').addEventListener('click', () => {
        const serviceDetailsDiv = document.getElementById('serviceDetails');
        if (serviceDetailsDiv) {
            serviceDetailsDiv.classList.add('hidden');
            serviceDetailsDiv.classList.remove('block');
        }
    });

    // Submit review event listener
    document.getElementById('submitReview').addEventListener('click', async () => {
        const rating = document.getElementById('reviewRating').value;
        const message = document.getElementById('reviewText').value;
        const serviceId = itemsData.find(item => item.Name === document.getElementById('serviceName').textContent).Id;

        if (rating === "" || message.trim() === "") {
            alert("Please provide both a rating and a message.");
            return;
        }

        const reviewData = {
            service_id: serviceId,
            rating: parseInt(rating),
            message: message,
        };

        try {
            const response = await fetch('/home/submit_review/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(reviewData),
            });

            if (response.ok) {
                const result = await response.json();
                fetchAndDisplayReviews(serviceId, 1);
                document.getElementById('reviewRating').value = '';
                document.getElementById('reviewText').value = '';
            } else {
                const error = await response.json();
                alert(error.error || "Failed to submit review.");
            }
        } catch (error) {
            console.error('Error submitting review:', error);
            alert("An error occurred. Please try again.");
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners for bookmark checkboxes
    const bookmarkCheckboxes = document.querySelectorAll('.bookmark-checkbox');
    bookmarkCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async function () {
            const serviceId = this.dataset.serviceId;
            const action = this.checked ? 'add' : 'remove';

            try {
                const response = await fetch('/home/toggle_bookmark/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({
                        'service_id': serviceId,
                        'action': action,
                    }),
                });

                const data = await response.json();
                if (!data.success) {
                    // Revert the checkbox state if the request failed
                    this.checked = !this.checked;
                    alert(data.error || 'Failed to toggle bookmark.');
                } else {
                    // If removing bookmark, remove the service card from the UI
                    if (action === 'remove') {
                        const serviceCard = this.closest('.bg-gray-50');
                        serviceCard.remove();

                        // Check if there are any remaining bookmarks
                        const remainingBookmarks = document.querySelectorAll('.bookmark-checkbox');
                        if (remainingBookmarks.length === 0) {
                            const bookmarksContainer = document.querySelector('.grid.gap-4');
                            const noBookmarksMessage = document.createElement('p');
                            noBookmarksMessage.className = 'text-gray-500';
                            noBookmarksMessage.textContent = 'No bookmarks yet.';
                            bookmarksContainer.innerHTML = '';
                            bookmarksContainer.appendChild(noBookmarksMessage);
                        }
                    }
                }
            } catch (error) {
                console.error('Error toggling bookmark:', error);
                this.checked = !this.checked;
                alert('An error occurred. Please try again.');
            }
        });
    });
});

// Function to get CSRF token from cookies
function getCsrfToken() {
    const cookies = document.cookie.split('; ');
    for (const cookie of cookies) {
        const [name, value] = cookie.split('=');
        if (name === 'csrftoken') return value;
    }
    return '';
}
