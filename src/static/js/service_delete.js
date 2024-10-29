document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('deleteModal');
    const deleteButtons = document.querySelectorAll('.delete-service');
    const deleteForm = document.getElementById('deleteForm');
    const confirmDeleteButton = document.getElementById('confirmDelete');
    const cancelDeleteButton = document.getElementById('cancelDelete');
    const serviceNameSpan = document.getElementById('serviceName');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const serviceId = this.dataset.serviceId;
            const serviceName = this.dataset.serviceName;
            serviceNameSpan.textContent = serviceName;
            deleteForm.action = `/services/${serviceId}/delete/`;
            deleteModal.classList.remove('hidden');
        });
    });

    cancelDeleteButton.addEventListener('click', function() {
        deleteModal.classList.add('hidden');
    });

    // No need for confirmDeleteButton event listener as the form will handle submission
});