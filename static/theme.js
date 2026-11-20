const themeSelect = document.getElementById("theme-select");

const savedTheme = localStorage.getItem("jobtracker-theme") || "system";


function applyTheme(theme) {

    const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)"
    ).matches;

    let effectiveTheme = theme;

    if (theme === "system") {
        effectiveTheme = prefersDark ? "dark" : "light";
    }

    document.documentElement.setAttribute(
        "data-theme",
        effectiveTheme
    );

    if (themeSelect) {
        themeSelect.value = theme;
    }
}


// Apply the saved theme when the page loads

applyTheme(savedTheme);


// Save and apply a new theme when selected

if (themeSelect) {

    themeSelect.addEventListener("change", function () {

        const selectedTheme = this.value;

        localStorage.setItem(
            "jobtracker-theme",
            selectedTheme
        );

        applyTheme(selectedTheme);

    });

}