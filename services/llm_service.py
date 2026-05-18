# services/llm_service.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict
from schemas.chat import Message
from core.config import settings
from pymongo import MongoClient
import uuid
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, model: str, api_key: str, base_url: str, mongodb_uri: str, mongo_db_name: str = "chat_db"):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        self.sessions: Dict[str, List] = {}

        self._mongo_client = MongoClient(mongodb_uri)
        self._messages_collection = self._mongo_client[mongo_db_name]["messages"]

    def _load_session_from_db(self, session_id: str) -> List:
        messages = []
        try:
            cursor = self._messages_collection.find({"session_id": session_id}).sort("timestamp", 1)
            for msg in cursor:
                role = msg.get("role")
                content = msg.get("content")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role in ("ai", "assistant"):
                    messages.append(AIMessage(content=content))
            if messages:
                logger.info(f"Loaded {len(messages)} historical messages for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to load session {session_id} from DB: {e}")
        return messages

    def _get_session_history(self, session_id: str) -> List:
        if session_id not in self.sessions:
            self.sessions[session_id] = self._load_session_from_db(session_id)
        return self.sessions[session_id]

    def chat(self, user_message: str, session_id: str) -> str:
        messages = self._get_session_history(session_id)
        messages.append(HumanMessage(content=user_message))
        ai_message = self.llm.invoke(messages).content
        messages.append(AIMessage(content=ai_message))
        return ai_message

    def chat_with_context(self, user_message: str, session_id: str, rag_context: str = "") -> str:
        messages = self._get_session_history(session_id)
        if rag_context:
            system_prompt = (
                "请基于以下检索到的文档内容回答问题。如果文档中没有相关信息，请如实告知用户。\n\n"
                f"## 检索到的文档\n{rag_context}"
            )
            messages.append(HumanMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_message))
        ai_message = self.llm.invoke(messages).content
        messages.append(AIMessage(content=ai_message))
        return ai_message

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id


llm_service = LLMService(
    model=settings.model,
    api_key=settings.api_key,
    base_url=settings.base_url,
    mongodb_uri=settings.mongodb_uri,
)
