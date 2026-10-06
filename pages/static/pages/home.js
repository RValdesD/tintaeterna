const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#story-search");
const cards = document.querySelectorAll(".story-card");
const sections = document.querySelectorAll(".story-section");
const noResults = document.querySelector("#no-results");

function filterStories() {
    const query = searchInput.value.trim().toLowerCase();
    let visibleCount = 0;

    cards.forEach((card) => {
        const matches = card.dataset.search
            .toLowerCase()
            .includes(query);

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