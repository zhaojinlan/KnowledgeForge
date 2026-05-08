# schemas/chat.py
from pydantic import BaseModel, Field
from typing import List,Optional

class Message(BaseModel):
    role: str  # "user", "assistant", "ai"
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # 可选，不传则新建会话
    
class ChatResponse(BaseModel):
    response: str
    session_id: str