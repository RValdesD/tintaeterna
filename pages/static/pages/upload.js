(() => {
    const form = document.getElementById("drop-upload-form");
    if (!form) return;

    const zone = document.getElementById("drop-zone");
    const input = document.getElementById("drop-file");
    const status = document.getElementById("upload-status");

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

    zone.addEventListener("dragover", (event) => {
        event.preventDefault();
        zone.classList.add("is-dragging");
    });

    zone.addEventListener("dragleave", (event) => {
        if (!zone.contains(event.relatedTarget)) {
            zone.classList.remove("is-dragging");
        }
    });

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

    input.addEventListener("change", () => {
        status.textContent = validate(input.files[0]);
    });

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