// Only run if not already initialized
if (!window.serviceFormInitialized) {
    window.serviceFormInitialized = true;

    const initializeFormHandlers = () => {
        const addButton = document.getElementById('add-description');
        const formset = document.getElementById('description-formset');
        const totalForms = document.getElementById('id_description-TOTAL_FORMS');
        let formCount = parseInt(totalForms.value);

        // Get the empty form template
        const emptyFormTemplate = document.getElementById('empty-form-template').innerHTML;

        // Function to add a new description item
        function addDescription() {
            // Replace __prefix__ with the current form count
            let newFormHtml = emptyFormTemplate.replace(/__prefix__/g, formCount);

            // Create a temporary div to hold the new form HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = newFormHtml;

            // Get the new form element
            const newForm = tempDiv.firstElementChild;

            // Append the new form to the formset
            formset.appendChild(newForm);

            // Increment form count and update total forms
            formCount++;
            totalForms.value = formCount;

            // Attach delete event listener to the new delete button
            const deleteButton = newForm.querySelector('.delete-description').add('bg-red-600', 'hover:bg-red-700', 'text-white');
            deleteButton.addEventListener('click', function() {
                markFormForDeletion(this);
            });
        }

        // Function to mark a form for deletion
        function markFormForDeletion(button) {
            const formDiv = button.closest('.description-form');
            const deleteInput = formDiv.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteInput) {
                deleteInput.checked = true;
            }
            formDiv.style.display = 'none';

            // Check if there are any visible forms left
            const visibleForms = formset.querySelectorAll('.description-form:not([style*="display: none"])');
            if (visibleForms.length === 0) {
                addDescription();
            }
        }

        // Attach delete event listeners to existing delete buttons
        document.querySelectorAll('.delete-description').forEach(button => {
            button.addEventListener('click', function() {
                markFormForDeletion(this);
            });
        });

        // Attach add event listener to the add button
        if (addButton) {
            addButton.addEventListener('click', addDescription);
        }

        // Add initial blank form if no forms exist
        const existingForms = formset.querySelectorAll('.description-form');
        if (existingForms.length === 0) {
            addDescription();
        }
    };

    // Only attach the event listener if we're not already in DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeFormHandlers);
    } else {
        initializeFormHandlers();
    }
}