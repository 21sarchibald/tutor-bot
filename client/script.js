// `file://` pages have no hostname and cannot form a valid API URL. Keep the
// documented local-server workflow usable even when index.html is opened directly.
const API_BASE = window.location.protocol === "http:" || window.location.protocol === "https:"
  ? `${window.location.protocol}//${window.location.hostname || "127.0.0.1"}:8080`
  : "http://127.0.0.1:8080";
const IS_FILE_PAGE = window.location.protocol === "file:";
const sideBar = document.querySelector("#sidebar");
const sideBtn = document.querySelector("#sidebarBtn");
const scrim = document.querySelector("#sidebarScrim");
const chatRoom = document.querySelector("#chatRoom");
const welcomeState = document.querySelector("#welcomeState");
const chatForm = document.querySelector("#chatForm");
const userPrompt = document.querySelector("#userPrompt");
const submitBtn = document.querySelector("#submit");
const navLinks = [...document.querySelectorAll(".nav-link")];
const sections = [...document.querySelectorAll(".content-section")];
const headerTitle = document.querySelector("#headerTitle");
const fileInput = document.querySelector("#fileInput");
const toast = document.querySelector("#toast");
const output = document.querySelector("#output");
const chatHistory = document.querySelector("#historyList");
const uploadPreview = document.querySelector("#uploadPreview");
const uploadName = document.querySelector("#uploadName");

let currentChatName = "default";
let selectedFile = null;
let flashcards = [];
let activeCardIndex = 0;
let studyMode = "cards";
let studyNotes = "";
let toastTimer;
let conversationLoadToken = 0;

function isAiProcessorErrorMessage(text) {
  return /(?:issue|error|problem) connecting to my ai processor/i.test(String(text || ""));
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3600);
}

function setSidebar(open) {
  const isMobile = window.matchMedia("(max-width: 760px)").matches;
  if (isMobile) {
    sideBar.classList.toggle("is-open", open);
    scrim.hidden = !open;
  } else {
    sideBar.classList.toggle("is-collapsed", !open);
  }
  sideBtn.setAttribute("aria-expanded", String(open));
  sideBtn.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
}

sideBtn.addEventListener("click", () => {
  const isOpen = window.matchMedia("(max-width: 760px)").matches
    ? sideBar.classList.contains("is-open")
    : !sideBar.classList.contains("is-collapsed");
  setSidebar(!isOpen);
});
scrim.addEventListener("click", () => setSidebar(false));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") setSidebar(false);
});

function navigate(sectionId) {
  const target = document.getElementById(sectionId);
  if (!target) return;
  sections.forEach((section) => {
    const active = section === target;
    section.hidden = !active;
    section.classList.toggle("active", active);
  });
  navLinks.forEach((link) => {
    const active = link.dataset.tab === sectionId;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  const activeLink = navLinks.find((link) => link.dataset.tab === sectionId);
  headerTitle.textContent = activeLink?.dataset.title || "AI tutor";
  if (window.matchMedia("(max-width: 760px)").matches) setSidebar(false);
}

navLinks.forEach((link) => link.addEventListener("click", () => navigate(link.dataset.tab)));
document.querySelectorAll("[data-tab]").forEach((button) => {
  if (button.classList.contains("nav-link")) return;
  button.addEventListener("click", () => navigate(button.dataset.tab));
});

function appendMessage(text, role) {
  welcomeState.hidden = true;
  const row = document.createElement("article");
  row.className = `chat-message ${role}`;
  const avatar = document.createElement("span");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "S" : "✳";
  const content = document.createElement("div");
  content.className = "message-content";
  content.textContent = text;
  row.append(avatar, content);
  chatRoom.append(row);
  chatRoom.scrollTop = chatRoom.scrollHeight;
  return { row, content };
}

function clearChat() {
  chatRoom.replaceChildren(welcomeState);
  welcomeState.hidden = false;
  userPrompt.value = "";
  userPrompt.style.height = "auto";
  userPrompt.focus();
}

async function loadConversation(chatName) {
  const loadToken = ++conversationLoadToken;
  const isCurrentLoad = () =>
    loadToken === conversationLoadToken && currentChatName === chatName;
  currentChatName = chatName;
  clearChat();
  try {
    const response = await fetch(`${API_BASE}/conversations/${encodeURIComponent(chatName)}`);
    if (!response.ok) throw new Error("Could not load conversation.");
    const conversation = await response.json();
    if (!isCurrentLoad()) return;
    const messages = (conversation.messages || []).filter((message) => ["user", "assistant"].includes(message.role));
    const visibleMessages = [];
    for (const current of messages) {
      // Keep every question in the saved transcript. A provider error is not
      // an answer, so omit only that error placeholder from the chat display.
      if (current.role === "assistant" && isAiProcessorErrorMessage(current.content)) {
        continue;
      }
      visibleMessages.push(current);
    }
    if (visibleMessages.length) {
      welcomeState.hidden = true;
      visibleMessages.forEach((message) => appendMessage(message.content || "", message.role === "user" ? "user" : "assistant"));
    }
  } catch (error) {
    if (!isCurrentLoad()) return;
    console.error("Conversation history error:", error);
    if (chatName !== "default") showToast("Could not load that conversation. Start a new one instead.");
  }
  if (isCurrentLoad()) await refreshHistory();
}

async function refreshHistory() {
  try {
    const response = await fetch(`${API_BASE}/conversations`);
    if (!response.ok) return;
    const data = await response.json();
    // Include the default/main chat too: every message sent there is saved by
    // the API and should remain reachable after the user leaves the page.
    const names = (data.conversations || []).reverse();
    chatHistory.replaceChildren();
    if (!names.length) {
      chatHistory.className = "history-empty";
      chatHistory.textContent = "Your conversations will appear here.";
      return;
    }
    chatHistory.className = "history-list";
    names.forEach((name) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "history-item";
      item.textContent = name === "default"
        ? "Main conversation"
        : name.replace(/^study-/, "Study session ");
      item.title = name;
      item.addEventListener("click", () => {
        navigate("chatSection");
        loadConversation(name);
      });
      chatHistory.append(item);
    });
  } catch (error) {
    console.info("Conversation list is unavailable until the API is running.", error);
  }
}

async function sendMessage(message = userPrompt.value.trim()) {
  const cleanMessage = message.trim();
  if (!cleanMessage || submitBtn.disabled) return;
  // A late history response must not repaint over a message the user just sent.
  conversationLoadToken += 1;
  navigate("chatSection");
  appendMessage(cleanMessage, "user");
  const pending = appendMessage("Tutor is thinking", "assistant");
  pending.row.classList.add("pending");
  const dots = document.createElement("span");
  dots.className = "typing-dots";
  dots.setAttribute("aria-label", "Loading");
  dots.innerHTML = "<i></i><i></i><i></i>";
  pending.content.append(dots);
  submitBtn.disabled = true;
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_name: currentChatName, message: cleanMessage }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Server error (${response.status}).`);
    pending.content.textContent = data.response || data.reply || "No response received.";
    pending.row.classList.remove("pending");
    userPrompt.value = "";
    userPrompt.style.height = "auto";
  } catch (error) {
    pending.row.classList.remove("pending");
    const apiUnavailable = error instanceof TypeError;
    pending.content.textContent = IS_FILE_PAGE
      ? "Open Studyspace at http://127.0.0.1:5501/ so the browser can connect to the tutor."
      : apiUnavailable
        ? "I can’t reach the Studyspace API at 127.0.0.1:8080. Start the backend from the server folder, then send your message again."
      : `I couldn’t reach your tutor. ${error.message || "Check that the server is running, then try again."}`;
    showToast(IS_FILE_PAGE
      ? "Open Studyspace at http://127.0.0.1:5501/ to use the tutor."
      : apiUnavailable
        ? "Studyspace API isn’t running. Start the backend, then try again."
        : `Message wasn’t sent. ${error.message || "Try again."}`);
  } finally {
    // The API saves the user's question before asking the AI provider. Refresh
    // here as well as on success so a question is still listed if AI fails.
    await refreshHistory();
    submitBtn.disabled = false;
    userPrompt.focus();
    chatRoom.scrollTop = chatRoom.scrollHeight;
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage();
});
userPrompt.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});
userPrompt.addEventListener("input", () => {
  userPrompt.style.height = "auto";
  userPrompt.style.height = `${Math.min(userPrompt.scrollHeight, 150)}px`;
});
document.querySelectorAll(".suggestion-card[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});
document.querySelector("#newChatBtn").addEventListener("click", () => {
  conversationLoadToken += 1;
  currentChatName = `study-${Date.now()}`;
  clearChat();
  navigate("chatSection");
  refreshHistory();
});

function setSelectedFile(file) {
  selectedFile = file;
  uploadPreview.hidden = !file;
  uploadName.textContent = file ? file.name : "";
}
document.querySelector("#fileupload").addEventListener("click", () => fileInput.click());
document.querySelector("#flashcardUploadBtn").addEventListener("click", () => fileInput.click());
document.querySelector("#emptyUploadBtn").addEventListener("click", () => fileInput.click());
document.querySelectorAll("[data-study-mode]").forEach((button) => {
  button.addEventListener("click", () => {
    studyMode = button.dataset.studyMode;
    document.querySelectorAll("[data-study-mode]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-pressed", String(active));
    });
  });
});
document.querySelector("#removeUpload").addEventListener("click", () => {
  setSelectedFile(null);
  fileInput.value = "";
});
fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  setSelectedFile(file);
  generateFlashcards(file);
});

function normalizeFlashcards(cards) {
  if (typeof cards === "string") {
    try { cards = JSON.parse(cards); } catch { return []; }
  }
  if (!Array.isArray(cards)) return [];
  return cards.map((card) => ({
    front: String(card.front || card.question || "Review this concept"),
    back: String(card.back || card.answer || "No answer provided."),
  }));
}

async function generateFlashcards(file) {
  navigate("flashcardsSection");
  output.replaceChildren();
  const loading = document.createElement("div");
  loading.className = "empty-deck";
  const icon = document.createElement("span");
  icon.textContent = "✧";
  const title = document.createElement("strong");
  title.textContent = "Making your deck…";
  const detail = document.createElement("p");
  detail.textContent = `Reading ${file.name} and finding the ideas worth remembering.`;
  loading.append(icon, title, detail);
  output.append(loading);
  const formData = new FormData();
  formData.append("file", file);
  formData.append("study_mode", studyMode);
  try {
    const response = await fetch(`${API_BASE}/flashcards`, { method: "POST", body: formData });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Server error (${response.status}).`);
    if (studyMode === "notes") {
      studyNotes = String(data.notes || "").trim();
      if (!studyNotes) throw new Error("No study notes could be generated from this document.");
      renderStudyNotes();
      showToast("Your study notes are ready.");
      return;
    }
    flashcards = normalizeFlashcards(data.flashcards);
    activeCardIndex = 0;
    if (!flashcards.length) throw new Error("No cards were generated. Try a text based PDF or a shorter document.");
    renderFlashcards();
    showToast(`${flashcards.length} flashcards ready to study.`);
  } catch (error) {
    output.replaceChildren();
    const empty = document.createElement("div");
    empty.className = "empty-deck";
    const icon = document.createElement("span");
    icon.textContent = "!";
    const title = document.createElement("strong");
    title.textContent = "We couldn’t make this deck yet.";
    const detail = document.createElement("p");
    detail.textContent = IS_FILE_PAGE
      ? "Open Studyspace at http://127.0.0.1:5501/ so the browser can connect to the tutor."
      : error instanceof TypeError
        ? "Can’t connect to the Studyspace API at 127.0.0.1:8080. Start the backend from the server folder, then try again."
      : error.message || "Check that the tutor server is running, then try again.";
    const retry = document.createElement("button");
    retry.className = "text-button";
    retry.type = "button";
    retry.textContent = "Try another file →";
    retry.addEventListener("click", () => fileInput.click());
    empty.append(icon, title, detail, retry);
    output.append(empty);
    showToast(IS_FILE_PAGE
      ? "Open Studyspace at http://127.0.0.1:5501/ to use the tutor."
      : error instanceof TypeError
        ? "Studyspace API isn’t running. Start the backend, then upload again."
      : `Flashcards weren’t generated. ${error.message || "Try again."}`);
  }
}

function renderStudyNotes() {
  output.replaceChildren();
  document.querySelector(".deck-toolbar h2").firstChild.textContent = "Study notes ";
  document.querySelector("#deckTotal").textContent = "(notes)";
  document.querySelector("#flashcardCount").textContent = "Notes";
  document.querySelector("#deckControls").hidden = true;
  document.querySelector("#flipHint").hidden = true;
  const article = document.createElement("article");
  article.className = "study-notes";
  const heading = document.createElement("h2");
  heading.textContent = "Study notes";
  const body = document.createElement("div");
  body.className = "study-notes-content";
  body.textContent = studyNotes;
  article.append(heading, body);
  output.append(article);
}

function renderFlashcards() {
  output.replaceChildren();
  document.querySelector(".deck-toolbar h2").firstChild.textContent = "Study cards ";
  document.querySelector("#deckTotal").textContent = `(${flashcards.length})`;
  document.querySelector("#flashcardCount").textContent = String(flashcards.length);
  document.querySelector("#deckControls").hidden = flashcards.length < 2;
  document.querySelector("#flipHint").hidden = flashcards.length === 0;
  document.querySelector("#cardCounter").textContent = `${activeCardIndex + 1} / ${flashcards.length}`;
  document.querySelector("#prevCard").disabled = activeCardIndex === 0;
  document.querySelector("#nextCard").disabled = activeCardIndex === flashcards.length - 1;
  flashcards.forEach((card, index) => {
    const element = document.createElement("button");
    element.type = "button";
    element.className = "flashcard";
    element.setAttribute("aria-label", `Card ${index + 1}: ${card.front}. Activate to reveal the answer.`);
    const label = document.createElement("span");
    label.className = "flashcard-label";
    label.textContent = "QUESTION";
    const question = document.createElement("p");
    question.className = "flashcard-text";
    question.textContent = card.front;
    const meta = document.createElement("span");
    meta.className = "flashcard-meta";
    meta.innerHTML = `<span>Card ${index + 1}</span><span>Tap to reveal ↗</span>`;
    element.append(label, question, meta);
    element.addEventListener("click", () => {
      const flipped = element.classList.toggle("is-flipped");
      element.setAttribute("aria-label", flipped ? `Card ${index + 1} answer: ${card.back}. Activate to show question.` : `Card ${index + 1}: ${card.front}. Activate to reveal the answer.`);
      label.textContent = flipped ? "ANSWER" : "QUESTION";
      question.textContent = flipped ? card.back : card.front;
      question.classList.toggle("flashcard-answer", flipped);
      meta.lastElementChild.textContent = flipped ? "Tap to flip back ↗" : "Tap to reveal ↗";
      activeCardIndex = index;
      updateCardCounter();
    });
    output.append(element);
  });
}

function updateCardCounter() {
  document.querySelector("#cardCounter").textContent = `${activeCardIndex + 1} / ${flashcards.length}`;
  document.querySelector("#prevCard").disabled = activeCardIndex === 0;
  document.querySelector("#nextCard").disabled = activeCardIndex === flashcards.length - 1;
  output.children[activeCardIndex]?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
document.querySelector("#prevCard").addEventListener("click", () => {
  if (activeCardIndex > 0) { activeCardIndex -= 1; updateCardCounter(); }
});
document.querySelector("#nextCard").addEventListener("click", () => {
  if (activeCardIndex < flashcards.length - 1) { activeCardIndex += 1; updateCardCounter(); }
});

refreshHistory();
loadConversation("default");
