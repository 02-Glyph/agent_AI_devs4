# app/main.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.assistant import AssistantAgent
from app.config import get_settings
from llm import get_llm_client
from tools.calculator import CalculatorTool
from tools.registry import ToolRegistry


# --- setup ---

settings = get_settings()

registry = ToolRegistry()
registry.register(CalculatorTool())

agent = AssistantAgent(
    client=get_llm_client(),
    registry=registry,
    system_prompt="You are a helpful assistant.",
)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


# --- schemas ---

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# --- routes ---

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "provider": settings.llm_provider}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        response = await agent.run(request.message)
        return ChatResponse(reply=response.output_text)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
