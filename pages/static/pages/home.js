const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#story-search");
const cards = document.querySelectorAll(".story-card");
const sections = document.querySelectorAll(".story-section");
const noResults = document.querySelector("#no-results");

//Elementos para tags
const tagDropdown = document.querySelector("#tag-dropdown");
const tagCheckboxes = document.querySelectorAll(".tag-checkbox");

// Mostrar menú al presionar la barra de búsqueda
searchInput.addEventListener("focus", () => {
    tagDropdown.classList.remove("hidden");
});

// Ocultar menú al hacer clic fuera del formulario
document.addEventListener("click", (event) => {
    if (!searchForm.contains(event.target)) {
        tagDropdown.classList.add("hidden");
    }
});

function filterStories() {
    const query = searchInput.value.trim().toLowerCase();
    
    // Obtener los valores de los tags que el usuario haya seleccionado
    const selectedTags = Array.from(tagCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    let visibleCount = 0;

    cards.forEach((card) => {
        const textMatches = card.dataset.search
            .toLowerCase()
            .includes(query);


        const cardTags = card.dataset.tags ? card.dataset.tags.toLowerCase() : "";
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