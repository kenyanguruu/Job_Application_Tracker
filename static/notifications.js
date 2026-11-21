(() => {
    "use strict";

    document.querySelectorAll(".flash-message").forEach((message) => {
        const closeButton = message.querySelector(".flash-close");

        function dismissNotification() {
            message.style.transition = "opacity 0.3s ease, transform 0.3s ease";
            message.style.opacity = "0";
            message.style.transform = "translateY(-8px)";

            setTimeout(() => {
                message.remove();
            }, 300);
        }

        if (closeButton) {
            closeButton.addEventListener("click", dismissNotification);
        }

        setTimeout(dismissNotification, 5000);
    });
})();