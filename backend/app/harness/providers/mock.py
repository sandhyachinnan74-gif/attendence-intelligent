import time
import json
import re
from typing import List, Dict, Any, Optional
from app.harness.providers.base import BaseLLMProvider
from app.harness.output_validator import OutputValidator

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider for offline development and regression tests.
    Generates structured enterprise markdown responses, valid tool calls, and handles follow-up reasoning.
    Never outputs raw JSON or unformatted data.
    """
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
        content = (last_message.get("content") or "").lower().strip()

        # Check if previous message had tool results
        tool_messages = [m for m in messages if m.get("role") == "tool"]
        tool_calls = None
        reply = ""

        if tool_messages:
            # Multi-turn tool synthesis: Combine tool results and format as clean Markdown
            synthesized_blocks = []
            for tm in tool_messages:
                raw_c = tm.get("content", "{}")
                try:
                    parsed = json.loads(raw_c) if isinstance(raw_c, str) else raw_c
                    synthesized_blocks.append(OutputValidator._format_parsed_json_to_markdown(parsed))
                except Exception:
                    synthesized_blocks.append(str(raw_c))

            reply = "\n\n---\n\n".join(synthesized_blocks)

        else:
            # Intent understanding & Tool Selection
            # Examine conversation history for follow-up context
            past_user_texts = [
                m.get("content", "").lower() for m in messages
                if m.get("role") == "user" and m != last_message
            ]
            last_user_context = past_user_texts[-1] if past_user_texts else ""

            # 1. Follow-up: "What about Engineering?" / "What about <dept>?"
            dept_match = re.search(r'what about ([a-zA-Z\s]+)\??', content)
            if dept_match and ("overtime" in last_user_context or "late" in last_user_context or "attendance" in last_user_context):
                target_dept = dept_match.group(1).strip().title()
                if "overtime" in last_user_context:
                    tool_calls = [{
                        "id": "call_ot_dept_1",
                        "type": "function",
                        "function": {
                            "name": "get_employee_overtime",
                            "arguments": json.dumps({"period": "last_month" if "last month" in last_user_context else "this_month", "department": target_dept})
                        }
                    }]
                    reply = f"Filtering overtime records for the {target_dept} department."
                elif "late" in last_user_context:
                    tool_calls = [{
                        "id": "call_late_dept_1",
                        "type": "function",
                        "function": {
                            "name": "get_late_arrivals",
                            "arguments": json.dumps({"period": "this_month", "department": target_dept, "group_by_employee": True})
                        }
                    }]
                    reply = f"Checking late arrivals for the {target_dept} department."
                else:
                    tool_calls = [{
                        "id": "call_att_dept_1",
                        "type": "function",
                        "function": {
                            "name": "get_attendance_summary",
                            "arguments": json.dumps({"period": "today", "department": target_dept})
                        }
                    }]
                    reply = f"Retrieving attendance summary for {target_dept}."

            # 2. Follow-up: "Show their employee details" / "Show profile for <name>"
            elif "details" in content or "profile" in content or "show their" in content:
                # Check for explicit name
                name_match = re.search(r'(?:for|of)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)', content)
                target_name = name_match.group(1).strip() if name_match else "Marcus Vance"
                tool_calls = [{
                    "id": "call_prof_1",
                    "type": "function",
                    "function": {
                        "name": "get_employee_profile",
                        "arguments": json.dumps({"name": target_name})
                    }
                }]
                reply = f"Retrieving verified employee profile records for {target_name}."

            # 3. HR Policies & Guidelines (e.g., "What is our overtime policy?", "remote work guidelines")
            elif any(w in content for w in ["policy", "handbook", "guideline", "guidelines", "rule", "procedure"]):
                tool_calls = [{
                    "id": "call_policy_1",
                    "type": "function",
                    "function": {
                        "name": "search_attendance_policy",
                        "arguments": json.dumps({"query": content})
                    }
                }]
                reply = "Searching official workforce policy documentation."

            # 3. Compound: Both repeated lateness and excessive overtime
            elif ("both" in content and ("late" in content or "tardiness" in content) and "overtime" in content) or \
                 ("repeated" in content and "overtime" in content):
                tool_calls = [{
                    "id": "call_corr_1",
                    "type": "function",
                    "function": {
                        "name": "get_workforce_correlations",
                        "arguments": json.dumps({"period": "this_month", "min_late_count": 3, "min_overtime_hours": 5.0})
                    }
                }]
                reply = "Analyzing compound workforce patterns for employees with both repeated lateness and high overtime."

            # 4. Absenteeism: "Who is absent today?" / "Compare absenteeism"
            elif "absent" in content or "absenteeism" in content:
                if "compare" in content or "department" in content or "highest" in content:
                    tool_calls = [{
                        "id": "call_dept_abs_1",
                        "type": "function",
                        "function": {
                            "name": "get_department_analytics",
                            "arguments": json.dumps({"period": "this_month"})
                        }
                    }]
                    reply = "Comparing department-level absenteeism and attendance rates."
                else:
                    tool_calls = [{
                        "id": "call_abs_1",
                        "type": "function",
                        "function": {
                            "name": "get_absenteeism",
                            "arguments": json.dumps({"period": "today"})
                        }
                    }]
                    reply = "Checking today's workforce absenteeism roster."

            # 5. Late arrivals with numerical conditions: "more than five times", "at least 3"
            elif "late" in content or "tardy" in content:
                min_count = None
                if "more than five" in content or "more than 5" in content or "> 5" in content:
                    min_count = 6
                elif "at least 5" in content or "5 or more" in content or ">= 5" in content:
                    min_count = 5
                elif "more than 3" in content or "more than three" in content:
                    min_count = 4
                elif "at least 3" in content:
                    min_count = 3

                period = "this_month" if "this month" in content or "month" in content else ("today" if "today" in content else "last_7_days")

                tool_calls = [{
                    "id": "call_late_1",
                    "type": "function",
                    "function": {
                        "name": "get_late_arrivals",
                        "arguments": json.dumps({
                            "period": period,
                            "min_late_count": min_count,
                            "group_by_employee": True if min_count or "employees" in content else False,
                            "limit": 15
                        })
                    }
                }]
                reply = f"Querying verified attendance records for late arrivals in {period}."

            # 6. Overtime
            elif "overtime" in content or "ot" in content:
                period = "last_month" if "last month" in content or "previous month" in content else "this_month"
                dept = "Engineering" if "engineering" in content else None
                tool_calls = [{
                    "id": "call_ot_1",
                    "type": "function",
                    "function": {
                        "name": "get_employee_overtime",
                        "arguments": json.dumps({"period": period, "department": dept, "limit": 10})
                    }
                }]
                reply = f"Calculating overtime records for {period}."

            # 7. Personal attendance
            elif "my attendance" in content or "my hours" in content or "my overtime" in content or "my record" in content:
                tool_calls = [{
                    "id": "call_my_att_1",
                    "type": "function",
                    "function": {
                        "name": "get_my_attendance",
                        "arguments": json.dumps({"period": "this_month"})
                    }
                }]
                reply = "Retrieving your personal verified attendance history."

            # 8. Anomalies
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

            # 10. Department overview
            elif "department" in content or "headcount" in content or "attendance rate" in content:
                tool_calls = [{
                    "id": "call_dept_1",
                    "type": "function",
                    "function": {
                        "name": "get_department_analytics",
                        "arguments": json.dumps({"period": "this_month"})
                    }
                }]
                reply = "Analyzing department metrics and attendance rates."

            else:
                reply = (
                    "### Welcome to AttendAI Workforce Intelligence\n\n"
                    "I am connected to authorized PostgreSQL workforce records and policy documents. You can ask:\n\n"
                    "- *\"Which employees arrived late more than five times this month?\"*\n"
                    "- *\"Who is absent today?\"*\n"
                    "- *\"Who worked the most overtime this month?\"*\n"
                    "- *\"Which department has the highest absenteeism?\"*\n"
                    "- *\"Find employees with both repeated lateness and excessive overtime.\"*\n"
                    "- *\"What is our remote work attendance policy?\"*"
                )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "content": reply,
            "tool_calls": tool_calls,
            "provider": "mock",
            "model": self.model,
            "latency_ms": round(max(5.0, latency_ms), 2),
            "tokens_used": len(reply.split()) * 2
        }
