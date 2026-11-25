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
