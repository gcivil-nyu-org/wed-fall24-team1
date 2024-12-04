async function checkFlagStatus(contentType, objectId) {
    try {
        const response = await fetch(`/moderation/check_flag_status/${contentType}/${objectId}/`);
        if (!response.ok) throw new Error('Failed to check flag status');
        return await response.json();
    } catch (error) {
        console.error('Error checking flag status:', error);
        return { hasPendingFlag: false };
    }
}

// Function to create appropriate icon based on flag status
function createFlagIcon(contentType, objectId, container) {
    checkFlagStatus(contentType, objectId).then(status => {
        container.innerHTML = ''; // Clear existing content

        if (status.hasPendingFlag) {
            // Create "under review" icon
            const reviewIcon = document.createElement('i');
            reviewIcon.classList.add('fas', 'fa-clock', 'text-yellow-500');
            reviewIcon.title = "This content is under review";
            container.appendChild(reviewIcon);

        } else {
            // Create normal flag icon
            const flagIcon = document.createElement('i');
            flagIcon.classList.add('fas', 'fa-flag', 'text-gray-400', 'hover:text-red-500', 'cursor-pointer');
            flagIcon.title = "Report this content";
            flagIcon.onclick = () => openFlagModal(contentType, objectId);
            container.appendChild(flagIcon);
        }
    });
}

function updateFlagIconsForForumContent() {
    // Update flag icons for posts
    document.querySelectorAll('[data-flag-container]').forEach(container => {
        const contentType = container.dataset.contentType;
        const objectId = container.dataset.objectId;
        createFlagIcon(contentType, objectId, container);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    updateFlagIconsForForumContent();
});