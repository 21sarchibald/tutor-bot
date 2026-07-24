import os
import sys
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

# Pre-load environment variables prior to importing application routes
load_dotenv(dotenv_path=SERVER_DIR / ".env", override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .routers.chat import router as chat_router
    from .routers.flashcards import router as flashcard_router
except ImportError:
    from routers.chat import router as chat_router
    from routers.flashcards import router as flashcard_router

app = FastAPI(
    title="AI Academic Tutor API",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register chat endpoints
app.include_router(chat_router)
app.include_router(flashcard_router)


@app.get("/")
def root():
    return {"message": "AI Academic Tutor API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}