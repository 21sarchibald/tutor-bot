"""FastAPI application for the Studyspace tutor and flashcard features."""

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

SERVER_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=SERVER_DIR / ".env", override=False)

# Support both `uvicorn main:app` from server/ and `import server.main` from the repo root.
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

try:
    from .routers import chat, flashcards
except ImportError:
    from routers import chat, flashcards

app = FastAPI(
    title="Studyspace API",
    description="AI tutoring conversations and study flashcards generated from course materials.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(flashcards.router)


@app.get("/", tags=["status"])
def root():
    return {"message": "Studyspace API is running."}


@app.get("/health", tags=["status"])
def health_check():
    return {"status": "healthy"}
