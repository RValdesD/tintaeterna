
const addChapter = document.getElementById('add-chapter');
const total = document.getElementById('id_chapters-TOTAL_FORMS');
const rows = document.getElementById('chapter-rows');
const template = document.getElementById('chapter-empty');

/**
 * Permite agregar dinámicamente nuevos capítulos al formulario.
 *
 * Comprueba que existan los elementos necesarios y configura
 * el botón para agregar nuevas filas de capítulos.
 *
 * Al presionar el botón, obtiene el número actual de formularios,
 * genera una nueva fila a partir de una plantilla HTML y reemplaza
 * el identificador __prefix__ por el índice correspondiente.
 *
 * Actualiza el contador de formularios y establece el foco
 * en el primer campo de entrada del capítulo agregado.
 *
 * Limita la cantidad de formularios a un máximo de 100
 * y deshabilita el botón cuando se alcanza dicho límite.
 *
 * @returns {void}
 */
if (addChapter && total && rows && template) {
    addChapter.addEventListener('click', () => {
        const index = Number(total.value);
        if (index >= 100) return;
        const html = template.innerHTML.replaceAll('__prefix__', String(index));
        rows.insertAdjacentHTML('beforeend', html);
        total.value = index + 1;
        rows.lastElementChild.querySelector('input').focus();
        addChapter.disabled = index + 1 >= 100;
    });
}

