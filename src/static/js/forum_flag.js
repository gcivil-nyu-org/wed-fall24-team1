async function checkFlagStatus(contentType, objectId) {
    try {
        const response = await fetch(`/moderation/check_flag_status/${contentType}/${objectId}/`);
        if (!response.ok) throw new Error('Failed to check flag status');
        const data = await response.json();

        // Return the full data object so we can use all the information
        return {
            userHasFlagged: data.userHasFlagged,
            hasPendingFlags: data.hasPendingFlags,
            pendingFlagsCount: data.pendingFlagsCount
        };
    } catch (error) {
        console.error('Error checking flag status:', error);
        // Return a safe default state if there's an error
        return {
            userHasFlagged: false,
            hasPendingFlags: false,
            pendingFlagsCount: 0
        };
    }
}

function createFlagIcon(contentType, objectId, container) {
    checkFlagStatus(contentType, objectId).then(status => {
        container.innerHTML = ''; // Clear existing content

        if (status.userHasFlagged) {
            // Show clock icon only to users who have flagged the content
            const reviewIcon = document.createElement('i');
            reviewIcon.classList.add('fas', 'fa-clock', 'text-yellow-500');
            reviewIcon.title = "You have reported this content - under review";
            container.appendChild(reviewIcon);
        } else {
            // Show flag icon to users who haven't flagged yet
            const flagIcon = document.createElement('i');
            flagIcon.classList.add('fas', 'fa-flag', 'text-gray-400', 'hover:text-red-500', 'cursor-pointer');
            flagIcon.title = "Report this content";

            // Only add click handler if the user hasn't flagged yet
            flagIcon.onclick = () => openFlagModal(contentType, objectId);
            container.appendChild(flagIcon);
        }

        // Optionally, for admin users, we could show additional information
        // This would require passing the user's admin status to the frontend
        if (window.isAdminUser && status.hasPendingFlags) {
            const flagCount = document.createElement('span');
            flagCount.classList.add('text-xs', 'text-yellow-500', 'ml-1');
            flagCount.title = "Number of pending flags";
            flagCount.textContent = status.pendingFlagsCount;
            container.appendChild(flagCount);
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