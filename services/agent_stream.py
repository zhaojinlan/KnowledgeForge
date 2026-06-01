"""
Streaming event types for KnowledgeForge Agent.
Adapted from deep-code-agent tui/bridge/stream_handler.py pattern.

Converts LangGraph streaming output into structured events for WebSocket broadcast.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Literal


EventType = Literal[
    "thinking",
    "tool_call",
    "tool_result",
    "token",
    "complete",
    "error",
    "status",
]


@dataclass
class AgentEvent:
    """A structured event emitted during agent execution.

    Maps to the types used in deep-code-agent's AgentEvent:
    - thinking: Agent is reasoning about next steps
    - tool_call: Agent is invoking a tool
    - tool_result: Tool execution completed
    - token: Streaming LLM token output
    - complete: Agent finished the full response
    - error: An error occurred
    - status: General status update
    """

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["type"] = self.type
        return result

    @classmethod
    def thinking(cls, message: str, session_id: str = "") -> "AgentEvent":
        return cls(type="thinking", data={"message": message}, session_id=session_id)

    @classmethod
    def tool_call(cls, tool_name: str, tool_args: dict, session_id: str = "") -> "AgentEvent":
        return cls(
            type="tool_call",
            data={"tool_name": tool_name, "tool_args": tool_args},
            session_id=session_id,
        )

    @classmethod
    def tool_result(cls, tool_name: str, result: str, session_id: str = "") -> "AgentEvent":
        return cls(
            type="tool_result",
            data={"tool_name": tool_name, "result": result},
            session_id=session_id,
        )

    @classmethod
    def token(cls, content: str, session_id: str = "") -> "AgentEvent":
        return cls(type="token", data={"content": content}, session_id=session_id)

    @classmethod
    def complete(cls, full_response: str, tool_calls_count: int = 0, session_id: str = "") -> "AgentEvent":
        return cls(
            type="complete",
            data={"full_response": full_response, "tool_calls_count": tool_calls_count},
            session_id=session_id,
        )

    @classmethod
    def error(cls, message: str, details: str = "", session_id: str = "") -> "AgentEvent":
        return cls(
            type="error",
            data={"message": message, "details": details},
            session_id=session_id,
        )

    @classmethod
    def status(cls, message: str, session_id: str = "") -> "AgentEvent":
        return cls(type="status", data={"message": message}, session_id=session_id)
