
/**
 * Inicializa los controles de los menús desplegables de usuario.
 *
 * Recorre todos los menús de cuenta disponibles y configura
 * los eventos necesarios para controlar su apertura y cierre.
 *
 * Permite cerrar cada menú al hacer clic fuera de él o al
 * presionar la tecla Escape.
 *
 * @returns {void}
 */
document.querySelectorAll(".account-menu").forEach((menu) => {

    /**
     * Cierra el menú de usuario cuando se hace clic fuera de él.
     *
     * Comprueba si el elemento seleccionado pertenece al menú.
     * Si el clic ocurre fuera de este, modifica su estado para cerrarlo.
     *
     * @param {MouseEvent} event - Evento de clic en el documento.
     * @returns {void}
     */
    document.addEventListener("click", (event) => {
        if (!menu.contains(event.target)) menu.open = false;
    });

    /**
     * Permite cerrar el menú de usuario mediante el teclado.
     *
     * Detecta si el usuario presiona la tecla Escape y, en ese caso,
     * cierra el menú desplegable y devuelve el foco a su elemento summary.
     *
     * @param {KeyboardEvent} event - Evento de pulsación de tecla.
     * @returns {void}
     */
    menu.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            menu.open = false;
            menu.querySelector("summary").focus();
        }
    });
});
