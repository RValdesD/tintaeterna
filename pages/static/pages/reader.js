const root = document.getElementById("reader");
const area = document.getElementById("book");
const status = document.getElementById("status");
const position = document.getElementById("position");
const previous = document.getElementById("previous");
const next = document.getElementById("next");
let page = 1, total = 1, busy = false, draw, rendition;

function controls() {
    previous.disabled = busy || page <= 1;
    next.disabled = busy || page >= total;
}

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

function loadScript(url) {
    return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = url;
        script.onload = resolve;
        script.onerror = reject;
        document.head.append(script);
    });
}

previous.addEventListener("click", () => move(-1));
next.addEventListener("click", () => move(1));

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
        draw = async () => {
            const current = await pdf.getPage(page);
            const viewport = current.getViewport({ scale: 1.5 });
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            await current.render({ canvasContext: canvas.getContext("2d"), viewport }).promise;
            canvas.setAttribute("aria-label", `Página ${page}`);
        };
        await move(0);
    } else if (root.dataset.format === "txt") {
        const text = new TextDecoder("utf-8", { fatal: true }).decode(data);
        // Stable sections; avoid splitting a word when possible.
        const sections = [];
        let start = 0;
        while (start < text.length) {
            let end = Math.min(start + 3000, text.length);
            if (end < text.length) {
                const space = text.lastIndexOf(" ", end);
                if (space > start + 1500) end = space + 1;
            }
            sections.push(text.slice(start, end));
            start = end;
        }
        total = Math.max(1, sections.length);
        const content = document.createElement("pre");
        area.append(content);
        draw = async () => { content.textContent = sections[page - 1] || ""; };
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
        rendition.on("relocated", (location) => {
            // EPUB pages reflow: use boundary flags for navigation.
            page = location.atStart ? 1 : 2;
            total = location.atEnd ? page : page + 1;
            position.textContent = `Sección ${location.start.index + 1}`;
            controls();
        });
        await rendition.display();
        status.textContent = "";
        controls();
    }
} catch (error) {
    status.textContent = "No se pudo abrir el archivo. Comprueba tu sesión, conexión y el formato. Puedes descargarlo.";
    previous.disabled = next.disabled = true;
}
