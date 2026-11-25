
const root = document.documentElement;

/**
 * Aplica el tema de color seleccionado y actualiza el botón de cambio de tema.
 *
 * Establece el atributo data-theme en el elemento HTML raíz para permitir
 * que CSS seleccione el tema correspondiente.
 * Si el botón existe => actualiza su texto para indicar el tema opuesto
 * y establece aria-pressed para señalar si el modo claro está activo.
 *
 * No guarda la preferencia en localStorage; el manejador del evento
 * de clic se encarga de la persistencia por separado.
 *
 * @param {"light" | "dark"} theme - Tema a ser aplicado.
 * @returns {void}
 *
 * @example
 * applyTheme("light");
 */

function applyTheme(theme) {
    root.dataset.theme = theme;

    const button = document.getElementById("theme-toggle");

    if (button) {
        const isLight = theme === "light";

        button.textContent = isLight ? "Modo Oscuro" : "Modo Claro";
        button.setAttribute("aria-pressed", String(isLight));
    }
}

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
