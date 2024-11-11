const profileButton = document.getElementById('profileButton');
const profileDropdown = document.getElementById('profileDropdown');
const notificationsButton = document.getElementById('notificationsButton');
const notificationsDropdown = document.getElementById('notificationsDropdown');

profileButton.addEventListener('click', () => {
    profileDropdown.classList.toggle('hidden');
});

if (notificationsButton) {
    notificationsButton.addEventListener('click', () => {
        notificationsDropdown.classList.toggle('hidden');
        profileDropdown.classList.add('hidden');
    });
}


// Optional: Close the dropdown if clicked outside
document.addEventListener('click', (e) => {
    if (!profileButton.contains(e.target) && !profileDropdown.contains(e.target)) {
        profileDropdown.classList.add('hidden');
    }

    if (notificationsButton && !notificationsButton.contains(e.target) && !notificationsDropdown.contains(e.target)) {
        notificationsDropdown.classList.add('hidden');
    }
});


if (notificationsButton) {
    function updateNotificationCount() {
        fetch('/forum/notifications/count/')
            .then(response => response.json())
            .then(data => {
                const countElement = document.getElementById('notificationCount');
                if (countElement) {
                    countElement.textContent = data.count;
                    countElement.style.display = data.count > 0 ? 'flex' : 'none';
                }
            });
    }

    // Update count every 30 seconds
    setInterval(updateNotificationCount, 30000);
}

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

// Add this to nav.js after the existing code
if (notificationsDropdown) {
    notificationsDropdown.addEventListener('click', async (e) => {
        if (e.target.matches('button[type="submit"]') || e.target.closest('button[type="submit"]')) {
            e.preventDefault();
            const form = e.target.closest('form');
            if (!form) return;

            // Check if it's the mark-all-read form
            if (form.classList.contains('mark-all-read-form')) {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (response.ok) {
                    // Remove all unread styling
                    const unreadNotifications = notificationsDropdown.querySelectorAll('.bg-blue-50');
                    unreadNotifications.forEach(notification => {
                        notification.classList.remove('bg-blue-50');
                    });
                    // Update the notification count
                    updateNotificationCount();
                }
            }
            // Check if it's the delete notification form
            else if (form.classList.contains('delete-notification-form')) {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (response.ok) {
                    // Remove the notification element from the DOM
                    const notificationDiv = form.closest('.border-b');
                    notificationDiv.remove();

                    // Update the notification count
                    updateNotificationCount();

                    // If no more notifications, show the "No notifications" message
                    const remainingNotifications = notificationsDropdown.querySelectorAll('.border-b');
                    if (remainingNotifications.length === 0) {
                        const emptyMessage = document.createElement('div');
                        emptyMessage.className = 'p-4 text-center text-gray-500';
                        emptyMessage.textContent = 'No notifications';
                        notificationsDropdown.querySelector('.max-h-96').appendChild(emptyMessage);
                    }
                }
            }
            // Regular mark as read form
            else {
                const response = await fetch(form.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (response.ok) {
                    const notificationDiv = form.closest('.border-b');
                    notificationDiv.classList.remove('bg-blue-50');
                    updateNotificationCount();
                }
            }
        }
    });
}