import json
import os
import logging
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

try:
    from .study_context import retrieve_context
except ImportError:
    from services.study_context import retrieve_context

SERVER_DIR = Path(__file__).resolve().parent.parent

# Keep credentials in the ignored local file; the tracked .env can hold defaults.
load_dotenv(dotenv_path=SERVER_DIR / ".env", override=False)
load_dotenv(dotenv_path=SERVER_DIR / ".env.local", override=True)

SUMMARY_TRIGGER = 5
DEFAULT_CHAT = "default"
MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

API_KEY = os.getenv("GROQ_API_KEY")
logger = logging.getLogger(__name__)
client = Groq(api_key=API_KEY) if API_KEY else None


def get_client() -> Groq:
    """Return the configured Groq client, with an actionable setup error."""
    if client is None:
        raise RuntimeError("The AI service is not configured. Add GROQ_API_KEY to server/.env and restart the server.")
    return client


def describe_groq_error(error: Exception) -> str:
    """Translate common provider failures into actionable, non-secret guidance."""
    status_code = getattr(error, "status_code", None)
    if error.__class__.__name__ in {"APIConnectionError", "ConnectError", "TimeoutException"}:
        return (
            "Quoria is running, but it cannot reach Groq. Check your internet connection, "
            "VPN/firewall settings, and whether your network allows api.groq.com."
        )
    if status_code == 401:
        return "Groq rejected GROQ_API_KEY (HTTP 401). Replace it with a valid key in server/.env, then restart the API."
    if status_code == 404:
        return f"Groq could not find model '{MODEL_NAME}'. Set GROQ_MODEL to an available model in server/.env, then restart the API."
    if status_code == 429:
        return "Groq rate limit or quota was reached. Check your Groq account limits and try again later."
    if status_code == 403:
        body = getattr(error, "body", None)
        provider_error = body.get("error", {}) if isinstance(body, dict) else {}
        provider_message = provider_error.get("message", "") if isinstance(provider_error, dict) else ""
        if "network settings" in provider_message.casefold():
            return (
                "Groq denied this network or IP address (HTTP 403). Disable any VPN or proxy, "
                "or try another network, then retry."
            )
        return "Groq denied this request (HTTP 403). Check your Groq organization and project permissions."
    return "The AI service could not complete the request. Check the API key, model, and network connection."


def is_ai_processor_error_message(content: str) -> bool:
    """Identify connection-error placeholders that must not become tutor history."""
    normalized = " ".join(content.casefold().split())
    return any(
        phrase in normalized
        for phrase in (
            "issue connecting to my ai processor",
            "error connecting to my ai processor",
            "problem connecting to my ai processor",
        )
    )


def get_reliable_messages(messages: list[dict]) -> list[dict]:
    """Drop failed user/assistant turns from prompts while preserving saved history."""
    reliable = []
    index = 0
    while index < len(messages):
        current = messages[index]
        next_message = messages[index + 1] if index + 1 < len(messages) else None
        if (
            current.get("role") == "user"
            and next_message
            and next_message.get("role") == "assistant"
            and is_ai_processor_error_message(str(next_message.get("content", "")))
        ):
            index += 2
            continue
        if current.get("role") == "assistant" and is_ai_processor_error_message(str(current.get("content", ""))):
            index += 1
            continue
        reliable.append(current)
        index += 1
    return reliable


def query_groq_ai(prompt: str, *, response_format: dict | None = None, system_prompt: str = "You are a helpful academic tutor.") -> str:
    """Send a prompt to Groq and return the model response text."""
    try:
        options = {}
        if response_format is not None:
            options["response_format"] = response_format
        response = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            **options,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("The AI service returned an empty response.")
        return content
    except Exception as exc:
        logger.exception("Groq request failed")
        raise RuntimeError(describe_groq_error(exc)) from exc


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
    if is_ai_processor_error_message(old_summary):
        old_summary = ""
    transcript = ""
    reliable_messages = get_reliable_messages(conversation["messages"])

    if len(reliable_messages) < SUMMARY_TRIGGER:
        for message in reliable_messages:
            transcript += f"{message['role']}: {message['content']}\n\n"
    else:
        for message in reliable_messages[-SUMMARY_TRIGGER:]:
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
        response = get_client().chat.completions.create(
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
    messages = get_reliable_messages(conversation["messages"])
    if not messages:
        return []

    prompt_messages = [messages[0]]
    summary = conversation.get("summary", "")

    if summary and not is_ai_processor_error_message(summary):
        prompt_messages.append({
            "role": "system",
            "content": f"Conversation Summary:\n{summary}"
        })

    messages_since_summary = (len(messages) - 1) % SUMMARY_TRIGGER

    if len(messages) - 1 <= SUMMARY_TRIGGER:
        prompt_messages.extend(messages[1:])
    elif messages_since_summary < 3:
        prompt_messages.extend(messages[-3:])
    else:
        prompt_messages.extend(messages[-messages_since_summary:])

    return prompt_messages


def process_chat_message(
    chat_name: str,
    user_input: str,
    context_id: str | None = None,
    difficulty: str = "standard",
    socratic: bool = False,
) -> str:
    """Processes message, maintains state, queries Groq API, and returns reply."""
    if not chat_name:
        chat_name = DEFAULT_CHAT

    conversation = load_conversation(chat_name)
    if context_id:
        conversation["study_context_id"] = context_id
    context_id = context_id or conversation.get("study_context_id")
    messages = conversation["messages"]

    # A failed provider request leaves its user turn at the end of the saved
    # transcript. Replace that unanswered turn on retry so the provider never
    # receives consecutive user messages (including from failures before this
    # recovery logic was added).
    if messages and messages[-1].get("role") == "user":
        messages[-1]["content"] = user_input
    else:
        messages.append({"role": "user", "content": user_input})
    conversation["messages"] = messages
    save_conversation(chat_name, conversation)

    maybe_update_summary(chat_name, conversation)

    context = retrieve_context(context_id, user_input)
    prompt_messages = build_prompt_messages(conversation)
    difficulty_instructions = {
        "eli5": "Use plain language, short sentences, and a relatable analogy. Define any unavoidable technical term.",
        "standard": "Give a clear, balanced explanation with enough detail to build real understanding.",
        "expert": "Assume strong fundamentals. Be precise, technical, and include edge cases or formal reasoning when useful.",
    }
    tutor_mode = difficulty_instructions.get(difficulty, difficulty_instructions["standard"])
    if socratic:
        tutor_mode += " Use Socratic tutoring: do not reveal the final answer immediately. Ask one focused question or give one useful hint at a time, and celebrate partial reasoning."
    prompt_messages.insert(1, {
        "role": "system",
        "content": f"Tutor mode for this turn: {tutor_mode}",
    })
    if context["sources"]:
        source_text = "\n\n".join(
            f"[Source section {source['section']}]\n{source['text']}"
            for source in context["sources"]
        )
        prompt_messages.insert(1, {
            "role": "system",
            "content": (
                f"The user uploaded {context['filename']}. Use the retrieved material below when relevant. "
                "Answer from these sources when possible, do not invent unsupported facts, and end with "
                "a brief citation like [Source section 2]. If the sources do not answer the question, say so.\n\n"
                f"Retrieved material:\n{source_text}"
            ),
        })

    try:
        response = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=prompt_messages
        )
        bot_response = response.choices[0].message.content
        if not bot_response:
            raise RuntimeError("The AI service returned an empty response.")
    except Exception as error:
        logger.exception("Tutor response generation failed")
        raise RuntimeError(describe_groq_error(error)) from error

    if is_ai_processor_error_message(bot_response):
        logger.warning("AI provider returned a connection-error placeholder; it was not saved as a tutor reply.")
        raise RuntimeError(
            "The AI provider returned a connection-error message instead of a tutor answer. "
            "The failed reply was not saved; please retry."
        )

    # Save bot response
    messages.append({"role": "assistant", "content": bot_response})
    conversation["messages"] = messages
    save_conversation(chat_name, conversation)

    return bot_response
