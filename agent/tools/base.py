# tools/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.types import ToolCall, ToolResult, ToolSpec


class BaseTool(ABC):
    """Base class for all tools. Inherit from this and implement name, description, input_schema, and run()."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]: ...

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )

    @abstractmethod
    async def run(self, arguments: dict[str, Any]) -> str:
        """Execute the tool logic. Return raw string output."""
        ...

    async def safe_run(self, tool_call: ToolCall) -> ToolResult:
        """Wraps run() with error handling. Always use this in the loop."""
        try:
            output = await self.run(tool_call.arguments)
        except Exception as e:
            output = f"Error: {e}"

        return ToolResult(
            tool_name=self.name,
            output=output,
            tool_call_id=tool_call.tool_call_id,
        )
