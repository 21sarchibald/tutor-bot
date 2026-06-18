const sideBtn = document.querySelector("#sidebarBtn");
const sideBar = document.querySelector("#sidebar");
const chatRoom = document.querySelector("#chatRoom");
const userPrompt = document.querySelector("#userPrompt");
const submitBtn = document.querySelector("#submit");
const closeBtn = document.querySelector(".close");

sideBtn.addEventListener("click", () => {
   sideBar.hidden = !sideBar.hidden;
});
closeBtn.addEventListener('click', ()=>{
  sideBar.hidden = !sideBar.hidden;
});
submitBtn.addEventListener("click",()=>{
   let cleanedInput = userPrompt.value.trim();
   if (cleanedInput != ""){
      chatRoom.innerHTML += `
      <p class="userPromptDisplay">${userPrompt.value}</p>`;
      userPrompt.value = "";
   }
});

userPrompt.addEventListener("keypress", (e) => {
   if (e.key === "Enter") {
      submitBtn.click();
   }
});

// ===============================
// DOM ELEMENTS
// ===============================
const fileInput = document.getElementById("fileInput");
const generateBtn = document.getElementById("generateBtn");
const output = document.getElementById("output");

// ===============================
// EVENT LISTENER
// ===============================
generateBtn.addEventListener("click", handleUpload);

// ===============================
// MAIN UPLOAD FUNCTION
// ===============================
async function handleUpload() {
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

    // The backend returns a string of JSON — we need to parse it
    let flashcards;
    try {
      flashcards = JSON.parse(data.flashcards);
    } catch (err) {
      output.textContent = "Error parsing flashcards. Check backend output.";
      console.error("Parsing error:", err);
      return;
    }

    renderFlashcards(flashcards);

  } catch (error) {
    output.textContent = "Something went wrong. Check console.";
    console.error(error);
  }
}

// ===============================
// RENDER FLASHCARDS
// ===============================
function renderFlashcards(cards) {
  if (!Array.isArray(cards)) {
    output.textContent = "Flashcards format invalid.";
    return;
  }

  output.innerHTML = ""; // clear previous content

  cards.forEach(card => {
    const cardEl = document.createElement("div");
    cardEl.classList.add("flashcard");

    cardEl.innerHTML = `
      <h3>Q: ${card.question}</h3>
      <p><strong>A:</strong> ${card.answer}</p>
    `;

    output.appendChild(cardEl);
  });
}
