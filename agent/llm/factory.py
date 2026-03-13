# agent/llm/factory.py
import os
from .openrouter_client import OpenRouterClient
from .openai_client import OpenAIClient

def create_llm_client() -> OpenRouterClient | OpenAIClient:
    llm_provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
    
    if llm_provider == "openrouter":
        return OpenRouterClient(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        )
    elif llm_provider == "openai":
        return OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {llm_provider}")
