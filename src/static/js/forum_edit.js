document.addEventListener('DOMContentLoaded', function() {
    // Edit Post functionality
    const editPostModal = document.getElementById('editPostModal');
    const editPostForm = document.getElementById('editPostForm');
    const editPostButtons = document.querySelectorAll('[data-edit-post]');

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

    // Close modals
    document.querySelectorAll('[data-modal-close]').forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.dataset.modalClose;
            document.getElementById(modalId).classList.add('hidden');
        });
    });
});