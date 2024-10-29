// map.js

// Global variables
let map;
let currentLocationMarker = null;
let userLat = null;
let userLng = null;
let serviceMarkers = []; // Array to hold service markers

const userLocationIcon = L.icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Initialize the map when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Set default coordinates (e.g., New York City)
    const defaultLat = 40.7128;
    const defaultLng = -74.0060;

    // Initialize the map
    map = L.map('map').setView([defaultLat, defaultLng], 12);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Check if user location is stored in localStorage
    userLat = localStorage.getItem('userLat');
    userLng = localStorage.getItem('userLng');
    const savedAddress = localStorage.getItem('userAddress'); // Fetch saved address

    if (userLat && userLng) {
        // If user location is stored, update the marker and map view
        setUserLocation(parseFloat(userLat), parseFloat(userLng), false);
    } else {
        // If not, set the default marker
        setUserLocation(defaultLat, defaultLng, false);
    }

    // Check if the address field has a saved value, and populate the input
    if (savedAddress) {
        document.getElementById('location').value = savedAddress;
    }

    const radiusInput = document.getElementById('radius');
    const radiusValue = document.getElementById('radiusValue');
    if (radiusInput && radiusValue) {
        // Set the initial radius value display
        radiusValue.textContent = radiusInput.value;

        radiusInput.addEventListener('input', function () {
            radiusValue.textContent = this.value;
            // Additional code to update map based on radius change
            initializeServiceMarkers(); // Update markers based on radius change
        });
    }

    // Event listener for manual address input (on 'Enter' key)
    const locationInput = document.getElementById('location');
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (locationInput && applyFiltersBtn) {
        locationInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                const address = this.value;
                geocodeAddress(address).then(function() {
                    // After geocoding and updating hidden inputs, simulate click on "Apply Filters" button
                    applyFiltersBtn.click();
                }).catch(function(error) {
                    alert('Address not found. Please try a different address.');
                });
            }
        });
    } else {
        console.error('Element with ID "location" or "apply-filters" not found.');
    }

    // Clear Filters button event listener
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            // Reset form fields
            document.getElementById('search').value = '';
            document.getElementById('location').value = '';
            document.getElementById('type').selectedIndex = 0;
            document.getElementById('radius').value = 5; // Default radius value
            radiusValue.textContent = '5';

            // Reset hidden inputs
            document.getElementById('user-lat').value = '';
            document.getElementById('user-lon').value = '';

            // Clear localStorage values
            localStorage.removeItem('userLat');
            localStorage.removeItem('userLng');
            localStorage.removeItem('userAddress');

            // Reset global variables
            userLat = defaultLat;
            userLng = defaultLng;

            // Reset map to default location
            setUserLocation(defaultLat, defaultLng, false);

            // Remove existing service markers
            if (serviceMarkers.length > 0) {
                serviceMarkers.forEach(marker => {
                    map.removeLayer(marker);
                });
                serviceMarkers = [];
            }

            // Re-initialize service markers
            initializeServiceMarkers();
        });
    }
});

// Function to set user's location and update the marker
function setUserLocation(lat, lon, shouldReverseGeocode = true) {
    if (currentLocationMarker) {
        map.removeLayer(currentLocationMarker);
    }
    currentLocationMarker = L.marker([lat, lon], { icon: userLocationIcon }).addTo(map);
    map.setView([lat, lon], 12);

    // Update global variables
    userLat = lat;
    userLng = lon;

    // Store the user's coordinates in localStorage
    localStorage.setItem('userLat', lat);
    localStorage.setItem('userLng', lon);

    document.getElementById('user-lat').value = lat;
    document.getElementById('user-lon').value = lon;

    // Reverse geocode to update the address in the location input field
    if (shouldReverseGeocode) {
        reverseGeocode(lat, lon);
    }

    // After updating the user location, re-initialize the service markers
    initializeServiceMarkers();
}

// Function to reverse geocode coordinates to an address
function reverseGeocode(lat, lon) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data && data.display_name) {
                const address = data.display_name;
                document.getElementById('location').value = address;
                // Save the address to localStorage
                localStorage.setItem('userAddress', address);
            }
        })
        .catch(error => {
            console.error('Error during reverse geocoding:', error);
        });
}

// Function to geocode address to coordinates
function geocodeAddress(address) {
    const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&q=${encodeURIComponent(address)}`;

    return fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);

                // Update userLat and userLng
                userLat = lat;
                userLng = lon;

                document.getElementById('user-lat').value = lat;
                document.getElementById('user-lon').value = lon;

                // Update the map and marker
                setUserLocation(lat, lon, false);

                // Save the address to localStorage
                localStorage.setItem('userAddress', address);

                return Promise.resolve();
            } else {
                return Promise.reject('Address not found');
            }
        });
}

// Function to initialize service markers based on the updated location
function initializeServiceMarkers() {
    // Remove existing service markers
    if (serviceMarkers.length > 0) {
        serviceMarkers.forEach(marker => {
            map.removeLayer(marker);
        });
        serviceMarkers = [];
    }

    // Make sure itemsData is defined and accessible
    // itemsData should be an array of service objects with properties: Lat, Log, Name, Address, Ratings

    if (!itemsData || !Array.isArray(itemsData)) {
        console.error('itemsData is not defined or is not an array.');
        return;
    }

    // Calculate distance to filter nearby services (e.g., within the specified radius)
    const radiusInMiles = document.getElementById('radius').value || 5;

    // Helper function to calculate distance between two lat/lon points
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 3958.8; // Earth's radius in miles
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a =
            0.5 - Math.cos(dLat)/2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            (1 - Math.cos(dLon))/2;

        return R * 2 * Math.asin(Math.sqrt(a));
    }

    // Filter services within the specified radius
    const nearbyServices = itemsData.filter((item) => {
        if (item.Lat && item.Log) {
            const distance = calculateDistance(userLat, userLng, item.Lat, item.Log);
            return distance <= radiusInMiles;
        }
        return false;
    });

    // Add markers for nearby services
    nearbyServices.forEach((item, index) => {
        const marker = L.marker([item.Lat, item.Log])
            .addTo(map)
            .bindPopup(`<b>${item.Name}</b><br>${item.Address}<br>Rating: ${item.Ratings}`)
            .on('click', () => {
                showServiceDetails(index); // Use index as identifier
            });
        serviceMarkers.push(marker);
    });

    // Adjust map view to include all markers
    const allMarkers = [...serviceMarkers, currentLocationMarker];
    if (allMarkers.length > 0) {
        const group = L.featureGroup(allMarkers);
        map.fitBounds(group.getBounds());
    } else {
        map.setView([userLat, userLng], 12);
    }
}

// Function to get the user's current location
function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                // Update userLat and userLng
                userLat = lat;
                userLng = lon;

                // Update the map and marker
                setUserLocation(lat, lon, true);
                console.log(`User's location: ${lat}, ${lon}`);
            },
            error => {
                handleLocationError(error);
            }
        );
    } else {
        // If the browser doesn't support Geolocation API
        alert("Geolocation is not supported by this browser.");
        setFallbackLocation();
    }
}

// Function to handle geolocation errors
function handleLocationError(error) {
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
    setFallbackLocation();
}

// Function to set a fallback location
function setFallbackLocation() {
    // Default to New York City coordinates
    const defaultLat = 40.7128;
    const defaultLng = -74.0060;
    setUserLocation(defaultLat, defaultLng, false);
    document.getElementById('location').value = 'New York, NY';
}

// Function to show service details (Assuming you have this function)
function showServiceDetails(index) {
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

    // Assuming you have a function to fetch and display reviews
    fetchAndDisplayReviews(service.Id, 1);

    const serviceDetailsDiv = document.getElementById('serviceDetails');
    if (serviceDetailsDiv) {
        serviceDetailsDiv.classList.remove('hidden');
        serviceDetailsDiv.classList.add('block');
    }
}

// Event listener for the radius input change
const radiusInput = document.getElementById('radius');
const radiusValue = document.getElementById('radiusValue');
if (radiusInput && radiusValue) {
    radiusInput.addEventListener('input', function () {
        radiusValue.textContent = this.value;
        initializeServiceMarkers();
    });
}
