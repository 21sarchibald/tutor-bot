"""Document upload and flashcard generation endpoint."""

import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

try:
    from ..services.flashcard_generator import generate_flashcards, generate_study_notes
    from ..services.study_context import save_study_context
    from ..services.text_extraction import extract_text_from_pdf
except ImportError:
    from services.flashcard_generator import generate_flashcards, generate_study_notes
    from services.study_context import save_study_context
    from services.text_extraction import extract_text_from_pdf

router = APIRouter()
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt"}


@router.post("/flashcards")
def flashcard_endpoint(file: UploadFile = File(...), study_mode: str = Form("cards")):
    """Extract text from an uploaded document and return cards or concise study notes."""
    if study_mode not in {"cards", "notes"}:
        raise HTTPException(status_code=400, detail="Choose either flashcards or study notes.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload a PDF, DOCX, or TXT file.")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="The selected file is empty.")
    if file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="The file is too large. Choose a file under 12 MB.")

    try:
        text = extract_text_from_pdf(file)
        if text.startswith(("Error:", "Error processing file:")):
            detail = text.removeprefix("Error processing file:").removeprefix("Error:").strip()
            raise HTTPException(status_code=422, detail=detail)
        if not text.strip():
            raise HTTPException(status_code=422, detail="No readable text was found. Try a text based PDF, DOCX, or TXT file.")
        context_id = save_study_context(file.filename or "study material", text)
        if study_mode == "notes":
            notes = generate_study_notes(text)
            if not notes.strip():
                raise HTTPException(status_code=422, detail="No study notes could be generated from this document.")
            return {"notes": notes, "context_id": context_id, "filename": file.filename}
        cards = generate_flashcards(text)
    except HTTPException:
        raise
    except RuntimeError as error:
        logger.exception("Flashcard generation failed")
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        logger.exception("Document processing failed")
        raise HTTPException(status_code=422, detail="This document could not be read. Check the file and try again.") from error
    finally:
        file.file.close()

    if not cards:
        raise HTTPException(status_code=422, detail="No flashcards could be generated from this document.")
    return {"flashcards": cards, "context_id": context_id, "filename": file.filename}
