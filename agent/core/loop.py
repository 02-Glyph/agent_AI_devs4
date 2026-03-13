# core/loop.py
from __future__ import annotations

from agent.core.types import AgentResponse, AgentState, LLMClient, Message
from agent.tools.registry import ToolRegistry


async def run_loop(
    client: LLMClient,
    state: AgentState,
    registry: ToolRegistry,
    max_iterations: int = 10,
) -> AgentResponse:
    for _ in range(max_iterations):
        response = await client.generate(
            messages=state.messages,
            tools=registry.get_specs() or None,
        )

        if not response.tool_calls:
            state.messages.append(Message(
                role="assistant",
                content=response.output_text,
            ))
            return response

        state.messages.append(Message(
            role="assistant",
            content=response.output_text,
            tool_calls=response.tool_calls,
        ))

        for tool_call in response.tool_calls:
            result = await registry.execute(tool_call)
            state.messages.append(Message(
                role="tool",
                content=result.output,
                name=result.tool_name,
                tool_call_id=result.tool_call_id,
            ))

    raise RuntimeError(
        f"Agent loop reached max_iterations={max_iterations} without a final response."
    )
