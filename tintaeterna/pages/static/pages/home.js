
const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#story-search");
const cards = document.querySelectorAll(".story-card");
const sections = document.querySelectorAll(".story-section");
const noResults = document.querySelector("#no-results");

//Elementos para tags
const tagDropdown = document.querySelector("#tag-dropdown");
const tagCheckboxes = document.querySelectorAll(".tag-checkbox");

/**
 * Cierra el menú desplegable de etiquetas cuando se hace clic fuera de él.
 *
 * Comprueba si el elemento seleccionado pertenece al menú desplegable.
 * Si el clic ocurre fuera de este, modifica su estado para cerrarlo.
 *
 * @param {MouseEvent} event - Evento de clic en el documento.
 * @returns {void}
 */
document.addEventListener("click", (event) => {
    if (!tagDropdown.contains(event.target)) tagDropdown.open = false;
});

/**
 * Permite cerrar el menú de etiquetas mediante el teclado.
 *
 * Detecta si el usuario presiona la tecla Escape y, en ese caso,
 * cierra el menú desplegable y devuelve el foco a su elemento summary.
 *
 * @param {KeyboardEvent} event - Evento de pulsación de tecla.
 * @returns {void}
 */
tagDropdown.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        tagDropdown.open = false;
        tagDropdown.querySelector("summary").focus();
    }
});

/**
 * Normaliza un texto para compararlo sin distinguir tildes ni mayúsculas.
 *
 * Descompone cada carácter en su letra base y sus marcas diacríticas (NFD),
 * elimina esas marcas (tildes, diéresis y la tilde de la ñ) y convierte
 * el resultado a minúsculas. Si el valor recibido es null o undefined,
 * lo trata como un texto vacío.
 *
 * Se aplica tanto al texto buscado como al texto de cada tarjeta, de modo
 * que "Señor", "SEÑOR" y "senor" produzcan el mismo resultado.
 *
 * @param {string} text - Texto que se desea normalizar.
 * @returns {string} Texto en minúsculas y sin tildes.
 *
 * @example
 * normalizeText("Señor Ñandú"); // "senor nandu"
 */
function normalizeText(text) {
    return String(text ?? "")
        .normalize("NFD")
        .replace(/\p{M}/gu, "")
        .toLowerCase();
}

/**
 * Filtra las historias según el texto de búsqueda y las etiquetas seleccionadas.
 *
 * Obtiene el texto ingresado por el usuario, lo normaliza con normalizeText
 * (minúsculas y sin tildes) y elimina los espacios al inicio y al final.
 * El texto de cada tarjeta se normaliza de la misma manera antes de compararlo.
 *
 * También obtiene las etiquetas seleccionadas y actualiza su contador.
 * Una historia se muestra únicamente cuando coincide con el texto
 * buscado y contiene al menos una de las etiquetas seleccionadas.
 *
 * Si no se seleccionan etiquetas, el filtrado se realiza solamente
 * mediante el texto de búsqueda.
 *
 * Oculta las historias que no cumplen los criterios y las secciones
 * que no contienen historias visibles. Si no existen coincidencias,
 * muestra el mensaje correspondiente.
 *
 * @returns {void}
 *
 * @example
 * filterStories();
 */
function filterStories() {
    const query = normalizeText(searchInput.value).trim();
    
    // Obtener los valores de los tags que el usuario haya seleccionado
    const selectedTags = Array.from(tagCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    document.getElementById("tag-count").textContent = selectedTags.length ? `(${selectedTags.length})` : "";
    let visibleCount = 0;

    cards.forEach((card) => {
        const textMatches = normalizeText(card.dataset.search).includes(query);

        const cardTags = (card.dataset.tags || "").trim().split(/\s+/);
        const tagMatches = selectedTags.length === 0 || selectedTags.some(tag => cardTags.includes(tag));

        const matches = textMatches && tagMatches;
        
        card.hidden = !matches;

        if (matches) {
            visibleCount++;
        }
    });

    sections.forEach((section) => {
        const visibleCard = section.querySelector(
            ".story-card:not([hidden])"
        );

        section.hidden = !visibleCard;
    });

    noResults.hidden = visibleCount > 0;
}

/**
 * Procesa el envío del formulario de búsqueda de historias.
 *
 * Evita el comportamiento predeterminado del formulario
 * y ejecuta el filtrado utilizando los criterios actuales.
 *
 * @param {SubmitEvent} event - Evento de envío del formulario.
 * @returns {void}
 */
searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    filterStories();
});

/**
 * Actualiza los resultados de búsqueda mientras el usuario escribe.
 *
 * Ejecuta el filtrado cada vez que cambia el contenido
 * del campo de búsqueda.
 *
 * @returns {void}
 */
searchInput.addEventListener("input", filterStories);

/**
 * Actualiza los resultados cuando cambia la selección de etiquetas.
 *
 * Asocia el evento change a cada casilla de selección para
 * aplicar inmediatamente los filtros cuando el usuario
 * marca o desmarca una etiqueta.
 *
 * @returns {void}
 */
// Filtrar instantáneamente cada vez que el usuario marca o desmarca un tag
tagCheckboxes.forEach(cb => cb.addEventListener("change", filterStories));
