from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class ToolCall:
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    tool_name: str
    output: str
    tool_call_id: str | None = None


@dataclass
class Message:
    role: str
    content: str | None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class AgentState:
    messages: list[Message] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    output_text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict[str, Any] | None = None


class Tool(Protocol):
    @property
    def spec(self) -> ToolSpec: ...

    async def run(self, arguments: dict[str, Any]) -> ToolResult: ...


class LLMClient(Protocol):
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> AgentResponse: ...
