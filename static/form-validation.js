
(() => {
    "use strict";

    const form = document.querySelector(".application-form form");
    if (form) {
        form.setAttribute("novalidate", "novalidate");
    }

    if (!form) {
        return;
    }

    const fields = [
        "company_name",
        "job_title",
        "job_location",
        "applicant_name",
        "contact_email",
        "phone_number"
    ];

    const limits = {
        company_name: 150,
        job_title: 150,
        job_location: 150,
        applicant_name: 150,
        contact_email: 150,
        phone_number: 50
    };

    const emailPattern = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

    function getErrorMessage(field) {
        const value = field.value.trim();
        const name = field.name;

        if (fields.includes(name) && !value) {
            return "This field is required.";
        }

        if (limits[name] && value.length > limits[name]) {
            return `Maximum ${limits[name]} characters allowed.`;
        }

        if (name === "contact_email" && value && !emailPattern.test(value)) {
            return "Please enter a valid email address.";
        }

        if (name === "application_status") {
            const allowedStatuses = [
                "Applied",
                "Under Review",
                "Interview",
                "Offered",
                "Rejected"
            ];

            if (!allowedStatuses.includes(value)) {
                return "Please select a valid application status.";
            }
        }

        return "";
    }

    function showError(field, message) {
        let error = document.getElementById(`${field.id}-error`);

        if (!error) {
            error = document.createElement("small");
            error.id = `${field.id}-error`;
            error.className = "field-error";
            error.setAttribute("role", "alert");

            field.insertAdjacentElement("afterend", error);
        }

        error.textContent = message;
        field.setAttribute("aria-invalid", message ? "true" : "false");

        if (message) {
            field.classList.add("input-invalid");
        } else {
            field.classList.remove("input-invalid");
        }
    }

    function validateField(field) {
        const message = getErrorMessage(field);
        showError(field, message);
        return !message;
    }

    fields.forEach((name) => {
        const field = form.elements.namedItem(name);

        if (!field) {
            return;
        }

        field.addEventListener("blur", () => {
            validateField(field);
        });

        field.addEventListener("input", () => {
            if (field.getAttribute("aria-invalid") === "true") {
                validateField(field);
            }
        });
    });

    const statusField = form.elements.namedItem("application_status");

    if (statusField) {
        statusField.addEventListener("change", () => {
            validateField(statusField);
        });
    }

    form.addEventListener("submit", (event) => {
        let formIsValid = true;

        fields.forEach((name) => {
            const field = form.elements.namedItem(name);

            if (field && !validateField(field)) {
                formIsValid = false;
            }
        });

        if (statusField && !validateField(statusField)) {
            formIsValid = false;
        }

        if (!formIsValid) {
            event.preventDefault();

            const firstInvalidField = form.querySelector(
                '[aria-invalid="true"]'
            );

            if (firstInvalidField) {
                firstInvalidField.focus();
            }
        }
    });
})();
