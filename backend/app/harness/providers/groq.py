import time
import httpx
from typing import List, Dict, Any, Optional
from app.harness.providers.base import BaseLLMProvider
from app.core.config import settings

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = model or settings.GROQ_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        start_time = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        choice = data["choices"][0]["message"]
        content = choice.get("content") or ""
        tool_calls = choice.get("tool_calls")
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)

        return {
            "content": content,
            "tool_calls": tool_calls,
            "provider": "groq",
            "model": self.model,
            "latency_ms": round(latency_ms, 2),
            "tokens_used": tokens
        }
