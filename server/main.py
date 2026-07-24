from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import active routers
from routers.flashcards import router as flashcards_router
from routers.chat import router as chat_router

app = FastAPI(
    title="AI Academic Tutor API",
    version="1.0.0"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints
app.include_router(flashcards_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "message": "AI Academic Tutor API is running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }