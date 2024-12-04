function toggleEdit() {
    var viewSection = document.getElementById('view-profile');
    var editSection = document.getElementById('edit-profile');
    viewSection.classList.toggle('hidden');
    editSection.classList.toggle('hidden');
}

let reviewToDelete = null;

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
    const tabs = ['posts', 'bookmarks', 'reviews'];
    let activeTab = 'posts';

    function switchTab(tabName) {
        // Hide all tab contents
        tabs.forEach(tab => {
            const tabContent = document.getElementById(`${tab}-tab`);
            if (tabContent) {
                tabContent.classList.add('hidden');
            }
        });

        // Show selected tab content
        const selectedTab = document.getElementById(`${tabName}-tab`);
        if (selectedTab) {
            selectedTab.classList.remove('hidden');
        }

        // Update tab button styles
        tabs.forEach(tab => {
            const button = document.getElementById(`${tab}-tab-btn`);
            if (button) {
                if (tab === tabName) {
                    button.classList.remove('border-transparent', 'text-gray-500');
                    button.classList.add('border-blue-500', 'text-blue-600');
                } else {
                    button.classList.add('border-transparent', 'text-gray-500');
                    button.classList.remove('border-blue-500', 'text-blue-600');
                }
            }
        });

        activeTab = tabName;
    }

    // Add click listeners to tab buttons
    tabs.forEach(tab => {
        const button = document.getElementById(`${tab}-tab-btn`);
        if (button) {
            button.addEventListener('click', () => switchTab(tab));
        }
    });

    // Initialize with bookmarks tab
    switchTab('posts');

    let map = null;
    let marker = null;

    function showServiceDetails(serviceId) {
        const service = itemsData.find(item => item.Id === serviceId);
        if (!service) {
            console.error(`Service with ID ${serviceId} not found.`);
            return;
        }
        document.getElementById('serviceName').textContent = service.Name || 'No Name';

        // Handle announcement display
        const announcementDiv = document.getElementById('serviceAnnouncement');
        const announcementText = announcementDiv.querySelector('p');
        if (service.Announcement && service.Announcement.trim()) {
            announcementText.textContent = service.Announcement;
            announcementDiv.classList.remove('hidden');
        } else {
            announcementDiv.classList.add('hidden');
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
            const dl = document.createElement('dl');
            dl.className = 'mt-2 space-y-1';

            for (const [key, value] of Object.entries(service.Description)) {
                if (value !== null && value !== '') {
                    hasDescription = true;
                    const div = document.createElement('div');
                    div.className = 'flex';

                    const dt = document.createElement('dt');
                    dt.className = 'text-sm font-medium text-gray-400 w-1/3';
                    dt.textContent = `${key.replace(/_/g, ' ')}:`;

                    const dd = document.createElement('dd');
                    dd.className = 'text-sm text-gray-300 ml-2';
                    dd.innerHTML = value.replace(/\n/g, '<br>');

                    div.appendChild(dt);
                    div.appendChild(dd);
                    dl.appendChild(div);
                }
            }

            if (hasDescription) {
                descriptionElement.appendChild(dl);
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

});

document.addEventListener('DOMContentLoaded', () => {

    function updateBookmarkCounters() {
        const remainingBookmarks = document.querySelectorAll('.bookmark-checkbox').length;

        // Update tab counter
        const tabCounter = document.querySelector('#bookmarks-tab-btn .ml-2');
        if (tabCounter) {
            tabCounter.textContent = remainingBookmarks;
        }

        // Update header counter
        const headerCounter = document.querySelector('#bookmarks-tab .bg-blue-100');
        if (headerCounter) {
            headerCounter.textContent = `${remainingBookmarks} service${remainingBookmarks !== 1 ? 's' : ''}`;
        }
    }

    const modal = document.getElementById('deleteConfirmModal');
    const confirmBtn = document.getElementById('confirmDelete');
    const cancelBtn = document.getElementById('cancelDelete');

    function closeModal() {
        const modal = document.getElementById('deleteConfirmModal');
        modal.classList.add('hidden');
        reviewToDelete = null;
    }

    confirmBtn.addEventListener('click', async () => {
        if (!reviewToDelete) return;

        try {
            const response = await fetch(`/home/delete_review/${reviewToDelete.ReviewId}/`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({
                    username: reviewToDelete.Username,
                }),
            });

            const data = await response.json();
            if (data.success) {
                const reviewElement = document.querySelector(`[data-review-id="${reviewToDelete.ReviewId}"]`);
                if (reviewElement) {
                    reviewElement.remove();
                    updateReviewCounters();
                }
            } else {
                alert(data.error || "Failed to delete review.");
            }
        } catch (error) {
            console.error("Error deleting review:", error);
            alert("An error occurred. Please try again.");
        } finally {
            closeModal();
        }
    });

    cancelBtn.addEventListener('click', closeModal);

    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Close modal on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });
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
                    this.checked = !this.checked;
                    alert(data.error || 'Failed to toggle bookmark.');
                } else {
                    if (action === 'remove') {
                        const serviceCard = this.closest('.bg-gray-700');
                        serviceCard.remove();

                        // Update counters after removing bookmark
                        updateBookmarkCounters();

                        const remainingBookmarks = document.querySelectorAll('.bookmark-checkbox');
                        if (remainingBookmarks.length === 0) {
                            const bookmarksContainer = document.querySelector('#bookmarks-tab .grid.gap-4');
                            if (bookmarksContainer) {
                                const noBookmarksMessage = document.createElement('p');
                                noBookmarksMessage.className = 'text-gray-500';
                                noBookmarksMessage.textContent = 'No bookmarks yet.';
                                bookmarksContainer.innerHTML = '';
                                bookmarksContainer.appendChild(noBookmarksMessage);
                            }
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


function updateReviewCounters() {
    const remainingReviews = document.querySelectorAll('#reviews-tab .grid > div').length;

    // Update tab counter
    const tabCounter = document.querySelector('#reviews-tab-btn .ml-2');
    if (tabCounter) {
        tabCounter.textContent = remainingReviews;
    }

    // Update header counter
    const headerCounter = document.querySelector('#reviews-tab .bg-blue-100');
    if (headerCounter) {
        headerCounter.textContent = `${remainingReviews} review${remainingReviews !== 1 ? 's' : ''}`;
    }

    // Show "No reviews" message if needed
    if (remainingReviews === 0) {
        const reviewsContainer = document.querySelector('#reviews-tab .grid');
        if (reviewsContainer) {
            reviewsContainer.innerHTML = '<p class="text-gray-500">No reviews yet.</p>';
        }
    }
}


function handleDeleteReview(review) {
    reviewToDelete = review;
    const modal = document.getElementById('deleteConfirmModal');
    modal.classList.remove('hidden');
}

// Function to get CSRF token from cookies
function getCsrfToken() {
    const cookies = document.cookie.split('; ');
    for (const cookie of cookies) {
        const [name, value] = cookie.split('=');
        if (name === 'csrftoken') return value;
    }
    return '';
}
