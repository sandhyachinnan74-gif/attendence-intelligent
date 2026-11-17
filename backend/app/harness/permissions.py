from typing import Dict, Any, Optional

ALLOWED_TOOLS_BY_ROLE = {
    "admin": {
        "get_my_attendance",
        "get_attendance_summary",
        "get_late_arrivals",
        "get_employee_overtime",
        "get_department_analytics",
        "search_attendance_policy",
        "get_anomaly_reports",
        "get_employee_profile",
    },
    "hr_manager": {
        "get_my_attendance",
        "get_attendance_summary",
        "get_late_arrivals",
        "get_employee_overtime",
        "get_department_analytics",
        "search_attendance_policy",
        "get_anomaly_reports",
        "get_employee_profile",
    },
    "employee": {
        "get_my_attendance",
        "search_attendance_policy",
    }
}

class HarnessPermissions:
    @staticmethod
    def is_tool_allowed(role: str, tool_name: str) -> bool:
        allowed = ALLOWED_TOOLS_BY_ROLE.get(role, set())
        return tool_name in allowed

    @staticmethod
    def filter_tools_for_user(role: str, tools: list) -> list:
        allowed = ALLOWED_TOOLS_BY_ROLE.get(role, set())
        return [t for t in tools if t["function"]["name"] in allowed]
