// ==========================================
// DOM ELEMENTS - CHAT & SIDEBAR
// ==========================================
const sideBtn = document.querySelector("#sidebarBtn");
const sideBar = document.querySelector("#sidebar");
const chatRoom = document.querySelector("#chatRoom");
const topBar = document.querySelector("#top");
const userInput = document.querySelector("#userinput");
const userPrompt = document.querySelector("#userPrompt");
const submitBtn = document.querySelector("#submit");
const closeBtn = document.querySelector(".close");

// Sidebar Toggle Listener
if (sideBtn) sideBtn.addEventListener("click", openAndClose);
if (closeBtn) closeBtn.addEventListener("click", openAndClose);

function openAndClose() {
  if (sideBar) sideBar.hidden = !sideBar.hidden;
  if (topBar) topBar.classList.toggle("shrink");
  if (chatRoom) chatRoom.classList.toggle("shrink");
  if (userInput) userInput.classList.toggle("shrink");
}

// ==========================================
// CHAT FUNCTIONALITY
// ==========================================
if (submitBtn && userPrompt && chatRoom) {
  submitBtn.addEventListener("click", async () => {
    let cleanedInput = userPrompt.value.trim();
    if (cleanedInput !== "") {
      // Append user prompt message
      chatRoom.innerHTML += `<p class="userPromptDisplay">${cleanedInput}</p>`;
      userPrompt.value = "";
      chatRoom.scrollTop = chatRoom.scrollHeight;

      // Create bot loading placeholder
      const loadingEl = document.createElement("p");
      loadingEl.textContent = "Tutorbot is thinking...";
      loadingEl.classList.add("botResponse");
      chatRoom.appendChild(loadingEl);
      chatRoom.scrollTop = chatRoom.scrollHeight;

      try {
        const res = await fetch("http://localhost:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chat_name: "default", message: cleanedInput })
        });

        if (!res.ok) throw new Error("Server error: " + res.status);

        const data = await res.json();
        loadingEl.textContent = data.response || data.reply || "No response received.";
      } catch (err) {
        console.error(err);
        loadingEl.textContent = "Error connecting to server.";
      }
      chatRoom.scrollTop = chatRoom.scrollHeight;
    }
  });

  userPrompt.addEventListener("keypress", (e) => {
    if (e.key === "Enter") submitBtn.click();
  });
}

// ==========================================
// NAVIGATION & SECTION SWITCHING
// ==========================================
const navLinks = document.querySelectorAll(".nav-link");
const sections = document.querySelectorAll(".content-section");
const headerTitle = document.querySelector("#headerTitle");

navLinks.forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();

    navLinks.forEach((l) => l.classList.remove("active"));
    sections.forEach((sec) => {
      sec.classList.remove("active");
      sec.hidden = true;
    });

    link.classList.add("active");
    const targetSectionId = link.getAttribute("data-tab");
    const targetSection = document.getElementById(targetSectionId);

    if (targetSection) {
      targetSection.classList.add("active");
      targetSection.hidden = false;
    }

    if (headerTitle) {
      headerTitle.textContent = link.textContent.trim();
    }

    // Auto-close sidebar on mobile after clicking
    if (window.innerWidth < 700 && sideBar && !sideBar.hidden) {
      openAndClose();
    }
  });
});

// ==========================================
// FILE UPLOAD & FLASHCARDS
// ==========================================
const fileUploadBtn = document.getElementById("fileupload");
const fileInput = document.getElementById("fileInput");
const output = document.getElementById("output");

if (fileUploadBtn && fileInput) {
  fileUploadBtn.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleUpload();
    }
  });
}

async function handleUpload() {
  if (!fileInput || !output) return;
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  output.innerHTML = "<p>Generating flashcards... this may take a moment.</p>";

  // Automatically open the flashcards tab
  const flashcardTabBtn = document.querySelector('[data-tab="flashcardsSection"]');
  if (flashcardTabBtn) flashcardTabBtn.click();

  try {
    const res = await fetch("http://localhost:8000/flashcards", {
      method: "POST",
      body: formData
    });

    if (!res.ok) throw new Error("Server error: " + res.statusText);

    const data = await res.json();
    let flashcards = data.flashcards;

    if (typeof flashcards === "string") {
      try {
        flashcards = JSON.parse(flashcards);
      } catch (err) {
        output.textContent = "Error parsing flashcards JSON string.";
        return;
      }
    }

    renderFlashcards(flashcards);
  } catch (error) {
    output.textContent = "Something went wrong generating flashcards.";
    console.error(error);
  }
}

function renderFlashcards(cards) {
  if (!Array.isArray(cards) || cards.length === 0) {
    output.textContent = "No valid flashcards found.";
    return;
  }

  output.innerHTML = "";

  cards.forEach((card, index) => {
    const frontText = card.front || card.question || "No term/question provided.";
    const backText = card.back || card.answer || "No definition/answer provided.";

    const cardEl = document.createElement("div");
    cardEl.classList.add("flashcard");

    cardEl.innerHTML = `
      <p style="font-size:0.8rem; opacity:0.7; margin:0 0 5px 0;">Card ${index + 1} (Click to flip)</p>
      <h3>${frontText}</h3>
    `;

    let isFlipped = false;
    cardEl.addEventListener("click", () => {
      isFlipped = !isFlipped;
      if (isFlipped) {
        cardEl.innerHTML = `
          <p style="font-size:0.8rem; opacity:0.7; margin:0 0 5px 0;">Card ${index + 1} (Back)</p>
          <p><strong>Answer:</strong> ${backText}</p>
        `;
      } else {
        cardEl.innerHTML = `
          <p style="font-size:0.8rem; opacity:0.7; margin:0 0 5px 0;">Card ${index + 1} (Front)</p>
          <h3>${frontText}</h3>
        `;
      }
    });

    output.appendChild(cardEl);
  });
}