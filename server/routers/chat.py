from fastapi import APIRouter
from pydantic import BaseModel
# from services.groq_client import chat_with_tutorbot

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return {
        "response": "You are chatting with the bot!"
        # chat_with_tutorbot(request.chat_name, request.message)
    }