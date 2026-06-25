const sideBtn = document.querySelector("#sidebarBtn");
const sideBar = document.querySelector("#sidebar");
const chatRoom = document.querySelector("#chatRoom");
const topBar = document.querySelector("#top");
const userInput = document.querySelector("#userinput");
const userPrompt = document.querySelector("#userPrompt");
const submitBtn = document.querySelector("#submit");
const closeBtn = document.querySelector(".close");

//open and close the
sideBtn.addEventListener("click", openAndClose);
closeBtn.addEventListener('click', openAndClose);

//display chat
submitBtn.addEventListener("click", async ()=>{
   let cleanedInput = userPrompt.value.trim();
   if (cleanedInput != ""){
      chatRoom.innerHTML += `
      <p class="userPromptDisplay">${userPrompt.value}</p>`;
      userPrompt.value = "";

      const loadingEl = document.createElement("p");
      loadingEl.textContent = "Tutorbot is thinking...";
      loadingEl.classList.add("botResponse");
      chatRoom.appendChild(loadingEl);

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

        loadingEl.textContent = data.response;
      } catch (err) {
        console.error(err);
        loadingEl.textContent = "Error connecting to server.";
      }


   } 
});

userPrompt.addEventListener("keypress", (e) => {
   if (e.key === "Enter") {
      submitBtn.click();
   }
});

function openAndClose(){
  sideBar.hidden = !sideBar.hidden;
   topBar.classList.toggle("shrink");   
   chatRoom.classList.toggle("shrink");   
   userInput.classList.toggle("shrink");
}

// ===============================
// DOM ELEMENTS
// ===============================
const fileInput = document.getElementById("fileInput");
const generateBtn = document.getElementById("generateBtn");
const output = document.getElementById("output");

// ===============================
// EVENT LISTENER
// ===============================
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
