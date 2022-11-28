'use strict';
{
    window.addEventListener('DOMContentLoaded', function (e) {
        function getFallbackTheme() {
            const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
            return prefersDark ? "dark" : "light";
        }

        function setTheme(mode) {
            if (mode !== "light" && mode !== "dark") {
                const newMode = getFallbackTheme();
                console.error(`Got invalid theme mode: ${mode}. Resetting to ${newMode}.`);
                mode = newMode;
            }
            document.documentElement.dataset.theme = mode;
            localStorage.setItem("theme", mode);
        }

        function cycleTheme() {
            const currentTheme = localStorage.getItem("theme") || getFallbackTheme();
            if (currentTheme === "dark") {
                setTheme("light");
            } else {
                setTheme("dark");
            }
        }

        function initTheme() {
            const currentTheme = localStorage.getItem("theme");
            currentTheme ? setTheme(currentTheme) : setTheme(getFallbackTheme());
        }

        function setupTheme() {
            // Attach event handlers for toggling themes
            const buttons = document.getElementsByClassName("theme-toggle");
            Array.from(buttons).forEach((btn) => {
                btn.addEventListener("click", cycleTheme);
            });
            initTheme();
        }

        setupTheme();
    });
}