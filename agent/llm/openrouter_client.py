from __future__ import annotations

import json

from openai import AsyncOpenAI

from agent.core.types import AgentResponse, Message, ToolCall, ToolSpec


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        app_name: str = "agent_white_label",
        site_url: str = "http://localhost:8000",
    ) -> None:
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": site_url,
                "X-Title": app_name,
            },
        )
        self.model = model

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
        # ← WSZYSTKIE główne parametry OpenRouter/OpenAI:
        temperature: float | None = None,        # 0.0-2.0, domyślnie 1.0
        max_tokens: int | None = None,           # max output tokens
        top_p: float | None = None,              # 0.0-1.0, domyślnie 1.0
        frequency_penalty: float | None = None,  # -2.0-2.0, domyślnie 0.0
        presence_penalty: float | None = None,   # -2.0-2.0, domyślnie 0.0
        top_k: int | None = None,                # model-specific
        tool_choice: str | None = None,          # "auto", "none", "required"
        stream: bool = False,
    ) -> AgentResponse:
        api_messages = []

        for m in messages:
            item = {"role": m.role, "content": m.content}
            if m.role == "tool":
                if m.name:
                    item["name"] = m.name
                if m.tool_call_id:
                    item["tool_call_id"] = m.tool_call_id
            if m.role == "assistant" and m.tool_calls:
                item["tool_calls"] = [
                    {
                        "id": tc.tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tc.tool_name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in m.tool_calls
                ]
            api_messages.append(item)

        api_tools = []
        if tools:
            for tool in tools:
                api_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.input_schema,
                        },
                    }
                )

        # ← Jawny payload z WSZYSTKIMI parametrami
        params = {
            "model": self.model,
            "messages": api_messages,
            "tools": api_tools or None,
            "tool_choice": tool_choice or ("auto" if api_tools else None),
            "stream": stream,
        }

        # Dodaj parametry modelu jeśli podane
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
        if top_p is not None:
            params["top_p"] = top_p
        if frequency_penalty is not None:
            params["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            params["presence_penalty"] = presence_penalty
        if top_k is not None:
            params["top_k"] = top_k

        response = await self.client.chat.completions.create(**params)

        msg = response.choices[0].message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                tool_calls.append(
                    ToolCall(
                        tool_call_id=tc.id,
                        tool_name=tc.function.name,
                        arguments=args,
                    )
                )

        return AgentResponse(
            output_text=msg.content or "",
            tool_calls=tool_calls,
            raw=response.model_dump(),
        )
