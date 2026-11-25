
/**
 * Divide un texto en secciones de hasta 3000 caracteres.
 *
 * Recorre el texto y genera fragmentos consecutivos, procurando
 * realizar los cortes en espacios para evitar dividir palabras.
 *
 * Si una sección alcanza el límite de 3000 caracteres, busca
 * el último espacio disponible antes de dicho límite.
 * Si el espacio se encuentra después de los primeros 1500
 * caracteres de la sección, realiza el corte en esa posición.
 * De lo contrario, corta exactamente en el límite establecido.
 *
 * Si el texto está vacío, devuelve un arreglo que contiene
 * una única cadena vacía.
 *
 * @param {string} text - Texto que se dividirá en secciones.
 * @returns {string[]} Arreglo de secciones que conservan
 * el contenido y orden del texto original.
 *
 * @example
 * const sections = textSections("Texto de ejemplo");
 * console.log(sections); // ["Texto de ejemplo"]
 */

export function textSections(text) {
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
    return sections.length ? sections : [""];
}
