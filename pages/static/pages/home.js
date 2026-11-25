const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#story-search");
const cards = document.querySelectorAll(".story-card");
const sections = document.querySelectorAll(".story-section");
const noResults = document.querySelector("#no-results");

//Elementos para tags
const tagDropdown = document.querySelector("#tag-dropdown");
const tagCheckboxes = document.querySelectorAll(".tag-checkbox");

// Native details supports keyboard and touch without a custom focus menu.
document.addEventListener("click", (event) => {
    if (!tagDropdown.contains(event.target)) tagDropdown.open = false;
});
tagDropdown.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        tagDropdown.open = false;
        tagDropdown.querySelector("summary").focus();
    }
});

function normalizeText(text) {
    return String(text ?? "")
        .normalize("NFD")
        .replace(/\p{M}/gu, "")
        .toLowerCase();

}

function filterStories() {
    const terms = normalizeText(searchInput.value).split(/\s+/).filter(Boolean);
    
    // Obtener los valores de los tags que el usuario haya seleccionado
    const selectedTags = Array.from(tagCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    document.getElementById("tag-count").textContent = selectedTags.length ? `(${selectedTags.length})` : "";
    let visibleCount = 0;

    cards.forEach((card) => {
        const text = normalizeText(card.dataset.search);
        const textMatches = terms.every(term => text.includes(term));
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

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    filterStories();
});

searchInput.addEventListener("input", filterStories);
// Filtrar instantáneamente cada vez que el usuario marca o desmarca un tag
tagCheckboxes.forEach(cb => cb.addEventListener("change", filterStories));