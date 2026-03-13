# agent/tools/hub_client.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("AI_DEVS_BASE_URL", "https://hub.ag3nts.org")
API_KEY = os.getenv("AI_DEVS_API_KEY")


def _inject_key(endpoint: str) -> str:
    """Replace any API key placeholder in the path."""
    return endpoint.replace("tutaj-twój-klucz", API_KEY)


async def hub_post(endpoint: str, payload: dict) -> dict:
    url = f"{BASE_URL}/{_inject_key(endpoint).lstrip('/')}"
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json={**payload, "apikey": API_KEY})
        r.raise_for_status()
    content_type = r.headers.get("content-type", "")
    return r.json() if "application/json" in content_type else r.text


async def hub_get(endpoint: str, params: dict | None = None) -> dict:
    url = f"{BASE_URL}/{_inject_key(endpoint).lstrip('/')}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params={"apikey": API_KEY, **(params or {})})
        r.raise_for_status()
    content_type = r.headers.get("content-type", "")
    return r.json() if "application/json" in content_type else r.text
