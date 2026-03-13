# agents/assistant.py
from __future__ import annotations

from agent.core.loop import run_loop
from agent.core.types import AgentResponse, AgentState, LLMClient, Message
from agent.tools.registry import ToolRegistry


class AssistantAgent:
    def __init__(
        self,
        client: LLMClient,
        registry: ToolRegistry,
        system_prompt: str = "You are a helpful assistant.",
        max_iterations: int = 10,
    ) -> None:
        self.client = client
        self.registry = registry
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    def _fresh_state(self, user_message: str) -> AgentState:
        return AgentState(
            messages=[
                Message(role="system", content=self.system_prompt),
                Message(role="user", content=user_message),
            ]
        )

    def _append_user_message(self, state: AgentState, user_message: str) -> AgentState:
        state.messages.append(Message(role="user", content=user_message))
        return state

    async def run(
        self,
        user_message: str,
        state: AgentState | None = None,
    ) -> AgentResponse:
        if state is None:
            state = self._fresh_state(user_message)
        else:
            state = self._append_user_message(state, user_message)

        return await run_loop(
            client=self.client,
            state=state,
            registry=self.registry,
            max_iterations=self.max_iterations,
        )
