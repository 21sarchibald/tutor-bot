"""Persisted, lightweight retrieval context for uploaded study materials."""

import json
import re
import uuid
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent
CONTEXTS_DIR = SERVER_DIR / "study_contexts"
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}")
CONTEXT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def _tokens(value: str) -> set[str]:
    return {token.casefold() for token in TOKEN_PATTERN.findall(value)}


def save_study_context(filename: str, text: str) -> str:
    """Save extracted material and return an opaque ID for later chat requests."""
    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)
    context_id = uuid.uuid4().hex
    paragraphs = [part.strip() for part in text.splitlines() if part.strip()]
    chunks: list[dict[str, object]] = []
    current: list[str] = []
    current_size = 0
    for paragraph in paragraphs:
        if current and current_size + len(paragraph) + 2 > 4000:
            chunks.append({"text": "\n\n".join(current), "section": len(chunks) + 1})
            current = []
            current_size = 0
        current.append(paragraph)
        current_size += len(paragraph) + 2
    if current:
        chunks.append({"text": "\n\n".join(current), "section": len(chunks) + 1})

    payload = {"filename": filename, "chunks": chunks}
    (CONTEXTS_DIR / f"{context_id}.json").write_text(json.dumps(payload), encoding="utf-8")
    return context_id


def retrieve_context(context_id: str | None, query: str, limit: int = 4) -> dict:
    """Return the most lexically relevant source chunks for a user question."""
    if not context_id or not CONTEXT_ID_PATTERN.fullmatch(context_id):
        return {"filename": "", "sources": []}
    path = CONTEXTS_DIR / f"{context_id}.json"
    if not path.is_file():
        return {"filename": "", "sources": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"filename": "", "sources": []}

    query_tokens = _tokens(query)
    ranked = []
    for chunk in payload.get("chunks", []):
        text = str(chunk.get("text", ""))
        score = len(query_tokens & _tokens(text))
        if score:
            ranked.append((score, chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)
    sources = [
        {"section": chunk.get("section", index + 1), "text": chunk.get("text", "")}
        for index, (_, chunk) in enumerate(ranked[:limit])
    ]
    return {"filename": payload.get("filename", ""), "sources": sources}
