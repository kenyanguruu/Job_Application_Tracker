
(() => {
    "use strict";

    const deleteForm = document.getElementById("delete-application-form");
    const deleteTrigger = document.getElementById("delete-trigger");
    const deleteDialog = document.getElementById("delete-confirm-dialog");
    const cancelDelete = document.getElementById("cancel-delete");
    const confirmDelete = document.getElementById("confirm-delete");

    if (!deleteForm || !deleteTrigger || !deleteDialog ||
        !cancelDelete || !confirmDelete) {
        return;
    }

    // Open the custom confirmation dialog.
    deleteTrigger.addEventListener("click", () => {
        deleteDialog.showModal();
    });

    // Close the dialog without deleting.
    cancelDelete.addEventListener("click", () => {
        deleteDialog.close();
    });

    // Submit the original protected POST form.
    confirmDelete.addEventListener("click", () => {
        deleteForm.requestSubmit();
    });

    // Close the dialog when clicking outside its content.
    deleteDialog.addEventListener("click", (event) => {
        if (event.target === deleteDialog) {
            deleteDialog.close();
        }
    });

})();
