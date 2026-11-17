from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from app.models.models import User, Employee, Department
from app.core.exceptions import ForbiddenException, ValidationException

# 1. Report Type Registry by Role
ADMIN_REPORT_TYPES = [
    {"id": "workforce_complete", "name": "Complete Organization Report", "category": "Workforce", "desc": "Comprehensive overview of workforce, active headcounts, designations and status."},
    {"id": "department_report", "name": "Department Report", "category": "Departmental", "desc": "Attendance and headcount breakdown for specific departments."},
    {"id": "employee_individual", "name": "Individual Employee Report", "category": "Workforce", "desc": "In-depth attendance, punctuality and profile history for a single chosen employee."},
    {"id": "employee_multiple", "name": "Multiple Employee Report", "category": "Workforce", "desc": "Combined metrics and profiles for selected employees."},
    {"id": "attendance_org", "name": "Attendance Report", "category": "Attendance", "desc": "Organization-wide attendance logs across all departments and shifts."},
    {"id": "overtime_report", "name": "Overtime Report", "category": "Time & Hours", "desc": "Work performed beyond scheduled shifts, total overtime hours and cost factor."},
    {"id": "leave_report", "name": "Leave Report", "category": "Leave & Absence", "desc": "Leave applications, balances, approved time-off and approval history."},
    {"id": "shift_report", "name": "Shift Report", "category": "Scheduling", "desc": "Shift assignments, schedules, operating windows and coverage."},
    {"id": "anomaly_report", "name": "Anomaly Report", "category": "Compliance", "desc": "Flagged attendance anomalies, missing punches, and audit reviews."},
    {"id": "workforce_analytics", "name": "Workforce Analytics Report", "category": "Analytics", "desc": "Macro attendance trends, absenteeism rates and punctuality metrics."}
]

HR_REPORT_TYPES = [
    {"id": "department_report", "name": "Authorized Department Report", "category": "Departmental", "desc": "Attendance and workforce metrics for your assigned department."},
    {"id": "employee_individual", "name": "Individual Employee Report", "category": "Workforce", "desc": "Detailed attendance and time tracking for an authorized employee."},
    {"id": "employee_multiple", "name": "Multiple Employee Report", "category": "Workforce", "desc": "Report covering multiple authorized employees in your scope."},
    {"id": "attendance_org", "name": "Attendance Report", "category": "Attendance", "desc": "Authorized workforce attendance logs within your departmental scope."},
    {"id": "overtime_report", "name": "Overtime Report", "category": "Time & Hours", "desc": "Overtime hours tracked for employees in your authorized scope."},
    {"id": "leave_report", "name": "Leave Report", "category": "Leave & Absence", "desc": "Leave records and pending requests in your authorized scope."},
    {"id": "shift_report", "name": "Shift Report", "category": "Scheduling", "desc": "Shift assignments for authorized employees."},
    {"id": "anomaly_report", "name": "Anomaly Report", "category": "Compliance", "desc": "Attendance discrepancies and flagged records in your scope."}
]

EMPLOYEE_REPORT_TYPES = [
    {"id": "my_attendance_monthly", "name": "My Monthly Attendance", "category": "Personal", "desc": "Your complete daily attendance record for the current month."},
    {"id": "my_attendance_history", "name": "My Attendance History", "category": "Personal", "desc": "Full chronological punch log with clock-in and clock-out timestamps."},
    {"id": "my_overtime", "name": "My Overtime Report", "category": "Personal", "desc": "Personal overtime hours logged beyond your scheduled shifts."},
    {"id": "my_working_hours", "name": "My Working Hours", "category": "Personal", "desc": "Detailed record of your daily worked hours vs required shift hours."},
    {"id": "my_leave_history", "name": "My Leave History", "category": "Personal", "desc": "Your submitted leave requests, approval statuses and dates."},
    {"id": "my_leave_balance", "name": "My Leave Balance", "category": "Personal", "desc": "Overview of your annual paid time off quota, days taken, and remaining balance."},
    {"id": "my_shifts", "name": "My Shift History", "category": "Personal", "desc": "Your current and past shift assignments and scheduled operating hours."}
]

# 2. Columns Registry
COLUMNS_REGISTRY = {
    "attendance": [
        {"id": "date", "label": "Date", "is_default": True},
        {"id": "employee_code", "label": "Employee Code", "is_default": True},
        {"id": "employee_name", "label": "Employee Name", "is_default": True},
        {"id": "department", "label": "Department", "is_default": True},
        {"id": "shift_name", "label": "Assigned Shift", "is_default": True},
        {"id": "scheduled_start", "label": "Scheduled Start", "is_default": False},
        {"id": "scheduled_end", "label": "Scheduled End", "is_default": False},
        {"id": "clock_in", "label": "Actual Clock In", "is_default": True},
        {"id": "clock_out", "label": "Actual Clock Out", "is_default": True},
        {"id": "break_duration", "label": "Break Duration (min)", "is_default": False},
        {"id": "worked_hours", "label": "Total Working Hours", "is_default": True},
        {"id": "late_minutes", "label": "Late Minutes", "is_default": True},
        {"id": "overtime_hours", "label": "Overtime Hours", "is_default": True},
        {"id": "status", "label": "Attendance Status", "is_default": True},
    ],
    "personal_attendance": [
        {"id": "date", "label": "Date", "is_default": True},
        {"id": "shift_name", "label": "Assigned Shift", "is_default": True},
        {"id": "scheduled_start", "label": "Scheduled Start", "is_default": False},
        {"id": "scheduled_end", "label": "Scheduled End", "is_default": False},
        {"id": "clock_in", "label": "Actual Clock In", "is_default": True},
        {"id": "clock_out", "label": "Actual Clock Out", "is_default": True},
        {"id": "break_duration", "label": "Break Duration (min)", "is_default": True},
        {"id": "worked_hours", "label": "Total Working Hours", "is_default": True},
        {"id": "late_minutes", "label": "Late Minutes", "is_default": True},
        {"id": "overtime_hours", "label": "Overtime Hours", "is_default": True},
        {"id": "status", "label": "Attendance Status", "is_default": True},
    ],
    "employee": [
        {"id": "employee_code", "label": "Employee Code", "is_default": True},
        {"id": "employee_name", "label": "Full Name", "is_default": True},
        {"id": "email", "label": "Email Address", "is_default": True},
        {"id": "department", "label": "Department", "is_default": True},
        {"id": "designation", "label": "Designation", "is_default": True},
        {"id": "phone", "label": "Phone", "is_default": False},
        {"id": "date_of_joining", "label": "Joining Date", "is_default": True},
        {"id": "current_shift", "label": "Current Shift", "is_default": True},
        {"id": "is_active", "label": "Employment Status", "is_default": True},
    ],
    "overtime": [
        {"id": "date", "label": "Date", "is_default": True},
        {"id": "employee_code", "label": "Employee Code", "is_default": True},
        {"id": "employee_name", "label": "Employee Name", "is_default": True},
        {"id": "department", "label": "Department", "is_default": True},
        {"id": "regular_hours", "label": "Regular Hours", "is_default": True},
        {"id": "overtime_hours", "label": "Overtime Hours", "is_default": True},
        {"id": "total_hours", "label": "Total Hours", "is_default": True},
        {"id": "status", "label": "Status", "is_default": False},
    ],
    "leave": [
        {"id": "employee_code", "label": "Employee Code", "is_default": True},
        {"id": "employee_name", "label": "Employee Name", "is_default": True},
        {"id": "department", "label": "Department", "is_default": True},
        {"id": "leave_type", "label": "Leave Type", "is_default": True},
        {"id": "start_date", "label": "Start Date", "is_default": True},
        {"id": "end_date", "label": "End Date", "is_default": True},
        {"id": "days_count", "label": "Number of Days", "is_default": True},
        {"id": "reason", "label": "Reason", "is_default": False},
        {"id": "status", "label": "Approval Status", "is_default": True},
        {"id": "created_at", "label": "Application Date", "is_default": True},
    ],
    "shift": [
        {"id": "employee_code", "label": "Employee Code", "is_default": True},
        {"id": "employee_name", "label": "Employee Name", "is_default": True},
        {"id": "department", "label": "Department", "is_default": True},
        {"id": "shift_name", "label": "Shift Name", "is_default": True},
        {"id": "shift_code", "label": "Shift Code", "is_default": True},
        {"id": "scheduled_start", "label": "Scheduled Start", "is_default": True},
        {"id": "scheduled_end", "label": "Scheduled End", "is_default": True},
        {"id": "required_hours", "label": "Required Hours", "is_default": True},
        {"id": "effective_from", "label": "Effective From", "is_default": True},
    ],
    "anomaly": [
        {"id": "date", "label": "Date", "is_default": True},
        {"id": "employee_code", "label": "Employee Code", "is_default": True},
        {"id": "employee_name", "label": "Employee Name", "is_default": True},
        {"id": "department", "label": "Department", "is_default": True},
        {"id": "anomaly_type", "label": "Anomaly Type", "is_default": True},
        {"id": "severity", "label": "Severity", "is_default": True},
        {"id": "explanation", "label": "Explanation", "is_default": True},
        {"id": "is_resolved", "label": "Resolution Status", "is_default": True},
    ]
}

def get_report_types_for_user(user: User) -> List[Dict[str, Any]]:
    if user.role == "admin":
        return ADMIN_REPORT_TYPES
    elif user.role == "hr_manager":
        return HR_REPORT_TYPES
    elif user.role == "employee":
        return EMPLOYEE_REPORT_TYPES
    return []

def get_columns_for_report_type(report_type: str, user_role: str) -> List[Dict[str, Any]]:
    if user_role == "employee":
        if "leave" in report_type:
            cols = [c for c in COLUMNS_REGISTRY["leave"] if c["id"] not in ["employee_code", "employee_name", "department"]]
            return cols
        elif "shift" in report_type:
            cols = [c for c in COLUMNS_REGISTRY["shift"] if c["id"] not in ["employee_code", "employee_name", "department"]]
            return cols
        else:
            return COLUMNS_REGISTRY["personal_attendance"]

    if report_type in ["employee_directory", "workforce_complete"]:
        return COLUMNS_REGISTRY["employee"]
    elif report_type == "overtime_report":
        return COLUMNS_REGISTRY["overtime"]
    elif report_type == "leave_report":
        return COLUMNS_REGISTRY["leave"]
    elif report_type == "shift_report":
        return COLUMNS_REGISTRY["shift"]
    elif report_type == "anomaly_report":
        return COLUMNS_REGISTRY["anomaly"]
    else:
        return COLUMNS_REGISTRY["attendance"]

def resolve_date_range(preset: Optional[str], start_date: Optional[date], end_date: Optional[date]) -> Tuple[date, date]:
    today = date.today()
    if preset == "today":
        return today, today
    elif preset == "yesterday":
        y = today - timedelta(days=1)
        return y, y
    elif preset == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, today
    elif preset == "last_week":
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return start, end
    elif preset == "this_month":
        start = date(today.year, today.month, 1)
        return start, today
    elif preset == "last_month":
        first_this_month = date(today.year, today.month, 1)
        end = first_this_month - timedelta(days=1)
        start = date(end.year, end.month, 1)
        return start, end
    elif preset == "last_7_days":
        return today - timedelta(days=6), today
    elif preset == "last_30_days":
        return today - timedelta(days=29), today
    elif preset == "last_90_days":
        return today - timedelta(days=89), today
    elif preset == "this_quarter":
        quarter_month = ((today.month - 1) // 3) * 3 + 1
        return date(today.year, quarter_month, 1), today
    elif preset == "this_year":
        return date(today.year, 1, 1), today
    elif start_date and end_date:
        if start_date > end_date:
            raise ValidationException("Start date cannot be after end date.")
        return start_date, end_date
    return date(today.year, today.month, 1), today
