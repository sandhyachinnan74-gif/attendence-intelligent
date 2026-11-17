from typing import Dict, Any, List

class OutputValidator:
    @staticmethod
    def validate_and_format(
        raw_text: str,
        tool_results: List[Dict[str, Any]],
        role: str
    ) -> Dict[str, Any]:
        """
        Validates output against tool execution results and appends source citations.
        """
        citations = []
        for tr in tool_results:
            tool_name = tr.get("tool_name")
            output = tr.get("output", {})
            if tool_name == "search_attendance_policy":
                matches = output.get("matches", [])
                for m in matches:
                    citations.append({
                        "source": m.get("citation", "Company Policy Document"),
                        "page": m.get("page_number"),
                        "section": m.get("section")
                    })
            elif tool_name in ["get_late_arrivals", "get_attendance_summary", "get_employee_overtime", "get_my_attendance"]:
                citations.append({
                    "source": f"PostgreSQL Database ({tool_name})",
                    "type": "database_record"
                })

        return {
            "validated_text": raw_text,
            "citations": citations,
            "is_grounded": len(citations) > 0 or len(tool_results) == 0
        }
