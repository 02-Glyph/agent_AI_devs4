# transports/cli.py
from __future__ import annotations

import asyncio

from agents.assistant import AssistantAgent
from app.config import get_settings
from llm import get_llm_client
from tools.calculator import CalculatorTool
from tools.registry import ToolRegistry


async def main() -> None:
    settings = get_settings()

    registry = ToolRegistry()
    registry.register(CalculatorTool())

    agent = AssistantAgent(
        client=get_llm_client(settings),
        registry=registry,
    )

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        response = await agent.run(user_input)
        print(f"Agent: {response.output_text}")


if __name__ == "__main__":
    asyncio.run(main())
