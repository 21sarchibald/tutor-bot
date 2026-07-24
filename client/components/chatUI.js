/**
 * Component: ChatUI
 * Renders interactive chat input and message stream.
 */
export function renderChatUI(container) {
  container.innerHTML = `
    <div class="chat-box">
      <div id="chat-history" class="chat-history"></div>
      <div class="chat-input-area">
        <input type="text" id="chat-input" style="flex:1; padding:0.75rem; border-radius:8px; border:1px solid #334155; background:#0f172a; color:white;" placeholder="Ask your AI Tutor..." />
        <button id="send-btn" style="padding:0.75rem 1.5rem; background:#3b82f6; color:white; border:none; border-radius:8px; cursor:pointer;">Send</button>
      </div>
    </div>
  `;

  const input = container.querySelector("#chat-input");
  const sendBtn = container.querySelector("#send-btn");
  const history = container.querySelector("#chat-history");

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    // Append User Message
    history.innerHTML += `<div class="message user">${text}</div>`;
    input.value = "";
    history.scrollTop = history.scrollHeight;

    try {
      // Mock or call local API route
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await response.json();
      
      // Append Assistant Response
      history.innerHTML += `<div class="message assistant">${data.reply || "Thinking..."}</div>`;
    } catch {
      history.innerHTML += `<div class="message assistant">⚠️ Error connecting to server.</div>`;
    }
    history.scrollTop = history.scrollHeight;
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keypress", (e) => e.key === "Enter" && sendMessage());
}