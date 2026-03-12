# core/orchestrator.py
"""
Orchestrator — multi-agent coordination layer.

Currently a placeholder. Will be expanded when multiple agents are needed.

Planned responsibilities:
- Route tasks to the appropriate agent
- Pass state/context between agents
- Aggregate results from parallel agent runs
- Handle MCP tool server coordination
"""
from __future__ import annotations

from agents.assistant import AssistantAgent
from core.types import AgentResponse, AgentState


class Orchestrator:
    def __init__(self) -> None:
        self._agents: dict[str, AssistantAgent] = {}

    def register(self, name: str, agent: AssistantAgent) -> None:
        if name in self._agents:
            raise ValueError(f"Agent '{name}' is already registered.")
        self._agents[name] = agent

    def get(self, name: str) -> AssistantAgent | None:
        return self._agents.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._agents

    def __len__(self) -> int:
        return len(self._agents)
