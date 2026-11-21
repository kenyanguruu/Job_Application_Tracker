
(() => {
    "use strict";

    const THEME_KEY = "jobtracker-theme";
    const themeSelect = document.getElementById("theme-select");
    const root = document.documentElement;
    const systemPreference = window.matchMedia("(prefers-color-scheme: dark)");

    function applyTheme(preference) {
        const effectiveTheme = preference === "system"
            ? (systemPreference.matches ? "dark" : "light")
            : preference;

        root.setAttribute("data-theme", effectiveTheme);

        if (themeSelect) {
            themeSelect.value = preference;
        }
    }

    // Dark is the default for new users.
    let savedTheme = "dark";

    try {
        const stored = localStorage.getItem(THEME_KEY);

        if (["light", "dark", "system"].includes(stored)) {
            savedTheme = stored;
        }
    } catch (error) {
        // Continue using dark mode if storage is unavailable.
    }

    applyTheme(savedTheme);

    if (themeSelect) {
        themeSelect.addEventListener("change", () => {
            const selected = themeSelect.value;

            if (!["light", "dark", "system"].includes(selected)) {
                return;
            }

            try {
                localStorage.setItem(THEME_KEY, selected);
            } catch (error) {
                // Theme still works for this page.
            }

            applyTheme(selected);
        });
    }

    if (typeof systemPreference.addEventListener === "function") {
        systemPreference.addEventListener("change", () => {
            if (savedTheme === "system") {
                applyTheme("system");
            }
        });
    }

    // Keep track of the current preference.
    if (themeSelect) {
        themeSelect.addEventListener("change", () => {
            savedTheme = themeSelect.value;
        });
    }
})();
