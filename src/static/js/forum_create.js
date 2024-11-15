document.addEventListener('DOMContentLoaded', function() {
    const createPostForm = document.querySelector('form');

    createPostForm.addEventListener('submit', function(e) {
        const title = document.querySelector('#id_title').value.trim();
        const content = document.querySelector('#id_content').value.trim();
        let isValid = true;

        // Clear previous error messages
        clearErrors();

        // Title validation
        if (!title) {
            showError('id_title', 'Title cannot be empty');
            isValid = false;
        } else if (title.length > 100) {
            showError('id_title', 'Title must not exceed 100 characters');
            isValid = false;
        }

        // Content validation
        if (!content) {
            showError('id_content', 'Content cannot be empty');
            isValid = false;
        }

        if (!isValid) {
            e.preventDefault();
        }
    });

    // Helper functions for validation
    function showError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-500 text-sm mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    function clearErrors() {
        document.querySelectorAll('.text-red-500.text-sm.mt-1').forEach(error => error.remove());
    }
});