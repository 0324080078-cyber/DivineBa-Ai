import httpx
from typing import List, Dict

from app.core.config import settings
from app.services.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI provider (default). Talks to api.openai.com via httpx."""

    BASE_URL = "https://api.openai.com/v1"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Copy .env.example → .env and fill in your key."
            )
        self._headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

    async def chat(self, messages: List[Dict[str, str]], model: str) -> str:
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._headers,
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    async def embed(self, texts: List[str], model: str) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.BASE_URL}/embeddings",
                headers=self._headers,
                json={"model": model, "input": texts},
            )
            r.raise_for_status()
            data = r.json()
            return [item["embedding"] for item in data["data"]]
