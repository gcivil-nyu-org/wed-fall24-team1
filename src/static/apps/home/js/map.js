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
function showServiceDetails(index) {
    const service = itemsData[index];
    if (!service) {
        console.error(`Service with index ${index} not found.`);
        return;
    }

    document.getElementById('serviceName').textContent = service.Name || 'No Name';
    document.getElementById('serviceAddress').textContent = service.Address || 'N/A';
    document.getElementById('serviceType').textContent = service.Category || 'Unknown';
    document.getElementById('serviceRating').textContent = service.Ratings || 'N/A';
    document.getElementById('serviceDistance').textContent = service.Distance ? service.Distance + ' miles' : 'N/A';
    document.getElementById('serviceDescription').textContent = service.Description || 'No description available.';

    // Set the Get Directions button link
    const getDirectionsBtn = document.getElementById('getDirections');
    if (service.MapLink) {
        getDirectionsBtn.href = service.MapLink;
        getDirectionsBtn.style.display = 'inline-block'; // Ensure the button is visible
    } else {
        getDirectionsBtn.href = '#';
        getDirectionsBtn.style.display = 'none'; // Hide the button if no MapLink
    }

    // Populate reviews
    const reviewsContainer = document.getElementById('reviewsContainer');
    if (reviewsContainer) {
        reviewsContainer.innerHTML = ''; // Clear existing reviews
        if (service.Reviews && service.Reviews.length > 0) {
            service.Reviews.forEach(review => {
                const reviewDiv = document.createElement('div');
                reviewDiv.classList.add('bg-white', 'rounded-lg', 'shadow', 'p-2', 'mb-2');

                // Review Content
                const contentDiv = document.createElement('div');
                contentDiv.classList.add('flex', 'justify-between', 'items-start');

                // Review Text and Rating
                const textDiv = document.createElement('div');
                const starsDiv = document.createElement('div');
                starsDiv.classList.add('flex', 'items-center');

                for(let i=0; i < review.rating; i++) {
                    const star = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                    star.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                    star.setAttribute("class", "h-4 w-4 text-yellow-400");
                    star.setAttribute("viewBox", "0 0 20 20");
                    star.setAttribute("fill", "currentColor");
                    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                    path.setAttribute("d", "M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z");
                    star.appendChild(path);
                    starsDiv.appendChild(star);
                }

                const reviewText = document.createElement('p');
                reviewText.classList.add('text-sm');
                reviewText.textContent = review.text || 'No review text provided.';

                textDiv.appendChild(starsDiv);
                textDiv.appendChild(reviewText);

                // Review Meta
                const metaDiv = document.createElement('div');
                metaDiv.classList.add('text-right', 'text-sm', 'text-gray-500');

                const dateDiv = document.createElement('div');
                dateDiv.classList.add('flex', 'items-center');
                const dateIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                dateIcon.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                dateIcon.setAttribute("class", "h-4 w-4 mr-1");
                dateIcon.setAttribute("fill", "none");
                dateIcon.setAttribute("viewBox", "0 0 24 24");
                dateIcon.setAttribute("stroke", "currentColor");
                const datePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
                datePath.setAttribute("stroke-linecap", "round");
                datePath.setAttribute("stroke-linejoin", "round");
                datePath.setAttribute("stroke-width", "2");
                datePath.setAttribute("d", "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z");
                dateIcon.appendChild(datePath);
                dateDiv.appendChild(dateIcon);
                dateDiv.appendChild(document.createTextNode(review.date || 'N/A'));

                const likesDiv = document.createElement('div');
                likesDiv.classList.add('flex', 'items-center');
                const likeIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                likeIcon.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                likeIcon.setAttribute("class", "h-4 w-4 mr-1");
                likeIcon.setAttribute("fill", "none");
                likeIcon.setAttribute("viewBox", "0 0 24 24");
                likeIcon.setAttribute("stroke", "currentColor");
                const likePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
                likePath.setAttribute("stroke-linecap", "round");
                likePath.setAttribute("stroke-linejoin", "round");
                likePath.setAttribute("stroke-width", "2");
                likePath.setAttribute("d", "M9 5l7 7-7 7");
                likeIcon.appendChild(likePath);
                likesDiv.appendChild(likeIcon);
                likesDiv.appendChild(document.createTextNode(review.likes || '0'));

                metaDiv.appendChild(dateDiv);
                metaDiv.appendChild(likesDiv);

                contentDiv.appendChild(textDiv);
                contentDiv.appendChild(metaDiv);

                reviewDiv.appendChild(contentDiv);
                reviewsContainer.appendChild(reviewDiv);
            });
        } else {
            reviewsContainer.innerHTML = '<p class="text-sm text-gray-500">No reviews yet.</p>';
        }
    }

    // Show the detailed view by removing 'hidden' class
    const serviceDetailsDiv = document.getElementById('serviceDetails');
    if (serviceDetailsDiv) {
        serviceDetailsDiv.classList.remove('hidden');
        serviceDetailsDiv.classList.add('block'); // Optionally add 'block' for better Tailwind handling
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
