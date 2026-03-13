# agent/tools/fetch_url.py
import httpx


async def fetch_url(url: str, params: dict | None = None) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params or {})
        r.raise_for_status()
        content_type = r.headers.get("content-type", "")
        return r.json() if "application/json" in content_type else r.text

