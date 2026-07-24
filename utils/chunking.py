"""
File: server/utils/chunking.py
Description: Text chunking helper utilities.
"""

def chunk_text(text: str, max_chars: int = 4000) -> list[str]:
    """
    Splits long text strings into smaller segments for AI processing.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = ""

    for paragraph in text.split("\n\n"):
        if len(current_chunk) + len(paragraph) <= max_chars:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks