from pathlib import Path
import textwrap

ROOT = Path(".").resolve()

FILES = {
    "pyproject.toml": """
        [build-system]
        requires = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "white-label-agent"
        version = "0.1.0"
        description = "Minimal white-label AI agent skeleton in pure Python"
        readme = "README.md"
        requires-python = ">=3.11"
        dependencies = []

        [project.optional-dependencies]
        dev = ["pytest>=8.0"]

        [tool.pytest.ini_options]
        testpaths = ["tests"]
    """,
    "README.md": """
        # White Label Agent

        Minimal agent skeleton in pure Python:
        - provider-agnostic LLM client interface
        - tool registry
        - think-act loop
        - orchestrator stub
        - CLI entrypoint
    """,
    ".gitignore": """
        .venv/
        __pycache__/
        *.pyc
        .pytest_cache/
    """,
    "app/__init__.py": "",
    "app/main.py": """
        import asyncio

        from agents.assistant import AssistantAgent
        from core.loop import AgentLoop
        from core.types import AgentState
        from llm.mock_client import MockLLMClient
        from tools.calculator import CalculatorTool
        from tools.registry import ToolRegistry


        async def main() -> None:
            tools = ToolRegistry()
            tools.register(CalculatorTool())

            llm = MockLLMClient()
            loop = AgentLoop(llm=llm, tools=tools, max_steps=5)

            agent = AssistantAgent(
                loop=loop,
                system_prompt=(
                    "You are a helpful assistant. "
                    "Use tools when needed. Keep answers concise."
                ),
            )

            state = AgentState()

            print("White Label Agent CLI")
            print("Type 'exit' to quit. Example: calculate 2 + 2\\n")

            while True:
                user_input = input("You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    break

                response = await agent.respond(user_input, state)
                print(f"Agent: {response}\\n")


        if __name__ == "__main__":
            asyncio.run(main())
    """,
    "core/__init__.py": "",
    "core/types.py": """
        from __future__ import annotations

        from dataclasses import dataclass, field
        from typing import Any, Protocol


        @dataclass
        class Message:
            role: str
            content: str
            name: str | None = None


        @dataclass
        class ToolSpec:
            name: str
            description: str
            input_schema: dict[str, Any]


        @dataclass
        class ToolCall:
            tool_name: str
            arguments: dict[str, Any]


        @dataclass
        class ToolResult:
            tool_name: str
            output: str


        @dataclass
        class AgentState:
            messages: list[Message] = field(default_factory=list)
            metadata: dict[str, Any] = field(default_factory=dict)


        @dataclass
        class AgentResponse:
            output_text: str
            tool_calls: list[ToolCall] = field(default_factory=list)
            raw: dict[str, Any] | None = None


        class Tool(Protocol):
            spec: ToolSpec

            async def run(self, arguments: dict[str, Any]) -> ToolResult:
                ...


        class LLMClient(Protocol):
            async def generate(
                self,
                messages: list[Message],
                tools: list[ToolSpec] | None = None,
            ) -> AgentResponse:
                ...
    """,
    "core/loop.py": """
        from core.types import AgentState, Message, LLMClient
        from tools.registry import ToolRegistry


        class AgentLoop:
            def __init__(self, llm: LLMClient, tools: ToolRegistry, max_steps: int = 5) -> None:
                self.llm = llm
                self.tools = tools
                self.max_steps = max_steps

            async def run(self, state: AgentState) -> str:
                for _ in range(self.max_steps):
                    response = await self.llm.generate(
                        messages=state.messages,
                        tools=self.tools.list_specs(),
                    )

                    if not response.tool_calls:
                        state.messages.append(Message(role="assistant", content=response.output_text))
                        return response.output_text

                    for call in response.tool_calls:
                        tool = self.tools.get(call.tool_name)
                        result = await tool.run(call.arguments)
                        state.messages.append(
                            Message(role="tool", name=result.tool_name, content=result.output)
                        )

                fallback = "I could not complete the task within the allowed steps."
                state.messages.append(Message(role="assistant", content=fallback))
                return fallback
    """,
    "core/orchestrator.py": """
        from core.types import AgentState


        class Orchestrator:
            def __init__(self, default_agent) -> None:
                self.default_agent = default_agent
                self.agents: dict[str, object] = {"default": default_agent}

            def register(self, name: str, agent: object) -> None:
                self.agents[name] = agent

            async def handle(self, user_input: str, state: AgentState) -> str:
                return await self.default_agent.respond(user_input, state)
    """,
    "agents/__init__.py": "",
    "agents/assistant.py": """
        from core.loop import AgentLoop
        from core.types import AgentState, Message


        class AssistantAgent:
            def __init__(self, loop: AgentLoop, system_prompt: str) -> None:
                self.loop = loop
                self.system_prompt = system_prompt

            async def respond(self, user_input: str, state: AgentState | None = None) -> str:
                state = state or AgentState()
                if not state.messages:
                    state.messages.append(Message(role="system", content=self.system_prompt))
                state.messages.append(Message(role="user", content=user_input))
                return await self.loop.run(state)
    """,
    "llm/__init__.py": "",
    "llm/mock_client.py": """
        import re

        from core.types import AgentResponse, Message, ToolCall, ToolSpec


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

                calc_match = re.search(r"calculate\\s+(.+)$", text, re.IGNORECASE)
                if calc_match:
                    expr = calc_match.group(1).strip()
                    return AgentResponse(
                        output_text="",
                        tool_calls=[ToolCall(tool_name="calculator", arguments={"expression": expr})],
                    )

                return AgentResponse(output_text=f"You said: {text}")
    """,
    "tools/__init__.py": "",
    "tools/base.py": """
        from core.types import ToolResult, ToolSpec


        class BaseTool:
            spec: ToolSpec

            async def run(self, arguments: dict) -> ToolResult:
                raise NotImplementedError
    """,
    "tools/registry.py": """
        from tools.base import BaseTool


        class ToolRegistry:
            def __init__(self) -> None:
                self._tools: dict[str, BaseTool] = {}

            def register(self, tool: BaseTool) -> None:
                if tool.spec.name in self._tools:
                    raise ValueError(f"Tool already registered: {tool.spec.name}")
                self._tools[tool.spec.name] = tool

            def get(self, name: str) -> BaseTool:
                if name not in self._tools:
                    raise KeyError(f"Unknown tool: {name}")
                return self._tools[name]

            def list_specs(self) -> list:
                return [tool.spec for tool in self._tools.values()]
    """,
    "tools/calculator.py": """
        from core.types import ToolResult, ToolSpec
        from tools.base import BaseTool


        class CalculatorTool(BaseTool):
            spec = ToolSpec(
                name="calculator",
                description="Evaluate a simple arithmetic expression.",
                input_schema={
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                    "additionalProperties": False,
                },
            )

            async def run(self, arguments: dict) -> ToolResult:
                expr = arguments["expression"]
                allowed = set("0123456789+-*/(). ")
                if any(ch not in allowed for ch in expr):
                    raise ValueError("Unsupported characters in expression")

                result = eval(expr, {"__builtins__": {}}, {})
                return ToolResult(tool_name=self.spec.name, output=str(result))
    """,
    "tests/test_calculator.py": """
        import asyncio

        from tools.calculator import CalculatorTool


        def test_calculator_tool():
            tool = CalculatorTool()
            result = asyncio.run(tool.run({"expression": "2 + 3 * 4"}))
            assert result.output == "14"
    """,
    "tests/test_agent.py": """
        import asyncio

        from agents.assistant import AssistantAgent
        from core.loop import AgentLoop
        from core.types import AgentState
        from llm.mock_client import MockLLMClient
        from tools.calculator import CalculatorTool
        from tools.registry import ToolRegistry


        def test_agent_calculation_flow():
            tools = ToolRegistry()
            tools.register(CalculatorTool())

            agent = AssistantAgent(
                loop=AgentLoop(llm=MockLLMClient(), tools=tools),
                system_prompt="You are helpful.",
            )

            state = AgentState()
            output = asyncio.run(agent.respond("calculate 2 + 2", state))
            assert "4" in output
    """,
}

def write_file(path_str: str, content: str) -> None:
    path = ROOT / path_str
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def main() -> None:
    for path_str, content in FILES.items():
        write_file(path_str, content)

    print("Repo skeleton created.")
    print("Next:")
    print("  python -m venv .venv")
    print("  source .venv/bin/activate   # on Windows: .venv\\\\Scripts\\\\activate")
    print("  pip install -e .[dev]")
    print("  pytest")
    print("  python -m app.main")


if __name__ == "__main__":
    main()