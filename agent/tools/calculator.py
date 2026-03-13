# tools/calculator.py
from __future__ import annotations

from typing import Any

from tools.base import BaseTool


class CalculatorTool(BaseTool):

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Evaluates a basic arithmetic expression and returns the result. "
            "Supports +, -, *, / and parentheses. Example: '(2 + 3) * 4'."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "An arithmetic expression to evaluate, e.g. '(2 + 3) * 4'",
                }
            },
            "required": ["expression"],
        }

    async def run(self, arguments: dict[str, Any]) -> str:
        expression = arguments["expression"]
        return str(self._safe_eval(expression))

    def _safe_eval(self, expression: str) -> float:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            raise ValueError(f"Invalid characters in expression: '{expression}'")
        return float(eval(expression))  # noqa: S307
