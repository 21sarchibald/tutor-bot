/**
 * Component: FlashcardView
 * Uploads document files to the FastAPI server and renders interactive flashcards.
 */
export function renderFlashcardView(container) {
    container.innerHTML = `
    <div style="margin-bottom: 2rem;">
      <h3>Upload File (.pdf, .docx, .txt)</h3>
      <input type="file" id="file-input" accept=".pdf,.docx,.txt" />
      <button id="upload-btn" style="padding:0.5rem 1rem; background:#3b82f6; color:white; border:none; border-radius:6px; cursor:pointer;">Generate Flashcards</button>
    </div>
    <div id="deck-area" class="flashcard-deck"></div>
  `;

    const uploadBtn = container.querySelector("#upload-btn");
    const fileInput = container.querySelector("#file-input");
    const deckArea = container.querySelector("#deck-area");

    uploadBtn.addEventListener("click", async () => {
        const file = fileInput.files[0];
        if (!file) return alert("Please select a file first.");

        const formData = new FormData();
        formData.append("file", file);

        deckArea.innerHTML = "<p>Processing document and generating flashcards...</p>";

        try {
            const response = await fetch("http://127.0.0.1:8000/flashcards", {
                method: "POST",
                body: formData
            });
            const data = await response.json();

            if (data.flashcards && data.flashcards.length > 0) {
                renderDeck(data.flashcards, deckArea);
            } else {
                deckArea.innerHTML = "<p>No flashcards could be generated from this document.</p>";
            }
        } catch (err) {
            deckArea.innerHTML = `<p>Error uploading file: ${err.message}</p>`;
        }
    });
}

function renderDeck(cards, container) {
    let currentIndex = 0;

    function showCard() {
        const card = cards[currentIndex];
        container.innerHTML = `
      <div class="card" id="active-card">
        <div class="card-inner" id="card-content">
          <strong>Front:</strong><br>${card.front}
        </div>
      </div>
      <div>
        <button id="prev-btn" ${currentIndex === 0 ? "disabled" : ""}>Previous</button>
        <span>Card ${currentIndex + 1} of ${cards.length}</span>
        <button id="next-btn" ${currentIndex === cards.length - 1 ? "disabled" : ""}>Next</button>
      </div>
    `;

        let showingFront = true;
        const cardContent = container.querySelector("#card-content");
        container.querySelector("#active-card").addEventListener("click", () => {
            showingFront = !showingFront;
            cardContent.innerHTML = showingFront
                ? `<strong>Front:</strong><br>${card.front}`
                : `<strong>Back:</strong><br>${card.back}`;
        });

        container.querySelector("#prev-btn").addEventListener("click", () => {
            if (currentIndex > 0) { currentIndex--; showCard(); }
        });
        container.querySelector("#next-btn").addEventListener("click", () => {
            if (currentIndex < cards.length - 1) { currentIndex++; showCard(); }
        });
    }

    showCard();
}