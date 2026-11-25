
import { textSections } from "./text-sections.js";

const root = document.getElementById("reader");
const area = document.getElementById("book");
const status = document.getElementById("status");
const position = document.getElementById("position");
const previous = document.getElementById("previous");
const next = document.getElementById("next");
const bookmarkForm = document.getElementById("bookmark-form");
const saveButton = document.getElementById("save-bookmark");
const bookmarkStatus = document.getElementById("bookmark-status");
const savedLocation = JSON.parse(document.getElementById("saved-location").textContent);
const navigation = new URLSearchParams(window.location.search);
const requestedPage = navigation.get("page");
const pageStart = requestedPage && /^[1-9][0-9]{0,6}$/.test(requestedPage) ? Number(requestedPage) : Number(savedLocation) || 1;
const requestedChapter = navigation.get("chapter");
let page = 1, total = 1, busy = false, draw, rendition;
let currentLocation = "", saving = false;

/**
 * Procesa el envío del formulario para guardar un marcador de lectura.
 *
 * Evita el envío tradicional del formulario y comprueba que exista una
 * ubicación válida y que no haya operaciones de navegación o guardado
 * en curso.
 *
 * Envía la ubicación actual al servidor mediante una solicitud POST
 * y muestra un mensaje de confirmación o error según el resultado.
 * Durante el guardado, actualiza el estado de los controles.
 *
 * @param {SubmitEvent} event - Evento de envío del formulario.
 * @returns {Promise<void>}
 */
if (bookmarkForm) bookmarkForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!currentLocation || busy || saving) return;
    saving = true;
    controls();
    const payload = new FormData(bookmarkForm);
    payload.set("location", currentLocation);
    try {
        const response = await fetch(bookmarkForm.action, {
            method: "POST", body: payload, credentials: "same-origin",
        });
        if (!response.ok || response.redirected) throw new Error("Save failed");
        await response.json();
        bookmarkStatus.textContent = "Marcador guardado. Se abrirá aquí cuando vuelvas.";
    } catch {
        bookmarkStatus.textContent = "No se pudo guardar. Comprueba tu conexión y que sigues conectado.";
    } finally {
        saving = false;
        controls();
    }
});

/**
 * Actualiza la disponibilidad de los controles del lector.
 *
 * Deshabilita el botón de guardado cuando existe una operación en curso
 * o no hay una ubicación válida para guardar.
 *
 * También deshabilita los botones de navegación cuando el lector
 * está ocupado o se encuentra en los límites de las páginas disponibles.
 *
 * @returns {void}
 */
function controls() {
    if (saveButton) saveButton.disabled = busy || saving || !currentLocation;
    previous.disabled = busy || page <= 1;
    next.disabled = busy || page >= total;
}

/**
 * Navega entre las páginas o secciones del documento.
 *
 * Para archivos EPUB, utiliza los métodos de navegación de la
 * representación del libro. Para PDF y TXT, calcula la nueva página,
 * actualiza el contenido mostrado y registra la ubicación actual.
 *
 * Impide ejecutar varias operaciones de navegación simultáneamente
 * y muestra un mensaje si ocurre un error.
 *
 * @param {number} delta - Desplazamiento de navegación.
 * Un valor negativo retrocede y uno positivo avanza.
 * @returns {Promise<void>}
 */
async function move(delta) {
    if (busy) return;
    busy = true;
    controls();
    try {
        if (rendition) {
            await (delta < 0 ? rendition.prev() : rendition.next());
        } else {
            page = Math.max(1, Math.min(total, page + delta));
            await draw();
            currentLocation = String(page);
            position.textContent = `Página ${page} de ${total}`;
        }
        status.textContent = "";
    } catch {
        status.textContent = "No se pudo mostrar esta página.";
    } finally {
        busy = false;
        controls();
    }
}

/**
 * Carga dinámicamente un archivo JavaScript externo.
 *
 * Crea un elemento script con la URL indicada y lo incorpora
 * al encabezado del documento HTML.
 *
 * La promesa se resuelve cuando el script termina de cargarse
 * y se rechaza si ocurre un error durante la carga.
 *
 * @param {string} url - Dirección URL del script que se cargará.
 * @returns {Promise<void>} Promesa que indica el resultado
 * de la carga del script.
 *
 * @example
 * await loadScript("https://example.com/library.js");
 */
function loadScript(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.append(script);
    });
}

/**
 * Configura los botones para retroceder y avanzar una página.
 *
 * Cada botón solicita un desplazamiento de una posición mediante
 * la función move().
 */
previous.addEventListener("click", () => move(-1));
next.addEventListener("click", () => move(1));

/**
 * Inicializa el lector y carga el documento solicitado.
 *
 * Obtiene el archivo desde la URL configurada en el elemento raíz,
 * utilizando las credenciales de la sesión actual.
 *
 * Según el formato, configura el sistema de visualización:
 * - PDF: utiliza PDF.js para renderizar páginas en un canvas.
 * - TXT: decodifica el texto y lo divide en secciones.
 * - EPUB: utiliza JSZip y EPUB.js para mostrar el libro.
 *
 * Recupera la posición guardada o la ubicación solicitada mediante
 * los parámetros de navegación cuando corresponde.
 *
 * Si ocurre un error durante la carga, muestra un mensaje
 * y deshabilita los controles de navegación y guardado.
 */

try {
    const response = await fetch(root.dataset.url, { credentials: "same-origin" });
    if (!response.ok || response.redirected) throw new Error("File unavailable");
    const data = await response.arrayBuffer();

    if (root.dataset.format === "pdf") {
        const pdfjs = await import("https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs");
        pdfjs.GlobalWorkerOptions.workerSrc =
            "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs";

        const pdf = await pdfjs.getDocument({ data, isEvalSupported: false }).promise;
        total = pdf.numPages;
        const canvas = document.createElement("canvas");
        area.append(canvas);

        /**
         * Renderiza la página actual del documento PDF.
         *
         * Obtiene la página seleccionada, calcula sus dimensiones
         * con una escala de 1.5 y dibuja su contenido en el canvas.
         *
         * Actualiza el atributo aria-label para identificar
         * la página mostrada mediante tecnologías de asistencia.
         *
         * @returns {Promise<void>}
         */

        draw = async () => {
            const current = await pdf.getPage(page);
            const viewport = current.getViewport({ scale: 1.5 });
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            await current.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
            canvas.setAttribute("aria-label", `Página ${page}`);
        };

        page = Math.max(1, Math.min(total, pageStart));
        await move(0);

    } else if (root.dataset.format === "txt") {
        const text = new TextDecoder("utf-8", { fatal: true }).decode(data);
        const sections = textSections(text);
        total = Math.max(1, sections.length);
        const content = document.createElement("pre");
        area.append(content);

        /**
         * Muestra la sección actual del documento de texto.
         *
         * Obtiene el fragmento correspondiente a la página
         * seleccionada y actualiza el contenido del elemento pre.
         *
         * Si la sección no existe, muestra una cadena vacía.
         *
         * @returns {Promise<void>}
         */

        draw = async () => { content.textContent = sections[page - 1] || ""; };

        page = Math.max(1, Math.min(total, pageStart));
        await move(0);

    } else {
        await loadScript("https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js");
        await loadScript("https://cdn.jsdelivr.net/npm/epubjs@0.3.93/dist/epub.min.js");

        area.classList.add("epub");
        const book = window.ePub(data);

        rendition = book.renderTo(area, {
            width: "100%", height: "100%", flow: "paginated", spread: "none",
            allowScriptedContent: false,
        });

        /**
         * Actualiza la ubicación de lectura cuando cambia
         * la posición mostrada dentro del documento EPUB.
         *
         * Guarda la ubicación mediante un identificador CFI,
         * que permite recuperar la posición aunque cambien
         * las dimensiones de la pantalla o el tamaño de fuente.
         *
         * También actualiza el indicador de sección y el
         * estado de los controles de navegación.
         *
         * @param {Object} location - Información de ubicación
         * proporcionada por EPUB.js.
         * @returns {void}
         */

        rendition.on("relocated", (location) => {
            // EPUB CFI remains stable when the viewport/font changes.
            currentLocation = location.start.cfi;
            page = location.atStart ? 1 : 2;
            total = location.atEnd ? page : page + 1;
            position.textContent = `Sección ${location.start.index + 1}`;
            controls();
        });

        await book.loaded.navigation;
        let chapterTarget;

        if (requestedChapter !== null && /^[0-9]{1,6}$/.test(requestedChapter)) {
            const chapters = [];

            /**
             * Recorre recursivamente la tabla de contenidos del EPUB.
             *
             * Almacena las direcciones de los capítulos en el mismo
             * orden en que aparecen en la estructura de navegación,
             * incluyendo los subcapítulos.
             *
             * @param {Object[]} items - Elementos de navegación
             * que se recorrerán.
             * @returns {void}
             */
            const visit = (items) => items.forEach(item => {
                chapters.push(item.href);
                visit(item.subitems || []);
            });

            visit(book.navigation.toc);
            chapterTarget = chapters[Number(requestedChapter)];
        }

        try {
            await rendition.display(chapterTarget || savedLocation || undefined);
        } catch (error) {
            if (!savedLocation && !chapterTarget) throw error;
            await rendition.display();
            if (bookmarkStatus) bookmarkStatus.textContent = "El marcador ya no es válido; se abrió el inicio.";
        }

        status.textContent = "";
        controls();
    }

} catch (error) {
    status.textContent = "No se pudo abrir el archivo. Comprueba tu sesión, conexión y el formato. Puedes descargarlo.";
    previous.disabled = next.disabled = true;
    if (saveButton) saveButton.disabled = true;
}
