# tests/test_calculator.py
import pytest

from core.types import ToolCall
from tools.calculator import CalculatorTool


@pytest.fixture
def tool() -> CalculatorTool:
    return CalculatorTool()


@pytest.mark.asyncio
async def test_basic_arithmetic(tool):
    result = await tool.run({"expression": "(2 + 3) * 4"})
    assert result == "20.0"


@pytest.mark.asyncio
async def test_division(tool):
    result = await tool.run({"expression": "10 / 4"})
    assert result == "2.5"


@pytest.mark.asyncio
async def test_invalid_characters(tool):
    with pytest.raises(ValueError, match="Invalid characters"):
        await tool.run({"expression": "__import__('os').system('ls')"})


@pytest.mark.asyncio
async def test_safe_run_success(tool):
    tool_call = ToolCall(
        tool_call_id="test-001",
        tool_name="calculator",
        arguments={"expression": "2 + 2"},
    )
    result = await tool.safe_run(tool_call)
    assert result.output == "4.0"
    assert result.tool_call_id == "test-001"
    assert result.tool_name == "calculator"


@pytest.mark.asyncio
async def test_safe_run_error_returns_tool_result(tool):
    tool_call = ToolCall(
        tool_call_id="test-002",
        tool_name="calculator",
        arguments={"expression": "2 / 0"},
    )
    result = await tool.safe_run(tool_call)
    assert result.tool_call_id == "test-002"
    assert "Error" in result.output
