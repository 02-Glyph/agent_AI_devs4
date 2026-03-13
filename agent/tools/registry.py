# tools/registry.py
from __future__ import annotations

from agent.core.types import ToolCall, ToolResult, ToolSpec
from agent.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered. "
                "Use a unique name or deregister the existing tool first."
            )
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_specs(self) -> list[ToolSpec]:
        return [tool.spec for tool in self._tools.values()]

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        tool = self._tools.get(tool_call.tool_name)
        if tool is None:
            return ToolResult(
                tool_name=tool_call.tool_name,
                output=f"Error: tool '{tool_call.tool_name}' not found in registry",
                tool_call_id=tool_call.tool_call_id,
            )
        return await tool.safe_run(tool_call)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
