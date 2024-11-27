// map.js

// Global variables
let map;
let currentLocationMarker = null;
window.userLat = null;
window.userLng = null;
let serviceMarkers = {}; // Object to hold service markers by Id
let selectedMarker = null; // Variable to track the selected marker
let selectedSidebarButton = null; // Variable to track the selected sidebar button

// Define User Location Icon
const userLocationIcon = L.icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Define Default and Selected Icons for Services
const defaultIcon = L.icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const selectedIcon = L.icon({
    iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

// Preprocess itemsData to ensure Ratings are numbers or NaN
itemsData.forEach(item => {
    const rating = parseFloat(item.Ratings);
    item.Ratings = isNaN(rating) ? NaN : rating;
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

    // Retrieve and set the selected filter from localStorage
    const savedFilter = sessionStorage.getItem('selectedFilter') || 'distance';
    const filterSelect = document.getElementById('filterSelect');
    if (filterSelect) {
        filterSelect.value = savedFilter;
    }

    // Check if user location is stored in localStorage
    window.userLat = sessionStorage.getItem('userLat');
    window.userLng = sessionStorage.getItem('userLng');
    const savedAddress = sessionStorage.getItem('userAddress'); // Fetch saved address

    if (window.userLat && window.userLng) {
        // If user location is stored, update the marker and map view
        setUserLocation(parseFloat(window.userLat), parseFloat(window.userLng), false);
    } else {
        // If not, set the default marker
        setUserLocation(defaultLat, defaultLng, false);
    }

    // Check if the address field has a saved value, and populate the input
    if (savedAddress) {
        const locationInput = document.getElementById('location');
        if (locationInput) {
            locationInput.value = savedAddress;
        }
    }

    const radiusInput = document.getElementById('radius');
    const radiusValue = document.getElementById('radiusValue');
    if (radiusInput && radiusValue) {
        // Set the initial radius value display
        radiusValue.textContent = radiusInput.value;

        radiusInput.addEventListener('input', function () {
            radiusValue.textContent = this.value;
            // Update markers and service list based on the new radius
            initializeServiceMarkers();
            updateServiceList();
        });
    }

    const locationInput = document.getElementById('location');
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (locationInput && applyFiltersBtn) {
        locationInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                const address = this.value.trim();
                if (address !== '') {
                    geocodeAddress(address).then(function() {
                        // After geocoding and updating hidden inputs, simulate click on "Apply Filters" button
                        applyFiltersBtn.click();
                    }).catch(function(error) {
                        alert('Address not found. Please try a different address.');
                    });
                } else {
                    alert('Please enter an address.');
                }
            }
        });
    } else {
        console.error('Element with ID "location" or "apply-filters" not found.');
    }

    // Add event listener to "Apply Filters" button
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function(event) {
            // Prevent the default form submission
            event.preventDefault();

            const locationInput = document.getElementById('location');
            const address = locationInput ? locationInput.value.trim() : '';
            const userLatInput = document.getElementById('user-lat');
            const userLonInput = document.getElementById('user-lon');
            const userLatValue = userLatInput ? userLatInput.value : '';
            const userLonValue = userLonInput ? userLonInput.value : '';

            if (address !== '') {
                // Location input has a value, geocode the address
                geocodeAddress(address).then(function() {
                    // After geocoding and updating hidden inputs, submit the form
                    applyFiltersBtn.closest('form').submit();
                }).catch(function(error) {
                    alert('Address not found. Please try a different address.');
                });
            } else {
                // No location entered, you can decide to use current location or alert the user
                alert('Please enter a location or use the current location button.');
            }
        });
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
            if (radiusValue) {
                radiusValue.textContent = '5';
            }

            // Reset hidden inputs
            document.getElementById('user-lat').value = '';
            document.getElementById('user-lon').value = '';

            // Clear localStorage values
            sessionStorage.removeItem('userLat');
            sessionStorage.removeItem('userLng');
            sessionStorage.removeItem('userAddress');
            sessionStorage.removeItem('selectedFilter'); // Clear selected filter

            // Reset global variables
            window.userLat = defaultLat;
            window.userLng = defaultLng;

            // Reset map to default location
            setUserLocation(defaultLat, defaultLng, false);

            // Remove existing service markers
            for (let id in serviceMarkers) {
                map.removeLayer(serviceMarkers[id]);
            }
            serviceMarkers = {};

            // Reset filter select to default
            if (filterSelect) {
                filterSelect.value = 'distance';
            }

            // Reload the page to the default URL (without any query parameters)
            window.location.href = window.location.pathname;
        });
    }

    // Add event listener to the filter select dropdown
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            const selectedFilter = this.value;
            // Save the selected filter to localStorage
            sessionStorage.setItem('selectedFilter', selectedFilter);
            // Re-initialize markers and service list based on the new filter
            initializeServiceMarkers();
            updateServiceList();
        });
    }

    // Initialize service markers and service list on page load
    initializeServiceMarkers();
    updateServiceList();
});

// Function to set user's location and update the marker
function setUserLocation(lat, lon, shouldReverseGeocode = true) {
    if (currentLocationMarker) {
        map.removeLayer(currentLocationMarker);
    }
    currentLocationMarker = L.marker([lat, lon], {
        icon: userLocationIcon,
        zIndexOffset: 1000
    }).addTo(map);
    map.setView([lat, lon], 12);

    // Update global variables
    window.userLat = lat;
    window.userLng = lon;

    // Store the user's coordinates in sessionStorage
    sessionStorage.setItem('userLat', lat);
    sessionStorage.setItem('userLng', lon);

    document.getElementById('user-lat').value = lat;
    document.getElementById('user-lon').value = lon;

    // Reverse geocode to update the address in the location input field
    if (shouldReverseGeocode) {
        reverseGeocode(lat, lon);
    }

    // After updating the user location, re-initialize the service markers and service list
    initializeServiceMarkers();
    updateServiceList();
}

// Function to reverse geocode coordinates to an address
function reverseGeocode(lat, lon) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data && data.display_name) {
                const address = data.display_name;
                const locationInput = document.getElementById('location');
                if (locationInput) {
                    locationInput.value = address;
                }
                // Save the address to sessionStorage
                sessionStorage.setItem('userAddress', address);
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
                window.userLat = lat;
                window.userLng = lon;

                document.getElementById('user-lat').value = lat;
                document.getElementById('user-lon').value = lon;

                // Update the map and marker
                setUserLocation(lat, lon, false);

                // Save the address to sessionStorage
                sessionStorage.setItem('userAddress', address);

                return Promise.resolve();
            } else {
                return Promise.reject('Address not found');
            }
        });
}

// Function to get the user's current location
function getCurrentLocation() {
    return new Promise(function(resolve, reject) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;

                    // Update userLat and userLng
                    window.userLat = lat;
                    window.userLng = lon;

                    // Update the map and marker
                    setUserLocation(lat, lon, true);

                    // Update hidden inputs
                    document.getElementById('user-lat').value = lat;
                    document.getElementById('user-lon').value = lon;

                    resolve();
                },
                error => {
                    handleLocationError(error);
                    reject(error);
                }
            );
        } else {
            alert("Geolocation is not supported by this browser.");
            reject(new Error("Geolocation not supported"));
        }
    });
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
    const locationInput = document.getElementById('location');
    if (locationInput) {
        locationInput.value = 'New York, NY';
    }
}

// Function to show service details
function showServiceDetails(serviceId) {
    // Find the service in itemsData by Id
    const service = itemsData.find(item => item.Id === serviceId);
    if (!service) {
        console.error(`Service with Id ${serviceId} not found.`);
        return;
    }

    // Populate basic service details
    const serviceIdElem = document.getElementById('serviceId');
    const serviceNameElem = document.getElementById('serviceName');
    const serviceAddressElem = document.getElementById('serviceAddress');
    const serviceTypeElem = document.getElementById('serviceType');
    const serviceRatingElem = document.getElementById('serviceRating');
    const serviceDistanceElem = document.getElementById('serviceDistance');

    if (serviceIdElem) serviceIdElem.textContent = service.Id || 'No ID';
    if (serviceNameElem) serviceNameElem.textContent = service.Name || 'No Name';
    if (serviceAddressElem) serviceAddressElem.textContent = service.Address || 'N/A';
    if (serviceTypeElem) serviceTypeElem.textContent = service.Category || 'Unknown';
    if (serviceRatingElem) serviceRatingElem.textContent = !isNaN(service.Ratings) && service.Ratings !== 0 ? parseFloat(service.Ratings).toFixed(2) : 'N/A';
    if (serviceDistanceElem) serviceDistanceElem.textContent = service.Distance ? parseFloat(service.Distance).toFixed(2) + ' Miles' : 'N/A';

    // Clear previous descriptions
    const descriptionElement = document.getElementById('serviceDescription');
    if (descriptionElement) {
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
    }

    // Handle Get Directions button
    const getDirectionsBtn = document.getElementById('getDirections');
    if (getDirectionsBtn) {
        if (service.MapLink) {
            getDirectionsBtn.href = service.MapLink;
            getDirectionsBtn.style.display = 'inline-block'; // Ensure the button is visible
        } else {
            getDirectionsBtn.href = '#';
            getDirectionsBtn.style.display = 'none'; // Hide the button if no MapLink
        }
    }

    // Assuming you have a function to fetch and display reviews
    if (typeof fetchAndDisplayReviews === 'function') {
        fetchAndDisplayReviews(service.Id, 1);
    }

    // Display the service details panel
    const serviceDetailsDiv = document.getElementById('serviceDetails');
    if (serviceDetailsDiv) {
        serviceDetailsDiv.classList.remove('hidden');
        serviceDetailsDiv.classList.add('block');
    }
}

// Function to initialize service markers based on the updated location and selected filter
function initializeServiceMarkers() {
    // Remove existing service markers
    for (let id in serviceMarkers) {
        map.removeLayer(serviceMarkers[id]);
    }
    serviceMarkers = {};

    // Reset selected marker and sidebar button
    selectedMarker = null;
    selectedSidebarButton = null;

    // Make sure itemsData is defined and accessible
    if (!itemsData || !Array.isArray(itemsData)) {
        console.error('itemsData is not defined or is not an array.');
        return;
    }

    // Get the selected filter from sessionStorage
    const filterSelect = document.getElementById('filterSelect');
    const selectedFilter = filterSelect ? filterSelect.value : 'distance'; // Default to distance

    // Clone itemsData to avoid mutating the original array
    let filteredServices = [...itemsData];

    // Sort based on the selected filter
    if (selectedFilter === 'distance') {
        filteredServices.sort((a, b) => parseFloat(a.Distance) - parseFloat(b.Distance));
    } else if (selectedFilter === 'rating') {
        filteredServices.sort((a, b) => {
            if (isNaN(b.Ratings) && isNaN(a.Ratings)) return 0;
            if (isNaN(b.Ratings)) return -1;
            if (isNaN(a.Ratings)) return 1;
            return b.Ratings - a.Ratings;
        });
    }

    // Calculate distance to filter nearby services
    const radiusInMiles = document.getElementById('radius').value || 5;

    // Helper function to calculate distance between two lat/lon points
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 3958.8;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a =
            0.5 - Math.cos(dLat)/2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            (1 - Math.cos(dLon))/2;

        return R * 2 * Math.asin(Math.sqrt(a));
    }

    // Filter services within the specified radius
    const nearbyServices = filteredServices.filter((item) => {
        if (item.Lat && item.Log) {
            const distance = calculateDistance(window.userLat, window.userLng, item.Lat, item.Log);
            item.Distance = distance;
            return distance <= radiusInMiles;
        }
        return false;
    });

    // Add markers for nearby services
    nearbyServices.forEach((item) => {
        const roundedDistance = Number(item.Distance).toFixed(2);
        const roundedRating = !isNaN(item.Ratings) ? Number(item.Ratings).toFixed(2) : 'N/A';

        // Create popup content with the scroll button
        const popupContent = document.createElement('div');
        popupContent.innerHTML = `
            <div>
                <b>${item.Name}</b><br>
                ${item.Address}<br>
                Rating: ${roundedRating}<br>
                Distance: ${roundedDistance} Miles<br>
                <button class="scroll-to-details mt-2 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                    View Details Below
                </button>
            </div>
        `;

        // Add click event listener to the scroll button
        const scrollButton = popupContent.querySelector('.scroll-to-details');
        scrollButton.addEventListener('click', () => {
            // Show service details first
            showServiceDetails(item.Id);
            
            // Wait for the details to be rendered
            setTimeout(() => {
                const serviceDetails = document.getElementById('serviceDetails');
                if (serviceDetails) {
                    // Calculate position accounting for any fixed header if present
                    const headerOffset = 20; // Adjust this value based on your header height
                    const elementPosition = serviceDetails.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    
                    // Smooth scroll to the details section
                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            }, 100); // Small delay to ensure DOM updates are complete
        });

        const marker = L.marker([item.Lat, item.Log], { icon: defaultIcon })
            .addTo(map)
            .bindPopup(popupContent)
            .on('click', () => {
                selectMarker(marker, item.Id);
                showServiceDetails(item.Id);
            });

        // Store the marker in the serviceMarkers map with service Id as the key
        serviceMarkers[item.Id] = marker;
    });

    // Adjust map view to include all markers
    const allMarkers = Object.values(serviceMarkers);
    if (currentLocationMarker) {
        allMarkers.push(currentLocationMarker);
    }

    if (allMarkers.length > 0) {
        const group = L.featureGroup(allMarkers);
        map.fitBounds(group.getBounds());
    } else {
        // If no service markers, set view to user location or default
        map.setView([window.userLat || defaultLat, window.userLng || defaultLng], 12);
    }
}

// Function to update the service list based on the selected filter and radius
function updateServiceList() {
    const serviceListDiv = document.getElementById('serviceList');
    if (!serviceListDiv) {
        console.error('Service list container not found.');
        return;
    }

    // Get the selected filter from sessionStorage
    const filterSelect = document.getElementById('filterSelect');
    const selectedFilter = filterSelect ? filterSelect.value : 'distance'; // Default to distance

    // Clone itemsData to avoid mutating the original array
    let filteredServices = [...itemsData];

    // Sort based on the selected filter
    if (selectedFilter === 'distance') {
        filteredServices.sort((a, b) => parseFloat(a.Distance) - parseFloat(b.Distance));
    } else if (selectedFilter === 'rating') {
        filteredServices.sort((a, b) => {
            if (isNaN(b.Ratings) && isNaN(a.Ratings)) return 0;
            if (isNaN(b.Ratings)) return -1; // b is NaN, a is valid -> a comes first
            if (isNaN(a.Ratings)) return 1;  // a is NaN, b is valid -> b comes first
            return b.Ratings - a.Ratings;    // Both are valid numbers
        });
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
    const nearbyServices = filteredServices.filter((item) => {
        if (item.Lat && item.Log) {
            const distance = calculateDistance(window.userLat, window.userLng, item.Lat, item.Log);
            // Update the distance property if it's not already accurate
            item.Distance = distance;
            return distance <= radiusInMiles;
        }
        return false;
    });

    // Clear the existing service list
    serviceListDiv.innerHTML = '';

    // Populate the service list with filtered and sorted services
    nearbyServices.forEach((item) => {
        // Create the button element
        const button = document.createElement('button');
        button.className = 'service-button w-full text-left p-2 hover:bg-gray-700 rounded';
        button.setAttribute('data-id', item.Id);

        // Create the inner HTML structure
        button.innerHTML = `
            <div class="flex items-center">
                <!-- Distance on the Left -->
                <div class="text-sm text-gray-400 mr-4 w-24">
                    ${Number(item.Distance).toFixed(2)} Miles
                </div>

                <!-- Name and Address -->
                <div class="flex-1">
                    <div class="font-medium text-gray-300">${item.Name}</div>
                    <div class="text-sm text-gray-400">${item.Address}</div>
                </div>

                <!-- Ratings on the Right -->
                <div class="flex items-center ml-4">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-yellow-400 mr-1" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    <span class="text-gray-400">
                        ${isNaN(item.Ratings) ? 'N/A' : Number(item.Ratings).toFixed(2)}
                    </span>
                </div>
            </div>
        `;

        // Add click event listener to the button
        button.addEventListener('click', () => {
            const serviceId = item.Id;
            if (serviceMarkers[serviceId]) {
                // Programmatically trigger the marker's click event
                serviceMarkers[serviceId].fire('click');
            }
        });

        // Append the button to the service list
        serviceListDiv.appendChild(button);
    });

    // If no services are found, display a message
    if (nearbyServices.length === 0) {
        serviceListDiv.innerHTML = '<p class="text-gray-600">No services found within the selected radius.</p>';
    }
}

// Function to select a marker and highlight it along with the corresponding sidebar button
function selectMarker(marker, serviceId) {
    // Reset the previously selected marker to default icon
    if (selectedMarker && selectedMarker !== marker) {
        selectedMarker.setIcon(defaultIcon);
    }

    // Set the new selected marker
    selectedMarker = marker;
    selectedMarker.setIcon(selectedIcon);

    // Reset the previously selected sidebar button
    if (selectedSidebarButton) {
        selectedSidebarButton.classList.remove('bg-blue-700');
    }

    // Highlight the new sidebar button
    const newSidebarButton = document.querySelector(`.service-button[data-id="${serviceId}"]`);
    if (newSidebarButton) {
        selectedSidebarButton = newSidebarButton;
        selectedSidebarButton.classList.add('bg-blue-700');

        // Get the service list container
        const serviceListDiv = document.getElementById('serviceList');
        if (serviceListDiv) {
            // Calculate the scroll position needed
            const buttonRect = newSidebarButton.getBoundingClientRect();
            const containerRect = serviceListDiv.getBoundingClientRect();
            
            // Calculate if the button is outside the visible area
            const isAbove = buttonRect.top < containerRect.top;
            const isBelow = buttonRect.bottom > containerRect.bottom;
            
            if (isAbove || isBelow) {
                // Calculate the new scroll position
                const scrollPosition = isAbove 
                    ? newSidebarButton.offsetTop - serviceListDiv.offsetTop
                    : newSidebarButton.offsetTop - serviceListDiv.offsetTop - (containerRect.height - buttonRect.height);
                
                // Smoothly scroll the service list container
                serviceListDiv.scrollTo({
                    top: scrollPosition,
                    behavior: 'smooth'
                });
            }
        }
    }

    // Pan the map to the selected marker smoothly
    map.panTo(selectedMarker.getLatLng());

    // Optionally, open the popup associated with the marker
    selectedMarker.openPopup();
}

// Function to hide service details
document.getElementById('closeDetails').addEventListener('click', () => {
    const serviceDetailsDiv = document.getElementById('serviceDetails');
    if (serviceDetailsDiv) {
        serviceDetailsDiv.classList.add('hidden');
        serviceDetailsDiv.classList.remove('block'); // Optionally remove 'block'
    }
});
