"""Minimal OpenAI-compatible Chat Completions client (httpx)."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from config.settings import get_settings


@dataclass
class ChatClient:
    api_key: str
    base_url: str
    model: str
    timeout_sec: float = 120.0

    async def complete(self, prompt: str, *, temperature: float = 0.2) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return str(data["choices"][0]["message"]["content"])


def get_crag_chat_client() -> ChatClient | None:
    s = get_settings()
    if not s.openai_api_key:
        return None
    return ChatClient(
        api_key=s.openai_api_key,
        base_url=s.openai_base_url,
        model=s.openai_crag_model,
    )


def get_orchestrator_chat_client() -> ChatClient | None:
    s = get_settings()
    if not s.openai_api_key:
        return None
    return ChatClient(
        api_key=s.openai_api_key,
        base_url=s.openai_base_url,
        model=s.openai_orchestrator_model,
    )
