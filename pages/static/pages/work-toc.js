import { textSections } from "./text-sections.js";
const root = document.getElementById("work-toc");
const list = document.getElementById("toc-list");
const status = document.getElementById("toc-status");
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
