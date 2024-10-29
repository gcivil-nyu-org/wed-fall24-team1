// Initialize the map
let BaseLat = 40.7128; //40.7128
let BaseLong = -74.0060; //-74.0060

const map = L.map('map').setView([BaseLat, BaseLong], 12);
let currentLocationMarker = null;  // Declare a global variable to hold the reference to the current location marker

let userLat = localStorage.getItem('userLat');
let userLng = localStorage.getItem('userLong');

const userLocationIcon = L.icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(map);

if(userLat != null && userLng != null) {
    currentLocationMarker = L.marker([userLat, userLng], { icon: userLocationIcon }).addTo(map);
}

function setUserLocation(lat, lon) {
    if (currentLocationMarker) {
        map.removeLayer(currentLocationMarker);  // Remove existing marker if any
    }
    currentLocationMarker = L.marker([lat, lon], { icon: userLocationIcon }).addTo(map);
    map.setView([lat, lon], 12);  // Center the map on the user's location

    // Store the user's coordinates in localStorage
    localStorage.setItem('userLat', lat);
    localStorage.setItem('userLong', lon);

    document.getElementById('user-lat').value = lat;
    document.getElementById('user-lon').value = lon;
}

// Initialize markers array
const markers = [];

// Add markers from itemsData
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
    // If no markers, default to BaseLat and BaseLong
    map.setView([BaseLat, BaseLong], 10);
}

// Update radius value display (if applicable)
// Update radius value display and adjust map view based on the radius input
const radiusInput = document.getElementById('radius');
const radiusValue = document.getElementById('radiusValue');
if (radiusInput && radiusValue) {
    radiusInput.addEventListener('input', function () {
        const radiusInMiles = this.value;
        radiusValue.textContent = radiusInMiles + ' miles';

        // Calculate the zoom level based on the radius in miles (simple approximation)
        const zoomLevel = getZoomLevelForRadius(radiusInMiles);

        // Update the map view with the new radius, centered on the current user's location or base location
        if (userLat && userLong) {
            map.setView([userLat, userLong], zoomLevel);
        } else {
            map.setView([BaseLat, BaseLong], zoomLevel);
        }
    });
}

// Function to approximate the zoom level based on the radius in miles
function getZoomLevelForRadius(radiusInMiles) {
    if (radiusInMiles <= 1) {
        return 13;  // Zoom in for a small area (city blocks)
    } else if (radiusInMiles <= 5) {
        return 13;  // Zoom for neighborhoods
    } else if (radiusInMiles <= 10) {
        return 12;  // Zoom for citywide view
    } else if (radiusInMiles <= 20) {
        return 11;  // Zoom for larger areas
    } else if (radiusInMiles <= 50) {
        return 10;  // Zoom for broader area
    } else {
        return 8;   // Zoom out for regional view
    }
}

async function showServiceDetails(index) {
    const service = itemsData[index];
    if (!service) {
        console.error(`Service with index ${index} not found.`);
        return;
    }

    // Populate basic service details
    document.getElementById('serviceId').textContent = service.Id || 'No ID';
    document.getElementById('serviceName').textContent = service.Name || 'No Name';
    document.getElementById('serviceAddress').textContent = service.Address || 'N/A';
    document.getElementById('serviceType').textContent = service.Category || 'Unknown';
    document.getElementById('serviceRating').textContent = service.Ratings && service.Ratings !== 0 ? parseFloat(service.Ratings).toFixed(2) : 'N/A';
    document.getElementById('serviceDistance').textContent = service.Distance ? service.Distance + ' miles' : 'N/A';
    
    // Clear previous descriptions
    const descriptionElement = document.getElementById('serviceDescription');
    descriptionElement.innerHTML = '';  // Clear previous content

    const heading = document.createElement('h3');
    heading.textContent = 'Additional Descriptive Details:';
    heading.style.marginBottom = '10px'; // Add some space below the heading
    heading.style.fontSize = '1.1em'; // Adjust font size as needed
    heading.style.fontWeight = 'bold'; // Make the heading bold
    descriptionElement.appendChild(heading);

    // Check if Description exists and is an object
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
                td.innerHTML = value.replace(/\n/g, '<br>'); // Replace \n with <br>

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

function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                // If the location is successfully retrieved
                userLat = position.coords.latitude;
                userLng = position.coords.longitude;

                // Update BaseLat and BaseLong with user's current location
                BaseLat = userLat;
                BaseLong = userLng;

                setUserLocation(BaseLat, BaseLong);
                console.log(`User's location: ${BaseLat}, ${BaseLong}`);
            },
            error => {
                // Handle geolocation errors
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        alert("Location access has been denied. Please enable location permissions in your browser settings.");
                        break;
                    case error.POSITION_UNAVAILABLE:
                        alert("Location information is unavailable. Please check your device's location settings.");
                        break;
                    case error.TIMEOUT:
                        alert("The request to get your location timed out. Please try again.");
                        break;
                    case error.UNKNOWN_ERROR:
                        alert("An unknown error occurred while retrieving your location.");
                        break;
                }
                console.error("Geolocation error:", error);
            }
        );
    } else {
        // If the browser doesn't support Geolocation API
        alert("Geolocation is not supported by this browser.");
    }
}
