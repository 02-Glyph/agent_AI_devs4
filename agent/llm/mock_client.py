import re

from agent.core.types import AgentResponse, Message, ToolCall, ToolSpec


class MockLLMClient:
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> AgentResponse:
        last_user = next((m for m in reversed(messages) if m.role == "user"), None)
        last_tool = next((m for m in reversed(messages) if m.role == "tool"), None)

        if last_tool is not None:
            return AgentResponse(output_text=f"Tool result: {last_tool.content}")

        if not last_user:
            return AgentResponse(output_text="Hello.")

        text = last_user.content.strip()

        calc_match = re.search(r"calculate\s+(.+)$", text, re.IGNORECASE)
        if calc_match:
            expr = calc_match.group(1).strip()
            return AgentResponse(
                output_text="",
                tool_calls=[ToolCall(tool_name="calculator", arguments={"expression": expr})],
            )

        return AgentResponse(output_text=f"You said: {text}")
