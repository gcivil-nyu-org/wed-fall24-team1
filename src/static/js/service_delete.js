document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('deleteModal');
    const deleteButtons = document.querySelectorAll('.delete-service');
    const confirmDeleteButton = document.getElementById('confirmDelete');
    const cancelDeleteButton = document.getElementById('cancelDelete');
    const serviceNameSpan = document.getElementById('serviceName');
    let currentServiceId = null;

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            currentServiceId = this.dataset.serviceId;
            serviceNameSpan.textContent = this.dataset.serviceName;
            deleteModal.classList.remove('hidden');
        });
    });

    cancelDeleteButton.addEventListener('click', function() {
        deleteModal.classList.add('hidden');
    });

    confirmDeleteButton.addEventListener('click', function() {
        if (currentServiceId) {
            window.location.href = `/services/${currentServiceId}/delete/`;
        }
    });
});