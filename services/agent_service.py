"""
Core Knowledge Agent Service for KnowledgeForge.
Adapted from deep-code-agent code_agent.py.

Provides the main agent factory using LangGraph's create_react_agent with:
- Tool calling loop (ReAct pattern)
- Subagent delegation via tool calls
- Streaming support via async generators
- HITL interrupt support
- Session management with MongoDB persistence and checkpointing.
"""

import logging
from typing import Any, AsyncGenerator, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from core.config import settings
from core.database import messages_collection
from services.agent_tools import make_agent_tools
from services.agent_prompts import get_system_prompt
from services.agent_stream import AgentEvent

logger = logging.getLogger(__name__)


class KnowledgeAgentService:
    """Main agent service for KnowledgeForge intelligent agent interactions.

    Wraps a LangGraph react agent with tools for knowledge base operations,
    session checkpointing, and streaming event output.
    """

    def __init__(self, max_iterations: int = 10):
        self.max_iterations = max_iterations
        self._checkpointer = InMemorySaver()
        self._agent = self._build_agent()
        logger.info("KnowledgeAgentService initialized")

    def _build_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.model,
            api_key=settings.api_key,
            base_url=settings.base_url,
            temperature=0.1,
        )

    def _build_agent(self):
        llm = self._build_llm()
        tools = make_agent_tools()
        system_prompt = get_system_prompt()

        return create_react_agent(
            model=llm,
            tools=tools,
            prompt=SystemMessage(content=system_prompt),
            checkpointer=self._checkpointer,
            version="v2",
        )

    async def _load_session_messages(self, session_id: str) -> list:
        """Load historical messages from MongoDB for a session."""
        messages = []
        try:
            cursor = messages_collection.find({"session_id": session_id}).sort("timestamp", 1)
            async for msg in cursor:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role in ("ai", "assistant"):
                    messages.append(AIMessage(content=content))
            if messages:
                logger.info(f"Loaded {len(messages)} historical messages for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to load session {session_id} history: {e}")
        return messages

    async def ainvoke(self, user_message: str, session_id: str) -> str:
        """Non-streaming agent invocation. Returns the full response text."""
        history = await self._load_session_messages(session_id)
        history.append(HumanMessage(content=user_message))

        config = {"configurable": {"thread_id": session_id}}
        result = await self._agent.ainvoke(
            {"messages": history},
            config=config,
        )

        messages = result.get("messages", [])
        last_ai = None
        for m in reversed(messages):
            if isinstance(m, AIMessage) and m.content:
                last_ai = m
                break

        response = last_ai.content if last_ai else ""
        return response

    async def astream_events(
        self,
        user_message: str,
        session_id: str,
    ) -> AsyncGenerator[AgentEvent, None]:
        """Stream agent execution as AgentEvent objects.

        Yields token, tool_call, tool_result, and complete events
        as the agent processes the user message. Mirrors the dual-mode
        streaming pattern from deep-code-agent cli.py.
        """
        history = await self._load_session_messages(session_id)
        history.append(HumanMessage(content=user_message))

        config = {"configurable": {"thread_id": session_id}}
        state = {"messages": history}

        full_response_parts: list[str] = []
        tool_calls_count = 0

        try:
            async for mode, chunk in self._agent.astream(
                state,
                config=config,
                stream_mode=["messages", "updates"],
            ):
                if mode == "messages":
                    token, metadata = chunk
                    if hasattr(token, "content") and token.content:
                        content = token.content
                        if isinstance(content, str) and content.strip():
                            full_response_parts.append(content)
                            yield AgentEvent.token(content, session_id=session_id)

                elif mode == "updates":
                    for _node_name, node_output in chunk.items():
                        if not node_output or not isinstance(node_output, dict):
                            continue

                        msgs = node_output.get("messages", [])
                        if not msgs:
                            continue

                        last_msg = msgs[-1] if isinstance(msgs, list) else msgs

                        if isinstance(last_msg, AIMessage):
                            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                for tc in last_msg.tool_calls:
                                    yield AgentEvent.tool_call(
                                        tool_name=tc.get("name", "unknown"),
                                        tool_args=tc.get("args", {}),
                                        session_id=session_id,
                                    )

                        elif hasattr(last_msg, "name") and hasattr(last_msg, "content"):
                            tool_name = getattr(last_msg, "name", "unknown")
                            content = getattr(last_msg, "content", "")
                            tool_calls_count += 1
                            yield AgentEvent.tool_result(
                                tool_name=tool_name,
                                result=str(content)[:2000],
                                session_id=session_id,
                            )

            full_text = "".join(full_response_parts)
            yield AgentEvent.complete(
                full_response=full_text,
                tool_calls_count=tool_calls_count,
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Agent streaming error: {e}", exc_info=True)
            yield AgentEvent.error(
                message=f"智能体执行错误: {str(e)}",
                details=str(e),
                session_id=session_id,
            )


agent_service = KnowledgeAgentService()


def create_knowledge_agent(max_iterations: int = 10) -> KnowledgeAgentService:
    """Factory function (mirrors deep-code-agent create_code_agent pattern)."""
    return KnowledgeAgentService(max_iterations=max_iterations)
