import time
import json
from typing import List, Dict, Any, Optional
from app.harness.providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    def __init__(self, model: str = "attendai-mock-engine"):
        self.model = model

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        last_message = messages[-1]
        content = (last_message.get("content") or "").lower()

        # Check if previous message had tool results
        has_tool_results = any(m.get("role") == "tool" for m in messages)
        tool_calls = None
        reply = ""

        if has_tool_results:
            # Synthesize answer from tool output
            tool_msg = next((m for m in reversed(messages) if m.get("role") == "tool"), None)
            tool_content = tool_msg.get("content", "{}") if tool_msg else "{}"
            reply = f"Based on verified database records: {tool_content}. All metrics have been retrieved via authorized backend tools."
        elif "late" in content or "tardy" in content:
            tool_calls = [{
                "id": "call_late_1",
                "type": "function",
                "function": {
                    "name": "get_late_arrivals",
                    "arguments": json.dumps({"limit": 10})
                }
            }]
            reply = "I will check the attendance records for recent late arrivals."
        elif "policy" in content or "handbook" in content or "guideline" in content:
            tool_calls = [{
                "id": "call_policy_1",
                "type": "function",
                "function": {
                    "name": "search_attendance_policy",
                    "arguments": json.dumps({"query": content})
                }
            }]
            reply = "Searching official workforce policy documentation."
        elif "overtime" in content:
            tool_calls = [{
                "id": "call_ot_1",
                "type": "function",
                "function": {
                    "name": "get_employee_overtime",
                    "arguments": json.dumps({"days": 30})
                }
            }]
            reply = "Querying overtime calculations from authorized records."
        elif "my attendance" in content or "my hours" in content or "my record" in content:
            tool_calls = [{
                "id": "call_my_att_1",
                "type": "function",
                "function": {
                    "name": "get_my_attendance",
                    "arguments": json.dumps({"days": 14})
                }
            }]
            reply = "Retrieving your personal verified attendance history."
        elif "anomaly" in content or "anomalies" in content or "flag" in content:
            tool_calls = [{
                "id": "call_anom_1",
                "type": "function",
                "function": {
                    "name": "get_anomaly_reports",
                    "arguments": json.dumps({"status": "pending"})
                }
            }]
            reply = "Fetching anomaly investigation flags."
        elif "department" in content:
            tool_calls = [{
                "id": "call_dept_1",
                "type": "function",
                "function": {
                    "name": "get_department_analytics",
                    "arguments": json.dumps({})
                }
            }]
            reply = "Fetching department analytics."
        else:
            reply = "I am AttendAI Assistant, connected to authorized workforce databases. You can ask me about employee attendance, late arrival trends, overtime statistics, anomaly reports, or HR policies."

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "content": reply,
            "tool_calls": tool_calls,
            "provider": "mock",
            "model": self.model,
            "latency_ms": round(max(5.0, latency_ms), 2),
            "tokens_used": len(reply.split()) * 2
        }
