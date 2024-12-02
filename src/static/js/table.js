document.addEventListener('DOMContentLoaded', () => {

    function formatTimestamp(utcTimestamp) {
        // Ensure we're parsing the UTC timestamp correctly
        const date = new Date(utcTimestamp + 'Z'); // Append 'Z' to ensure UTC interpretation

        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true,
        };

        return date.toLocaleString(undefined, options);
    }

    const reviewFormContainer = document.getElementById('reviewFormContainer');
    const loginToReviewContainer = document.getElementById('loginToReviewContainer');

    if (userIsAuthenticated) {
        reviewFormContainer.style.display = 'block';
        loginToReviewContainer.style.display = 'none';
    } else {
        reviewFormContainer.style.display = 'none';
        loginToReviewContainer.style.display = 'block';

        const loginButton = document.getElementById('loginToReview');
        loginButton.addEventListener('click', () => {
            window.location.href = '/accounts/login/user/';
        });
    }

    function sanitizeHTML(str) {
        const tempDiv = document.createElement('div');
        tempDiv.textContent = str; // Escapes the string
        return tempDiv.innerHTML;  // Returns the escaped string
    }

    async function fetchAndDisplayReviews(serviceId, page = 1) {

        try {
            const response = await fetch(`/home/get_reviews/${serviceId}/?page=${page}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch reviews. Status: ${response.status}`);
            }

            const {reviews, has_next, has_previous, current_page, username} = await response.json();

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

                const flexContainer = document.createElement('div');
                flexContainer.classList.add('flex-container'); // Add custom class for styling

                // Create and configure the rating element
                const ratingElement = document.createElement('p');
                ratingElement.classList.add('text-yellow-400', 'font-semibold', 'rating-element');
                ratingElement.textContent = `${rating} ★`;

                // Append the rating element to the flex container
                flexContainer.appendChild(ratingElement);

                // Check if username matches
                if (username === review.Username) {
                    // Create a container for the icons
                    const iconContainer = document.createElement('div');
                    iconContainer.classList.add('icon-container'); // Add custom class for styling

                    if(!review.ResponseText){
                        const editIcon = document.createElement('i');
                        editIcon.classList.add('fas', 'fa-edit', 'text-blue-500', 'cursor-pointer');
                        editIcon.title = "Edit Review";
                        editIcon.onclick = () => handleEditReview(review);
                        iconContainer.appendChild(editIcon);
                    }
                    // Delete icon
                    const deleteIcon = document.createElement('i');
                    deleteIcon.classList.add('fas', 'fa-trash', 'text-red-500', 'cursor-pointer');
                    deleteIcon.title = "Delete Review";
                    deleteIcon.onclick = () => handleDeleteReview(review);
                    iconContainer.appendChild(deleteIcon);

                    // Append the icon container to the flex container
                    flexContainer.appendChild(iconContainer);
                }

                // Append the flex container to the reviewDiv
                reviewDiv.appendChild(flexContainer);


                const reviewText = document.createElement('p');
                reviewText.classList.add('text-sm');
                reviewText.innerHTML = sanitizeHTML(review.RatingMessage).replace(/\n/g, '<br>');
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
                    responseText.innerHTML = sanitizeHTML(review.ResponseText).replace(/\n/g, '<br>');
                    responseDiv.appendChild(responseText);

                    const respondedAt = formatTimestamp(review.RespondedAt);
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

    // Expose the function globally
    window.fetchAndDisplayReviews = fetchAndDisplayReviews;

    // Add the showServiceDetails function
    function showServiceDetails(index) {
        const service = itemsData.find(item => item.Id === index);
        if (!service) {
            console.error(`Service with index ${index} not found.`);
            return;
        }

        document.getElementById('reviewRating').value = '';
        document.getElementById('reviewText').value = '';

        // Populate basic service details
        document.getElementById('serviceId').textContent = service.Id || 'No ID';
        document.getElementById('serviceName').textContent = service.Name || 'No Name';
        document.getElementById('serviceAddress').textContent = service.Address || 'N/A';
        document.getElementById('serviceType').textContent = service.Category || 'Unknown';
        document.getElementById('serviceRating').textContent = service.Ratings && service.Ratings !== 0 ? parseFloat(service.Ratings).toFixed(2) : 'N/A';
        document.getElementById('serviceDistance').textContent = service.Distance ? parseFloat(service.Distance).toFixed(2) + ' miles' : 'N/A';

        const serviceAvailability = document.getElementById('serviceAvailability');
        if (service.IsActive === false) {
            serviceAvailability.textContent = 'Currently Unavailable';
            serviceAvailability.classList.remove('text-green-500');
            serviceAvailability.classList.add('text-red-500');
        } else {
            serviceAvailability.textContent = 'Available';
            serviceAvailability.classList.remove('text-red-500');
            serviceAvailability.classList.add('text-green-500');
        }
        serviceAvailability.classList.remove('hidden');


        const bookmarkCheckbox = document.getElementById('bookmarkCheckbox');

        if (bookmarkCheckbox && userIsAuthenticated) {

            // Set the initial checkbox state based on the bookmark status
            bookmarkCheckbox.checked = service.IsBookmarked;


            // Add event listener to the bookmark checkbox
            bookmarkCheckbox.onchange = function () {
                const action = bookmarkCheckbox.checked ? 'add' : 'remove';
                const serviceId = service.Id;

                fetch('/home/toggle_bookmark/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken(),
                    },
                    body: JSON.stringify({
                        'service_id': serviceId,
                        'action': action,
                    }),
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            service.IsBookmarked = bookmarkCheckbox.checked;
                        } else {
                            // Revert the checkbox state if the request failed
                            bookmarkCheckbox.checked = !bookmarkCheckbox.checked;
                            alert(data.error || 'Failed to toggle bookmark.');
                        }
                    })
                    .catch(error => {
                        console.error('Error toggling bookmark:', error);
                        // Revert the checkbox state if an error occurred
                        bookmarkCheckbox.checked = !bookmarkCheckbox.checked;
                        alert('An error occurred. Please try again.');
                    });
            };
        } else if (bookmarkCheckbox) {
            // Hide the bookmark checkbox if the user is not authenticated
            bookmarkCheckbox.parentElement.style.display = true;
        }


        const descriptionElement = document.getElementById('serviceDescription');
        descriptionElement.innerHTML = '';  // Clear previous content

        const heading = document.createElement('h3');
        heading.textContent = 'Additional Descriptive Details:';
        heading.style.marginBottom = '10px';
        heading.style.fontSize = '1.1em';
        heading.style.fontWeight = 'bold';
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

        const getDirectionsBtn = document.getElementById('getDirections');

        if (service.MapLink) {
            getDirectionsBtn.href = service.MapLink;
            getDirectionsBtn.style.display = 'inline-block';
        } else {
            getDirectionsBtn.href = '#';
            getDirectionsBtn.style.display = 'none';
        }

        // Fetch and display reviews
        fetchAndDisplayReviews(service.Id, 1);

        const serviceDetailsDiv = document.getElementById('serviceDetails');
        if (serviceDetailsDiv) {
            serviceDetailsDiv.classList.remove('hidden');
            serviceDetailsDiv.classList.add('block');
        }
    }

    // Expose the function globally
    window.showServiceDetails = showServiceDetails;

    // Event listener for closeDetails button
    document.getElementById('closeDetails').addEventListener('click', () => {
        const serviceDetailsDiv = document.getElementById('serviceDetails');
        if (serviceDetailsDiv) {
            serviceDetailsDiv.classList.add('hidden');
            serviceDetailsDiv.classList.remove('block');
        }
    });

    async function handleEditReview(review) {
        try {
          const newRating = prompt(
            "Enter a new rating (1-5):",
            review.RatingStars
          );

          // Validate the rating input
          const ratingRegex = /^[1-5]$/; // Only allows values from 1 to 5

          if (!newRating || !ratingRegex.test(newRating)) {
            alert("Please enter a valid rating between 1 and 5.");
            return;
          }

          const newMessage = prompt("Enter a new message:", review.RatingMessage);
          if (!newMessage.trim()) {
            alert("A message is required.");
            return;
          }

          const response = await fetch(
            `/home/edit_review/${review["ReviewId"]}/`,
            {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
              },
              body: JSON.stringify({
                username: review.Username,
                rating: parseInt(newRating),
                message: newMessage,
              }),
            }
          );

          const data = await response.json();

          if (response.ok && data.success) {
            fetchAndDisplayReviews(review.ServiceId, 1); // Refresh the reviews
          } else {
            alert(data.error || "Failed to edit review.");
          }
        } catch (error) {
          console.error("Error editing review:", error);
          alert("An error occurred. Please try again.");
        }
      }
      function handleDeleteReview(review) {
        if (confirm("Are you sure you want to delete this review?")) {
          fetch(`/home/delete_review/${review["ReviewId"]}/`, {
            method: "DELETE",
            headers: {
              "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
              username: review.Username,
            }),
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                // console.log("fetching again after delete " + review.ServiceId);
                fetchAndDisplayReviews(review.ServiceId, 1); // Refresh the reviews
              } else {
                alert(data.error || "Failed to delete review.");
              }
            })
            .catch((error) => {
              console.error("Error deleting review:", error);
              alert("An error occurred. Please try again.");
            });
        }
      }

    // Event listener for submitReview button
    document.getElementById('submitReview').addEventListener('click', async () => {
        const rating = document.getElementById('reviewRating').value;
        const message = document.getElementById('reviewText').value;
        const serviceId = document.getElementById('serviceId').textContent.trim();

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

// Function to get CSRF token from cookies
function getCsrfToken() {
    const cookies = document.cookie.split('; ');
    for (const cookie of cookies) {
        const [name, value] = cookie.split('=');
        if (name === 'csrftoken') return value;
    }
    return '';
}
