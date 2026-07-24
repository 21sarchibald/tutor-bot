// ===============================
// DOM ELEMENTS - CHAT & SIDEBAR
// ===============================
const sideBtn = document.querySelector("#sidebarBtn");
const sideBar = document.querySelector("#sidebar");
const chatRoom = document.querySelector("#chatRoom");
const topBar = document.querySelector("#top");
const userInput = document.querySelector("#userinput");
const userPrompt = document.querySelector("#userPrompt");
const submitBtn = document.querySelector("#submit");
const closeBtn = document.querySelector(".close");

// Toggle sidebar event listeners
if (sideBtn) sideBtn.addEventListener("click", openAndClose);
if (closeBtn) closeBtn.addEventListener("click", openAndClose);

// ===============================
// CHAT FUNCTIONALITY
// ===============================
if (submitBtn && userPrompt && chatRoom) {
  submitBtn.addEventListener("click", async () => {
    let cleanedInput = userPrompt.value.trim();
    if (cleanedInput !== "") {
      // Render user prompt
      chatRoom.innerHTML += `
        <p class="userPromptDisplay">${cleanedInput}</p>`;
      userPrompt.value = "";
      chatRoom.scrollTop = chatRoom.scrollHeight;

      // Render loading state placeholder
      const loadingEl = document.createElement("p");
      loadingEl.textContent = "Tutorbot is thinking...";
      loadingEl.classList.add("botResponse");
      chatRoom.appendChild(loadingEl);
      chatRoom.scrollTop = chatRoom.scrollHeight;

      try {
        const res = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            chat_name: "default",
            message: cleanedInput
          })
        });

        if (!res.ok) {
          throw new Error("Server error: " + res.status);
        }

        const data = await res.json();
        loadingEl.textContent = data.response || data.reply || "No response received.";
      } catch (err) {
        console.error(err);
        loadingEl.textContent = "Error connecting to server.";
      }
      chatRoom.scrollTop = chatRoom.scrollHeight;
    }
  });

  // Enter Key Listener
  userPrompt.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      submitBtn.click();
    }
  });
}

function openAndClose() {
  if (sideBar) sideBar.hidden = !sideBar.hidden;
  if (topBar) topBar.classList.toggle("shrink");
  if (chatRoom) chatRoom.classList.toggle("shrink");
  if (userInput) userInput.classList.toggle("shrink");
}

// ===============================
// DOM ELEMENTS - UPLOAD & FLASHCARDS
// ===============================
const fileInput = document.getElementById("fileInput");
const generateBtn = document.getElementById("generateBtn");
const output = document.getElementById("output");

// Bind upload listener
if (generateBtn && fileInput && output) {
  generateBtn.addEventListener("click", handleUpload);
}

// ===============================
// MAIN UPLOAD FUNCTION
// ===============================
async function handleUpload() {
  if (!fileInput || !output) {
    console.error("Upload elements not found.");
    return;
  }
  const file = fileInput.files[0];

  if (!file) {
    output.textContent = "Please select a file first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  output.textContent = "Generating flashcards... this may take a moment.";

  try {
    const res = await fetch("http://localhost:8000/flashcards", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      throw new Error("Server error: " + res.statusText);
    }

    const data = await res.json();

    // Safely parse flashcards whether returned as a string or a direct JSON array/object
    let flashcards = data.flashcards;

    if (typeof flashcards === "string") {
      try {
        flashcards = JSON.parse(flashcards);
      } catch (err) {
        output.textContent = "Error parsing flashcards JSON string.";
        console.error("Parsing error:", err);
        return;
      }
    }

    renderFlashcards(flashcards);

  } catch (error) {
    output.textContent = "Something went wrong. Check the console for details.";
    console.error(error);
  }
}

// ===============================
// RENDER FLASHCARDS
// ===============================
function renderFlashcards(cards) {
  if (!Array.isArray(cards) || cards.length === 0) {
    output.textContent = "No valid flashcards found in response.";
    return;
  }

  output.innerHTML = ""; // Clear existing output content

  cards.forEach((card, index) => {
    // Standardize keys (Supports both front/back and question/answer)
    const frontText = card.front || card.question || "No term/question provided.";
    const backText = card.back || card.answer || "No definition/answer provided.";

    const cardEl = document.createElement("div");
    cardEl.classList.add("flashcard");
    cardEl.style.cursor = "pointer";
    cardEl.style.margin = "10px 0";
    cardEl.style.padding = "15px";
    cardEl.style.border = "1px solid #334155";
    cardEl.style.borderRadius = "8px";

    // Initial Display (Front side)
    cardEl.innerHTML = `
      <p style="font-size:0.8rem; opacity:0.7;">Card ${index + 1} (Click to flip)</p>
      <h3>${frontText}</h3>
    `;

    // Interactive Flip Effect
    let isFlipped = false;
    cardEl.addEventListener("click", () => {
      isFlipped = !isFlipped;
      if (isFlipped) {
        cardEl.innerHTML = `
          <p style="font-size:0.8rem; opacity:0.7;">Card ${index + 1} (Back)</p>
          <p><strong>Answer:</strong> ${backText}</p>
        `;
      } else {
        cardEl.innerHTML = `
          <p style="font-size:0.8rem; opacity:0.7;">Card ${index + 1} (Front)</p>
          <h3>${frontText}</h3>
        `;
      }
    });

    output.appendChild(cardEl);
  });
}