from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from ..services.groq_client import (
        process_chat_message,
        list_all_conversations,
        load_conversation,
    )
except ImportError:
    from services.groq_client import (
        process_chat_message,
        list_all_conversations,
        load_conversation,
    )

router = APIRouter()


class ChatRequest(BaseModel):
    chat_name: str = "default"
    message: str


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    ai_reply = process_chat_message(request.chat_name, request.message)
    return {"response": ai_reply}


@router.get("/conversations")
async def get_conversations():
    """Returns list of available chat sessions."""
    return {"conversations": list_all_conversations()}


@router.get("/conversations/{chat_name}")
async def get_conversation_history(chat_name: str):
    """Returns stored conversation history for a given chat name."""
    return load_conversation(chat_name)