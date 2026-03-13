# llm/__init__.py
from agent.app.config import Settings, get_settings
from agent.llm.openai_client import OpenAIClient
from agent.llm.openrouter_client import OpenRouterClient



def get_llm_client(settings: Settings | None = None) -> OpenAIClient | OpenRouterClient:
    s = settings or get_settings()
    if s.llm_provider == "openai":
        return OpenAIClient(
            api_key=s.openai_api_key,
            model=s.openai_model,
        )
    return OpenRouterClient(
        api_key=s.openrouter_api_key,
        model=s.openrouter_model,
        base_url=s.openrouter_base_url,
        app_name=s.app_name,
        site_url=s.site_url,
    )
