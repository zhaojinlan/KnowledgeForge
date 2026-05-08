# services/llm_service.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict
from schemas.chat import Message
from core.config import settings
import uuid


class LLMService:
    def __init__(self, model: str, api_key: str, base_url: str):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        # 存储每个 session_id 的聊天历史
        self.sessions: Dict[str, List] = {}

    def _get_session_history(self, session_id: str) -> List:
        """获取指定会话的历史消息（LangChain 格式）"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def chat(self, user_message: str, session_id: str) -> str:
        """
        基于 session_id 进行会话隔离
        """
        messages = self._get_session_history(session_id)

        # 添加当前用户消息
        messages.append(HumanMessage(content=user_message))

        # 调用模型
        ai_message = self.llm.invoke(messages).content

        # 保存 AI 回复到历史
        messages.append(AIMessage(content=ai_message))

        return ai_message

    def clear_session(self, session_id: str):
        """清除某个会话的历史"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def new_session(self) -> str:
        """创建一个新的会话 ID"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id


# ✅ 创建并导出单例服务（但内部管理多 session）
llm_service = LLMService(
    model=settings.model,
    api_key=settings.api_key,
    base_url=settings.base_url
)
