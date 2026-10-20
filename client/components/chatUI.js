/** Render a small, reusable chat view into the supplied container. */
export function renderChatUI(container) {
  const apiBase = window.location.protocol === "http:" || window.location.protocol === "https:"
    ? `${window.location.protocol}//${window.location.hostname || "127.0.0.1"}:8080`
    : "http://127.0.0.1:8080";
  const layout = document.createElement("section");
  layout.className = "component-chat";

  const history = document.createElement("div");
  history.className = "chat-room";
  history.setAttribute("aria-live", "polite");
  history.setAttribute("aria-label", "Conversation messages");

  const form = document.createElement("form");
  form.className = "composer-row";
  const input = document.createElement("textarea");
  input.className = "component-chat-input";
  input.rows = 1;
  input.placeholder = "Ask your AI tutor…";
  input.setAttribute("aria-label", "Message your AI tutor");
  const sendButton = document.createElement("button");
  sendButton.className = "send-button";
  sendButton.type = "submit";
  sendButton.textContent = "↑";
  sendButton.setAttribute("aria-label", "Send message");
  form.append(input, sendButton);
  layout.append(history, form);
  container.replaceChildren(layout);

  function addMessage(text, role) {
    const message = document.createElement("article");
    message.className = `chat-message ${role}`;
    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;
    message.append(content);
    history.append(message);
    history.scrollTop = history.scrollHeight;
    return content;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text || sendButton.disabled) return;
    addMessage(text, "user");
    input.value = "";
    sendButton.disabled = true;
    const responseMessage = addMessage("Tutor is thinking…", "assistant");

    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_name: "default", message: text }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `Server error (${response.status}).`);
      responseMessage.textContent = data.response || data.reply || "No response received.";
    } catch (error) {
      responseMessage.textContent = `Could not reach the tutor. ${error.message || "Check that the server is running."}`;
    } finally {
      sendButton.disabled = false;
      input.focus();
      history.scrollTop = history.scrollHeight;
    }
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
}
