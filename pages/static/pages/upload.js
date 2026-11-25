
/**
 * Inicializa el form de upload de archivos mediante drag and drop.
 *
 * Configura los eventos necesarios para seleccionar, validar y enviar
 * archivos desde una zona de carga o desde el selector de archivos.
 *
 * Permite subir solo un archivo a la vez, de tipo PDF, EPUB o TXT,
 * que no esté vacío y cuyo tamaño no supere los 10 MB.
 *
 * Muestra mensajes de error o de estado durante el proceso y deshabilita
 * el botón de envío cuando comienza la carga.
 *
 * Si el formulario no existe, retorna.
 *
 * @returns {void}
 */

(() => {
    const form = document.getElementById("drop-upload-form");
    if (!form) return;

    const zone = document.getElementById("drop-zone");
    const input = document.getElementById("drop-file");
    const status = document.getElementById("upload-status");

    /**
     * Valida un archivo antes de permitir su carga.
     *
     * Comprueba que el archivo exista, que su extensión sea PDF,
     * EPUB o TXT, que no esté vacío y que su tamaño no supere
     * los 10 MB.
     *
     * La validación del formato se realiza mediante la extensión
     * del nombre del archivo, no mediante su contenido.
     *
     * @param {File | undefined} file - Archivo que se validará.
     * @returns {string} Mensaje de error si el archivo no es válido,
     * o una cadena vacía si cumple las restricciones.
     *
     * @example
     * const error = validate(input.files[0]);
     * if (error) {
     *     status.textContent = error;
     * }
     */

    function validate(file) {
        if (!file) return "Selecciona un archivo.";

        const extension = file.name.split(".").pop().toLowerCase();

        if (!["pdf", "epub", "txt"].includes(extension)) {
            return "Solo se permiten archivos PDF, EPUB y TXT.";
        }

        if (file.size === 0) {
            return "El archivo está vacío.";
        }

        if (file.size > 10 * 1024 * 1024) {
            return "El archivo no debe superar los 10 MB.";
        }

        return "";
    }

    /**
     * Permite arrastrar archivos sobre la zona de carga.
     *
     * Evita el comportamiento predeterminado del navegador
     * y agrega una clase CSS para indicar visualmente que
     * se está arrastrando un archivo sobre la zona.
     *
     * @param {DragEvent} event - Evento de arrastre.
     * @returns {void}
     */

    zone.addEventListener("dragover", (event) => {
        event.preventDefault();
        zone.classList.add("is-dragging");
    });

    /**
     * Restaura el estado visual de la zona de carga cuando
     * el elemento arrastrado sale de ella.
     *
     * Elimina la clase de arrastre únicamente cuando el
     * elemento abandona la zona y no se desplaza hacia
     * uno de sus elementos internos.
     *
     * @param {DragEvent} event - Evento de salida de la zona.
     * @returns {void}
     */

    zone.addEventListener("dragleave", (event) => {
        if (!zone.contains(event.relatedTarget)) {
            zone.classList.remove("is-dragging");
        }
    });

    /**
     * Procesa el archivo soltado sobre la zona de carga.
     *
     * Evita la acción predeterminada del navegador y comprueba
     * que se haya soltado exactamente un archivo válido.
     *
     * Si la validación falla, muestra el error correspondiente.
     * En caso contrario, asigna el archivo al selector y solicita
     * el envío del formulario.
     *
     * @param {DragEvent} event - Evento que contiene los archivos soltados.
     * @returns {void}
     */

    zone.addEventListener("drop", (event) => {
        event.preventDefault();
        zone.classList.remove("is-dragging");

        const files = event.dataTransfer.files;

        if (files.length !== 1) {
            status.textContent = "Sube un archivo a la vez.";
            return;
        }

        const error = validate(files[0]);

        if (error) {
            status.textContent = error;
            return;
        }

        input.files = files;
        form.requestSubmit();
    });

    /**
     * Valida el archivo seleccionado mediante el selector.
     *
     * Actualiza el mensaje de estado con el resultado
     * de la validación del primer archivo seleccionado.
     *
     * @returns {void}
     */

    input.addEventListener("change", () => {
        status.textContent = validate(input.files[0]);
    });

    /**
     * Valida el archivo antes de enviar el formulario.
     *
     * Si el archivo no cumple las restricciones, cancela
     * el envío y muestra el mensaje de error.
     *
     * Si es válido, muestra el estado de carga y deshabilita
     * el botón de envío para evitar envíos repetidos.
     *
     * @param {SubmitEvent} event - Evento de envío del formulario.
     * @returns {void}
     */
    
    form.addEventListener("submit", (event) => {
        const error = validate(input.files[0]);

        if (error) {
            event.preventDefault();
            status.textContent = error;
            return;
        }

        status.textContent = "Subiendo…";
        form.querySelector('button[type="submit"]').disabled = true;
    });
})();
