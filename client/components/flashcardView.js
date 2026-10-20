/** Render a self contained document upload and flashcard study view. */
export function renderFlashcardView(container) {
  const apiBase = `${window.location.protocol}//${window.location.hostname || "127.0.0.1"}:8080`;
  const view = document.createElement("section");
  view.className = "component-flashcards";
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = ".pdf,.docx,.txt";
  fileInput.hidden = true;
  const uploadButton = document.createElement("button");
  uploadButton.className = "primary-button";
  uploadButton.type = "button";
  uploadButton.textContent = "Choose a file";
  const status = document.createElement("p");
  status.className = "section-description";
  status.setAttribute("role", "status");
  const deck = document.createElement("div");
  deck.className = "flashcard-grid";
  view.append(fileInput, uploadButton, status, deck);
  container.replaceChildren(view);
  uploadButton.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    uploadButton.disabled = true;
    status.textContent = `Reading ${file.name} and making your flashcards…`;
    deck.replaceChildren();

    try {
      const response = await fetch(`${apiBase}/flashcards`, { method: "POST", body: formData });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Server error (${response.status}).`);
      let cards = data.flashcards;
      if (typeof cards === "string") cards = JSON.parse(cards);
      if (!Array.isArray(cards) || cards.length === 0) throw new Error("No flashcards could be generated from this document.");
      status.textContent = `${cards.length} flashcards are ready. Select a card to reveal its answer.`;
      cards.forEach((card, index) => {
        const question = String(card.front || card.question || "Review this concept");
        const answer = String(card.back || card.answer || "No answer provided.");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "flashcard";
        const label = document.createElement("span");
        label.className = "flashcard-label";
        label.textContent = "QUESTION";
        const content = document.createElement("p");
        content.className = "flashcard-text";
        content.textContent = question;
        const footer = document.createElement("span");
        footer.className = "flashcard-meta";
        footer.textContent = `Card ${index + 1} · Tap to reveal`;
        button.append(label, content, footer);
        button.addEventListener("click", () => {
          const flipped = button.classList.toggle("is-flipped");
          label.textContent = flipped ? "ANSWER" : "QUESTION";
          content.textContent = flipped ? answer : question;
          content.classList.toggle("flashcard-answer", flipped);
          footer.textContent = `Card ${index + 1} · Tap to ${flipped ? "flip back" : "reveal"}`;
        });
        deck.append(button);
      });
    } catch (error) {
      status.textContent = error.message || "Could not generate flashcards. Check that the tutor server is running.";
    } finally {
      uploadButton.disabled = false;
      fileInput.value = "";
    }
  });
}
