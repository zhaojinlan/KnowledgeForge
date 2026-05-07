# services/llm_service.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from typing import List
from schemas.chat import Message
from core.config import settings

class LLMService:
    def __init__(self, model: str, api_key: str, base_url: str):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7
        )

    # ✅ 注意：第一个参数是 self
    def chat(self, user_message: str, history: List[Message]) -> str:
        messages = []
        for msg in history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role in ["assistant", "ai"]:
                messages.append(AIMessage(content=msg.content))
        messages.append(HumanMessage(content=user_message))
        return self.llm.invoke(messages).content

# ✅ 创建并导出实例（关键！）
llm_service = LLMService(
    model=settings.model,
    api_key=settings.api_key,
    base_url=settings.base_url
)