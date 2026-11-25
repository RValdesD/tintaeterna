const root = document.documentElement;

function applyTheme(theme) {
    root.dataset.theme = theme;

    const button = document.getElementById("theme-toggle");

    if (button) {
        const isLight = theme === "light";

        button.textContent = isLight ? "Modo Oscuro" : "Modo Claro";
        button.setAttribute("aria-pressed", String(isLight));
    }
}

let savedTheme = "dark";

try {
    savedTheme = localStorage.getItem("theme") || "dark";
} catch {
}

applyTheme(savedTheme === "light" ? "light" : "dark");

document.addEventListener("DOMContentLoaded", () => {
    applyTheme(root.dataset.theme);

    document.getElementById("theme-toggle")?.addEventListener("click", () => {
        const nextTheme =
            root.dataset.theme === "light" ? "dark" : "light";

        applyTheme(nextTheme);

        try {
            localStorage.setItem("theme", nextTheme);
        } catch {
            
        }
    });
});