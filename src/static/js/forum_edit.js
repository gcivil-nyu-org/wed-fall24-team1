document.addEventListener('DOMContentLoaded', function() {
    // Edit Post functionality
    const editPostModal = document.getElementById('editPostModal');
    const editPostForm = document.getElementById('editPostForm');
    const editPostButtons = document.querySelectorAll('[data-edit-post]');

    // Add form validation for posts
    editPostForm.addEventListener('submit', function(e) {
        const title = document.getElementById('editPostTitle').value.trim();
        const content = document.getElementById('editPostContent').value.trim();
        let isValid = true;

        // Clear previous error messages if any
        clearErrors();

        // Title validation
        if (!title) {
            showError('editPostTitle', 'Title cannot be empty');
            isValid = false;
        } else if (title.length > 100) {
            showError('editPostTitle', 'Title must not exceed 100 characters');
            isValid = false;
        }

        // Content validation
        if (!content) {
            showError('editPostContent', 'Content cannot be empty');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    });

    editPostButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const postId = button.dataset.editPost;
            try {
                const response = await fetch(`/forum/post/${postId}/edit/`);
                const data = await response.json();

                document.getElementById('editPostTitle').value = data.title;
                document.getElementById('editPostContent').value = data.content;
                editPostForm.action = `/forum/post/${postId}/edit/`;

                editPostModal.classList.remove('hidden');
            } catch (error) {
                console.error('Error fetching post data:', error);
            }
        });
    });

    // Edit Comment functionality
    const editCommentModal = document.getElementById('editCommentModal');
    const editCommentForm = document.getElementById('editCommentForm');
    const editCommentButtons = document.querySelectorAll('[data-edit-comment]');

    // Add form validation for comments
    editCommentForm.addEventListener('submit', function(e) {
        const content = document.getElementById('editCommentContent').value.trim();
        let isValid = true;

        // Clear previous error messages if any
        clearErrors();

        // Content validation
        if (!content) {
            showError('editCommentContent', 'Comment cannot be empty');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    });

    editCommentButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const commentId = button.dataset.editComment;
            try {
                const response = await fetch(`/forum/comment/${commentId}/edit/`);
                const data = await response.json();

                document.getElementById('editCommentContent').value = data.content;
                editCommentForm.action = `/forum/comment/${commentId}/edit/`;

                editCommentModal.classList.remove('hidden');
            } catch (error) {
                console.error('Error fetching comment data:', error);
            }
        });
    });

    // Helper functions for validation
    function showError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message text-red-500 text-sm mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    function clearErrors() {
        document.querySelectorAll('.error-message').forEach(error => error.remove());
    }

    // Close modals
    document.querySelectorAll('[data-modal-close]').forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.dataset.modalClose;
            document.getElementById(modalId).classList.add('hidden');
        });
    });
});