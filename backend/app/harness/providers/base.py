from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Returns a dict:
        {
            "content": str,
            "tool_calls": Optional[List[Dict[str, Any]]],
            "provider": str,
            "model": str,
            "latency_ms": float,
            "tokens_used": int
        }
        """
        pass
