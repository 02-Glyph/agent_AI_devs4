# tests/test_agent.py
import pytest
from unittest.mock import AsyncMock

from agent.agents.assistant import AssistantAgent
from agent.core.types import AgentResponse, AgentState, Message
from agent.tools.registry import ToolRegistry


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.generate = AsyncMock(return_value=AgentResponse(
        output_text="Hello, how can I help?",
        tool_calls=[],
    ))
    return client


@pytest.fixture
def agent(mock_client):
    return AssistantAgent(
        client=mock_client,
        registry=ToolRegistry(),
        system_prompt="You are a helpful assistant.",
    )


@pytest.mark.asyncio
async def test_fresh_state_on_new_run(agent, mock_client):
    response = await agent.run("Hi")
    assert response.output_text == "Hello, how can I help?"
    messages = mock_client.generate.call_args[1]["messages"]
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert messages[1].content == "Hi"


@pytest.mark.asyncio
async def test_state_injection(agent, mock_client):
    existing_state = AgentState(messages=[
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="First message"),
        Message(role="assistant", content="First response"),
    ])

    captured_messages = []

    async def capture_generate(messages, tools=None):
        captured_messages.extend(messages)
        return AgentResponse(output_text="Hello, how can I help?", tool_calls=[])

    mock_client.generate = capture_generate

    await agent.run("Second message", state=existing_state)

    assert len(captured_messages) == 4
    assert captured_messages[-1].role == "user"
    assert captured_messages[-1].content == "Second message"
    assert len(existing_state.messages) == 5
    assert existing_state.messages[-1].role == "assistant"


@pytest.mark.asyncio
async def test_max_iterations_raises(mock_client):
    mock_client.generate = AsyncMock(return_value=AgentResponse(
        output_text="",
        tool_calls=[],
    ))
    agent = AssistantAgent(client=mock_client, registry=ToolRegistry())
    response = await agent.run("Hi")
    assert response.output_text == ""
