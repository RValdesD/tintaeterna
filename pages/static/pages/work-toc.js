
import { textSections } from "./text-sections.js";

const root = document.getElementById("work-toc");
const list = document.getElementById("toc-list");
const status = document.getElementById("toc-status");

/**
 * Crea y agrega un enlace de navegación al índice del documento.
 *
 * Genera un elemento de lista que contiene un enlace hacia el lector.
 * Construye la URL utilizando la dirección configurada en el elemento
 * raíz y agrega el parámetro de navegación correspondiente.
 *
 * @param {HTMLElement} parent - Elemento donde se agregará el enlace.
 * @param {string} label - Texto que se mostrará en el enlace.
 * @param {string} key - Nombre del parámetro de navegación.
 * @param {string | number} value - Valor del parámetro de navegación.
 * @returns {HTMLLIElement} Elemento de lista creado.
 *
 * @example
 * addLink(list, "Página 5", "page", 5);
 */
function addLink(parent, label, key, value) {
    const li = document.createElement("li");
    const link = document.createElement("a");
    const url = new URL(root.dataset.reader, window.location.origin);
    url.searchParams.set(key, String(value));
    link.href = url.href;
    link.textContent = label;
    li.append(link);
    parent.append(li);
    return li;
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
 * await script("https://example.com/library.js");
 */
function script(url) {
    return new Promise((resolve, reject) => {
        const tag = document.createElement("script");
        tag.src = url;
        tag.onload = resolve;
        tag.onerror = reject;
        document.head.append(tag);
    });
}

let resource;

/**
 * Inicializa y genera el índice de navegación del documento.
 *
 * Obtiene el archivo desde la URL configurada en el elemento raíz,
 * utilizando las credenciales de la sesión actual.
 *
 * Según el formato del archivo, construye el índice:
 * - PDF: utiliza los marcadores del documento y sus páginas asociadas.
 * - EPUB: utiliza la tabla de contenidos y sus subcapítulos.
 * - TXT: divide el texto en secciones de lectura.
 *
 * Si el PDF no contiene enlaces de navegación válidos, genera
 * un índice alternativo con todas sus páginas.
 *
 * Si ocurre un error, elimina los elementos del índice y muestra
 * un mensaje indicando que no fue posible cargarlo.
 *
 * Al finalizar, libera los recursos del documento cuando corresponde.
 */

try {
    const response = await fetch(root.dataset.file, { credentials: "same-origin" });
    if (!response.ok || response.redirected) throw new Error("File unavailable");
    const data = await response.arrayBuffer();

    if (root.dataset.format === "pdf") {
        const pdfjs = await import("https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs");
        pdfjs.GlobalWorkerOptions.workerSrc = "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs";

        const pdf = await pdfjs.getDocument({ data, isEvalSupported: false }).promise;
        resource = pdf;
        const outline = await pdf.getOutline();

        /**
         * Genera recursivamente las entradas del índice de un PDF.
         *
         * Recorre los marcadores del documento e intenta resolver
         * sus destinos para obtener los números de página.
         *
         * Cuando un destino es válido, crea un enlace hacia la página
         * correspondiente. Si no puede resolverse, conserva el título
         * como un elemento de lista sin enlace.
         *
         * Los marcadores anidados se representan mediante listas
         * secundarias para mantener la jerarquía original.
         *
         * @param {Object[]} items - Marcadores del PDF que se procesarán.
         * @param {HTMLElement} parent - Elemento donde se agregarán las entradas.
         * @returns {Promise<void>}
         */
        
        async function entries(items, parent) {
            for (const item of items) {
                let destination;
                let page;

                try {
                    destination = typeof item.dest === "string" ? await pdf.getDestination(item.dest) : item.dest;
                    if (destination?.length) {
                        page = typeof destination[0] === "number" ? destination[0] + 1 : await pdf.getPageIndex(destination[0]) + 1;
                    }
                } catch { /* Keep a non-navigable heading for invalid destinations. */ }

                let li;

                if (Number.isInteger(page) && page >= 1 && page <= pdf.numPages) {
                    li = addLink(parent, item.title || `Página ${page}`, "page", page);
                } else {
                    li = document.createElement("li");
                    li.textContent = item.title || "Sección";
                    parent.append(li);
                }

                if (item.items?.length) {
                    const children = document.createElement("ul");
                    li.append(children);
                    await entries(item.items, children);
                }
            }
        }

        if (outline?.length) await entries(outline, list);

        if (!list.querySelector("a")) {
            list.replaceChildren();
            for (let page = 1; page <= pdf.numPages; page++) addLink(list, `Página ${page}`, "page", page);
            status.textContent = "Sin índice de capítulos: se muestran las páginas.";
        } else status.textContent = "";

    } else if (root.dataset.format === "epub") {
        await script("https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js");
        await script("https://cdn.jsdelivr.net/npm/epubjs@0.3.93/dist/epub.min.js");

        const book = window.ePub(data);
        resource = book;
        const navigation = await book.loaded.navigation;
        let index = 0;

        /**
         * Genera recursivamente las entradas del índice de un EPUB.
         *
         * Recorre la tabla de contenidos y crea enlaces hacia
         * los capítulos del documento, asignando un índice numérico
         * consecutivo a cada entrada.
         *
         * Mantiene la jerarquía de capítulos y subcapítulos
         * mediante listas anidadas.
         *
         * Si una entrada no tiene etiqueta, utiliza un nombre
         * de sección generado automáticamente.
         *
         * @param {Object[]} items - Elementos de la tabla de contenidos.
         * @param {HTMLElement} parent - Elemento donde se agregarán las entradas.
         * @returns {void}
         */
        function entries(items, parent) {
            for (const item of items) {
                const li = addLink(parent, item.label?.trim() || `Sección ${index + 1}`, "chapter", index++);

                if (item.subitems?.length) {
                    const children = document.createElement("ul");
                    li.append(children);
                    entries(item.subitems, children);
                }
            }
        }

        entries(navigation.toc, list);
        status.textContent = list.children.length ? "" : "Este EPUB no incluye un índice. Usa Continuar lectura.";

    } else {
        const sections = textSections(new TextDecoder("utf-8", { fatal: true }).decode(data));
        sections.forEach((_, i) => addLink(list, `Sección ${i + 1}`, "page", i + 1));
        status.textContent = "Texto dividido en secciones de lectura.";
    }

} catch {
    list.replaceChildren();
    status.textContent = "No se pudo cargar el índice. Puedes intentar abrir el lector con Continuar lectura.";
} finally {
    if (resource) await resource.destroy();
}
