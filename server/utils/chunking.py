"""Helpers for splitting extracted study material into model sized sections."""


def chunk_text(text: str, max_chars: int = 12000) -> list[str]:
    """Split text at paragraph boundaries, splitting oversized paragraphs safely."""
    cleaned = text.strip()
    if not cleaned:
        return []
    if max_chars < 1:
        raise ValueError("max_chars must be a positive integer.")

    chunks: list[str] = []
    current: list[str] = []
    current_size = 0

    for paragraph in (part.strip() for part in cleaned.splitlines()):
        if not paragraph:
            continue

        # Break a single long paragraph into bounded pieces before packing it.
        segments = [paragraph[index:index + max_chars] for index in range(0, len(paragraph), max_chars)]
        for segment in segments:
            separator_size = 2 if current else 0
            if current and current_size + separator_size + len(segment) > max_chars:
                chunks.append("\n\n".join(current))
                current = []
                current_size = 0
            current.append(segment)
            current_size += (2 if len(current) > 1 else 0) + len(segment)

    if current:
        chunks.append("\n\n".join(current))
    return chunks
