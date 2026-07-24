"""
File: server/models/flashcard.py
Description: Pydantic schemas for flashcard data validation.
"""

from pydantic import BaseModel
from typing import List

class Flashcard(BaseModel):
    front: str
    back: str

class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]

    