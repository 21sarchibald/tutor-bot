"""FastAPI application for the Quoria tutor and flashcard features."""

import sys
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    title="Quoria API",
    description="AI tutoring conversations and study flashcards generated from course materials.",
    version="1.0.0",
)

LOCAL_FRONTEND_ORIGINS = {
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5501",
}
configured_origins = {
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
}
FRONTEND_ORIGINS = configured_origins or LOCAL_FRONTEND_ORIGINS


class PrivateNetworkAccessMiddleware:
    """Allow browser PNA preflights from the configured Quoria frontend only."""

    def __init__(self, app, allowed_origins):
        self.app = app
        self.allowed_origins = allowed_origins

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            headers = dict(scope.get("headers", ()))
            origin = headers.get(b"origin", b"").decode("latin-1")
            requested = headers.get(b"access-control-request-private-network")
            if requested == b"true" and origin in self.allowed_origins:
                requested_headers = headers.get(
                    b"access-control-request-headers", b"content-type"
                )
                await send(
                    {
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [
                            (b"access-control-allow-origin", origin.encode("latin-1")),
                            (b"access-control-allow-methods", b"GET, POST, OPTIONS"),
                            (b"access-control-allow-headers", requested_headers),
                            (b"access-control-allow-private-network", b"true"),
                            (b"content-length", b"2"),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": b"OK"})
                return
        await self.app(scope, receive, send)


app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(FRONTEND_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    PrivateNetworkAccessMiddleware,
    allowed_origins=FRONTEND_ORIGINS,
)

app.include_router(chat.router)
app.include_router(flashcards.router)


@app.get("/", tags=["status"], include_in_schema=False)
def root():
    if CLIENT_DIR.is_dir():
        return FileResponse(CLIENT_DIR / "index.html")
    return {"message": "Quoria API is running."}


@app.get("/health", tags=["status"])
def health_check():
    return {"status": "healthy", "ai_configured": bool(os.getenv("GROQ_API_KEY"))}


CLIENT_DIR = SERVER_DIR.parent / "client"
if CLIENT_DIR.is_dir():
    app.mount("/", StaticFiles(directory=CLIENT_DIR, html=True), name="frontend")
