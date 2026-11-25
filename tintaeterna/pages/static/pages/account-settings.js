
/**
 * Inicializa los controles de edición y previsualización de imágenes.
 *
 * Recorre todos los editores de imágenes disponibles y configura
 * sus elementos para seleccionar, visualizar y eliminar imágenes.
 *
 * Permite mostrar una vista previa del archivo seleccionado mediante
 * una URL temporal, reemplazando la imagen anterior cuando corresponda.
 *
 * También permite restablecer la vista previa, marcar la imagen para
 * su eliminación y mostrar un elemento de reemplazo cuando no existe
 * una imagen seleccionada.
 *
 * Libera las URL temporales anteriores para evitar mantener
 * recursos innecesarios en memoria.
 *
 * @returns {void}
 */

document.querySelectorAll('[data-image-editor]').forEach(editor => {
    const input = editor.querySelector('[data-image-input]');
    const clear = editor.querySelector('[data-image-clear]');
    const preview = editor.querySelector('[data-preview]');
    const placeholder = editor.querySelector('[data-placeholder]');
    let objectURL;

    /**
     * Restablece la vista previa de la imagen.
     *
     * Revoca la URL temporal existente, elimina la referencia
     * a la imagen y oculta el elemento de previsualización.
     *
     * Muestra el elemento de reemplazo para indicar que
     * no existe una imagen activa en la vista previa.
     *
     * @returns {void}
     */
    
    function resetPreview() {
        if (objectURL) URL.revokeObjectURL(objectURL);
        objectURL = null;
        preview.removeAttribute('src');
        preview.hidden = true;
        placeholder.hidden = false;
    }

    if (clear.checked) resetPreview();

    /**
     * Abre el selector de archivos para cambiar la imagen.
     *
     * Activa mediante código el campo de selección
     * cuando el usuario presiona el botón correspondiente.
     *
     * @returns {void}
     */
    editor.querySelector('[data-change-image]').addEventListener('click', () => input.click());

    /**
     * Actualiza la vista previa cuando se selecciona una nueva imagen.
     *
     * Comprueba que exista un archivo seleccionado y libera
     * la URL temporal de la imagen anterior, si corresponde.
     *
     * Genera una nueva URL temporal para mostrar la imagen,
     * oculta el elemento de reemplazo y desmarca la opción
     * de eliminación.
     *
     * @returns {void}
     */
    input.addEventListener('change', () => {
        if (!input.files.length) return;
        if (objectURL) URL.revokeObjectURL(objectURL);
        objectURL = URL.createObjectURL(input.files[0]);
        preview.src = objectURL;
        preview.hidden = false;
        placeholder.hidden = true;
        clear.checked = false;
    });

    /**
     * Elimina la imagen seleccionada y restablece la vista previa.
     *
     * Limpia el campo de selección de archivos, marca la opción
     * de eliminación de la imagen y ejecuta el restablecimiento
     * de los elementos visuales.
     *
     * @returns {void}
     */
    editor.querySelector('[data-reset-image]').addEventListener('click', () => {
        input.value = '';
        clear.checked = true;
        resetPreview();
    });
});
