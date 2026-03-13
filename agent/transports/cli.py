# transports/cli.py
from __future__ import annotations

import asyncio

from agent.agents.assistant import AssistantAgent
from agent.app.config import get_settings
from agent.llm import get_llm_client
from agent.tools.calculator import CalculatorTool
from agent.tools.registry import ToolRegistry


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
