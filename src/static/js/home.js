// home.js

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrfToken = getCookie('csrftoken');

// Function to show the login modal
function showLoginModal() {
    const loginModal = document.getElementById('loginModal');
    if (loginModal) {
        loginModal.classList.remove('hidden');
    }
}

// Function to hide the login modal
function hideLoginModal() {
    const loginModal = document.getElementById('loginModal');
    if (loginModal) {
        loginModal.classList.add('hidden');
    }
}

// Event listener for DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    // Handle login form submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            // Perform AJAX login
            fetch('/ajax_login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                }),
            })
            .then(response => {
                if (response.ok) {
                    hideLoginModal();
                    // Optionally refresh the page or update the UI to reflect the logged-in state
                    location.reload();
                } else {
                    return response.json().then(data => {
                        alert(data.error || 'Login failed. Please try again.');
                    });
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                alert('An error occurred during login. Please try again.');
            });
        });
    }

    // Handle cancel button
    const cancelLoginBtn = document.getElementById('cancelLogin');
    if (cancelLoginBtn) {
        cancelLoginBtn.addEventListener('click', function() {
            hideLoginModal();
        });
    }

    // Handle close button
    const closeLoginModalBtn = document.getElementById('closeLoginModal');
    if (closeLoginModalBtn) {
        closeLoginModalBtn.addEventListener('click', function() {
            hideLoginModal();
        });
    }

    // Example: Handle user-specific actions (e.g., bookmarking)
    const bookmarkButtons = document.querySelectorAll('.bookmark-btn');
    bookmarkButtons.forEach(button => {
        button.addEventListener('click', function() {
            const serviceId = this.dataset.serviceId;
            const action = this.dataset.action; // 'add' or 'remove'

            toggleBookmark(serviceId, action, this);
        });
    });

    // Function to toggle bookmark
    function toggleBookmark(serviceId, action, button) {
        fetch('/toggle_bookmark/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                service_id: serviceId,
                action: action,
            }),
        })
        .then(response => {
            if (response.status === 401) {
                // User is not authenticated, show login modal
                showLoginModal();
            } else if (response.ok) {
                return response.json().then(data => {
                    // Update bookmark UI
                    if (data.action === 'added') {
                        button.dataset.action = 'remove';
                        button.textContent = 'Unbookmark';
                    } else if (data.action === 'removed') {
                        button.dataset.action = 'add';
                        button.textContent = 'Bookmark';
                    }
                });
            } else {
                return response.json().then(data => {
                    alert(data.error || 'Failed to toggle bookmark.');
                });
            }
        })
        .catch(error => {
            console.error('Toggle bookmark error:', error);
            alert('An error occurred while toggling the bookmark.');
        });
    }
});
