import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

SERVER_DIR = Path(__file__).resolve().parent.parent

# Force dotenv to overwrite stale system environment variables with server/.env values
load_dotenv(dotenv_path=SERVER_DIR / ".env", override=True)

SUMMARY_TRIGGER = 5
DEFAULT_CHAT = "default"
MODEL_NAME = "llama-3.3-70b-versatile"

API_KEY = os.getenv("GROQ_API_KEY")

# Debug print to verify which key Python is actually reading on server startup
print(f"DEBUG: Loaded API Key starts with -> {API_KEY[:7] if API_KEY else 'NONE'}")

if not API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY environment variable. Please check your .env file or environment settings.")

client = Groq(api_key=API_KEY)


def query_groq_ai(prompt: str) -> str:
    """Sends a prompt to Groq and returns the model response text."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful academic tutor.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as exc:
        print(f"Groq API Error: {exc}")
        return f"Error: {exc}"


def ensure_conversations_folder():
    """Ensures the conversations directory exists."""
    conversations_dir = SERVER_DIR / "conversations"
    conversations_dir.mkdir(parents=True, exist_ok=True)


def get_chat_file(chat_name: str) -> str:
    """Generates a safe path for JSON conversation files."""
    safe_name = "".join(c for c in chat_name.strip() if c.isalnum() or c in ("-", "_")).strip()
    if not safe_name:
        safe_name = DEFAULT_CHAT
    return str(SERVER_DIR / "conversations" / f"{safe_name}.json")


def get_timestamp() -> str:
    """Generates UTC ISO timestamp."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def create_conversation(chat_name: str) -> dict:
    """Initializes a new chat structure."""
    timestamp = get_timestamp()
    return {
        "title": chat_name,
        "created": timestamp,
        "last_updated": timestamp,
        "summary": "",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI Academic Tutor operating like ChatGPT. You can answer any general knowledge question, study query, or topic accurately, clearly, and helpfully."
            }
        ]
    }


def save_conversation(chat_name: str, conversation: dict) -> None:
    """Saves conversation data to file."""
    ensure_conversations_folder()
    conversation["last_updated"] = get_timestamp()
    with open(get_chat_file(chat_name), "w", encoding="utf-8") as file:
        json.dump(conversation, file, indent=4)


def load_conversation(chat_name: str) -> dict:
    """Loads a conversation or builds a new one if missing or corrupted."""
    ensure_conversations_folder()
    path = get_chat_file(chat_name)
    if not os.path.exists(path):
        conversation = create_conversation(chat_name)
        save_conversation(chat_name, conversation)
        return conversation

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        conversation = create_conversation(chat_name)
        save_conversation(chat_name, conversation)
        return conversation


def list_all_conversations() -> list[str]:
    """Lists available conversation sessions."""
    ensure_conversations_folder()
    conversations_dir = SERVER_DIR / "conversations"
    conversations = []
    for file in sorted(os.listdir(conversations_dir)):
        if file.endswith(".json"):
            conversations.append(os.path.splitext(file)[0])
    return conversations


def update_summary(conversation: dict) -> str:
    """Creates/updates dynamic memory summary using Groq."""
    old_summary = conversation.get("summary", "")
    transcript = ""

    if len(conversation["messages"]) < SUMMARY_TRIGGER:
        for message in conversation["messages"]:
            transcript += f"{message['role']}: {message['content']}\n\n"
    else:
        for message in conversation["messages"][-SUMMARY_TRIGGER:]:
            transcript += f"{message['role']}: {message['content']}\n\n"

    summary_prompt = f"""
Create a summary using the recent messages.

Focus on:
- User Goals
- Important decisions
- Important facts
- Unfinished tasks

Exclude:
- Greetings
- Small Talk
- Repetitive information

Recent Conversation:
{transcript}
"""

    if len(old_summary.strip()) >= 1:
        summary_prompt = summary_prompt.replace("Create a", "Update the")
        summary_prompt += f"\n\nCurrent Summary:\n {old_summary}"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a memory extraction system that creates & updates concise conversation summaries."
                },
                {"role": "user", "content": summary_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {e}")
        return old_summary


def maybe_update_summary(chat_name: str, conversation: dict) -> None:
    """Checks if message count requires updating conversation summary."""
    message_ct = len(conversation["messages"]) - 1
    if message_ct < SUMMARY_TRIGGER or message_ct % SUMMARY_TRIGGER != 0:
        return
    summary = update_summary(conversation)
    conversation["summary"] = summary
    save_conversation(chat_name, conversation)


def build_prompt_messages(conversation: dict) -> list[dict]:
    """Combines baseline system instructions, memory summaries, and recent turns."""
    prompt_messages = [conversation["messages"][0]]
    summary = conversation.get("summary", "")

    if summary:
        prompt_messages.append({
            "role": "system",
            "content": f"Conversation Summary:\n{summary}"
        })

    messages_since_summary = (len(conversation["messages"]) - 1) % SUMMARY_TRIGGER

    if len(conversation["messages"]) - 1 <= SUMMARY_TRIGGER:
        prompt_messages.extend(conversation["messages"][1:])
    elif messages_since_summary < 3:
        prompt_messages.extend(conversation["messages"][-3:])
    else:
        prompt_messages.extend(conversation["messages"][-messages_since_summary:])

    return prompt_messages


def process_chat_message(chat_name: str, user_input: str) -> str:
    """Processes message, maintains state, queries Groq API, and returns reply."""
    if not chat_name:
        chat_name = DEFAULT_CHAT

    conversation = load_conversation(chat_name)
    messages = conversation["messages"]

    # Save user input
    messages.append({"role": "user", "content": user_input})
    conversation["messages"] = messages
    save_conversation(chat_name, conversation)

    maybe_update_summary(chat_name, conversation)

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=build_prompt_messages(conversation)
        )
        bot_response = response.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        bot_response = "I ran into an issue connecting to my AI processor. Please try again."

    # Save bot response
    messages.append({"role": "assistant", "content": bot_response})
    conversation["messages"] = messages
    save_conversation(chat_name, conversation)

    return bot_response