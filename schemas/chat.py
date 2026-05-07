# schemas/chat.py
from pydantic import BaseModel, Field
from typing import List

class Message(BaseModel):
    role: str  # "user", "assistant", "ai"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[Message] = Field(default_factory=list)

class ChatResponse(BaseModel):
    response: str