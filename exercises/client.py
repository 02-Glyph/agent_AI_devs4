# exercises/client.py
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("AI_DEVS_BASE_URL", "https://hub.ag3nts.org")
API_KEY = os.getenv("AI_DEVS_API_KEY")


async def post(endpoint: str, payload: dict) -> dict:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json={**payload, "apikey": API_KEY})
        response.raise_for_status()
        return response.json()


async def get(endpoint: str, params: dict | None = None) -> dict:
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url, params={"apikey": API_KEY, **(params or {})}
        )
        response.raise_for_status()
        return response.json()
