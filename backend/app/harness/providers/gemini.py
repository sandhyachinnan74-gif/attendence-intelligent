import time
import httpx
from typing import List, Dict, Any, Optional
from app.harness.providers.base import BaseLLMProvider
from app.core.config import settings

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        start_time = time.perf_counter()
        # Convert OpenAI-style messages to Gemini format
        gemini_contents = []
        system_instruction = None
        for m in messages:
            role = m["role"]
            content = m.get("content") or ""
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            else:
                gemini_role = "user" if role == "user" else "model"
                gemini_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": gemini_contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        candidates = data.get("candidates", [])
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                content = parts[0].get("text", "")

        return {
            "content": content,
            "tool_calls": None,
            "provider": "gemini",
            "model": self.model,
            "latency_ms": round(latency_ms, 2),
            "tokens_used": data.get("usageMetadata", {}).get("totalTokenCount", 0)
        }
