function showModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('hidden');
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('hidden');
}

function setupDeleteHandlers() {
    // Setup handlers for post deletion
    document.querySelectorAll('[data-delete-post]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            showModal('deletePostModal');
            const postId = button.getAttribute('data-delete-post');
            const form = document.getElementById('deletePostForm');
            form.action = `/forum/post/${postId}/delete/`;
        });
    });

    // Setup handlers for comment deletion
    document.querySelectorAll('[data-delete-comment]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            showModal('deleteCommentModal');
            const commentId = button.getAttribute('data-delete-comment');
            const form = document.getElementById('deleteCommentForm');
            form.action = `/forum/comment/${commentId}/delete/`;
        });
    });

    // Setup cancel buttons
    document.querySelectorAll('[data-modal-close]').forEach(button => {
        button.addEventListener('click', () => {
            hideModal(button.getAttribute('data-modal-close'));
        });
    });
}

// Initialize when the document is loaded
document.addEventListener('DOMContentLoaded', setupDeleteHandlers);