const profileButton = document.getElementById('profileButton');
const profileDropdown = document.getElementById('profileDropdown');

profileButton.addEventListener('click', () => {
    profileDropdown.classList.toggle('hidden');
});

// Optional: Close the dropdown if clicked outside
document.addEventListener('click', (e) => {
    if (!profileButton.contains(e.target) && !profileDropdown.contains(e.target)) {
        profileDropdown.classList.add('hidden');
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const radiusSlider = document.getElementById('radius');
    const radiusValue = document.getElementById('radiusValue');

    if (radiusSlider && radiusValue) {
        radiusSlider.addEventListener('input', function() {
            radiusValue.textContent = this.value;
        });
    }
});

document.addEventListener('DOMContentLoaded', () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
           var lat = position.coords.latitude;
           var lon = position.coords.longitude;
           document.getElementById('user-lat').value = lat;
           document.getElementById('user-lon').value = lon;
        }, function(error) {
           console.error("Error getting user location:", error);
        });
    } else {
        console.error("Geolocation is not supported by this browser.");
    }
});