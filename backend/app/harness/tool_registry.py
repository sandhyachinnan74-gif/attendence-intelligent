import json
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from app.models.models import (
    AttendanceRecord, Employee, Department, Shift, AttendanceAnomaly, Policy, PolicyChunk
)
from app.services.policy_service import PolicyService

# Tool schema definitions for OpenAI/NIM/Groq function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_my_attendance",
            "description": "Get current user's personal attendance history and working hours.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of past days to retrieve (default 14)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance_summary",
            "description": "Get organization or department aggregated attendance summary for a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Target date in YYYY-MM-DD format (defaults to today)"},
                    "department_id": {"type": "string", "description": "Optional department filter"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_late_arrivals",
            "description": "List employees who arrived late past the shift grace period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Days to look back (default 7)"},
                    "limit": {"type": "integer", "description": "Maximum records to return (default 15)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_overtime",
            "description": "List employees with overtime hours in the specified window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Past days window (default 30)"},
                    "limit": {"type": "integer", "description": "Max results (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_department_analytics",
            "description": "Compare attendance rates, absenteeism and headcounts across departments.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_attendance_policy",
            "description": "Search official HR attendance, overtime, leave and company policies for relevant sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keywords or question regarding HR policy"},
                    "limit": {"type": "integer", "description": "Max chunks (default 4)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_anomaly_reports",
            "description": "List attendance anomalies flagged by rule-based or Isolation Forest algorithms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "status": {"type": "string", "enum": ["pending", "investigating", "resolved", "dismissed"]},
                    "limit": {"type": "integer", "description": "Max records (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_profile",
            "description": "Retrieve profile information for an employee by code or email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_code": {"type": "string", "description": "Employee Code (e.g. EMP001)"},
                    "email": {"type": "string", "description": "Employee Email address"}
                }
            }
        }
    }
]

class ToolRegistry:
    @staticmethod
    async def execute_tool(
        name: str,
        arguments: Dict[str, Any],
        db: AsyncSession,
        user: Any,
        employee: Optional[Employee] = None
    ) -> Dict[str, Any]:
        """
        Executes approved tool with verified permissions and scope.
        """
        org_id = user.organization_id

        if name == "get_my_attendance":
            if not employee:
                return {"error": "No employee profile linked to current user account."}
            days = arguments.get("days", 14)
            start_date = date.today() - timedelta(days=days)
            stmt = select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.employee_id == employee.id,
                    AttendanceRecord.date >= start_date
                )
            ).order_by(AttendanceRecord.date.desc())
            records = (await db.execute(stmt)).scalars().all()
            return {
                "employee": f"{employee.first_name} {employee.last_name}",
                "records_count": len(records),
                "attendance": [
                    {
                        "date": str(r.date),
                        "clock_in": r.clock_in.strftime("%H:%M") if r.clock_in else None,
                        "clock_out": r.clock_out.strftime("%H:%M") if r.clock_out else None,
                        "worked_hours": round(r.worked_minutes / 60.0, 2),
                        "status": r.status,
                        "late_minutes": r.late_minutes
                    }
                    for r in records
                ]
            }

        elif name == "get_attendance_summary":
            # Scoped check: Employee can't view org-wide summary
            if user.role == "employee":
                return {"error": "Employees are not authorized to view organization-wide attendance."}

            target_date_str = arguments.get("date")
            target_date = date.fromisoformat(target_date_str) if target_date_str else date.today()
            dept_id = arguments.get("department_id")

            query = select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.organization_id == org_id,
                    AttendanceRecord.date == target_date
                )
            )
            records = (await db.execute(query)).scalars().all()
            present = sum(1 for r in records if r.status in ["present", "late", "half_day"])
            late = sum(1 for r in records if r.late_minutes > 0 or r.status == "late")
            return {
                "date": str(target_date),
                "total_records": len(records),
                "present": present,
                "late": late,
                "overtime_hours": round(sum(r.overtime_minutes for r in records) / 60.0, 2)
            }

        elif name == "get_late_arrivals":
            if user.role == "employee":
                return {"error": "Unauthorized to view other employees' late arrivals."}
            days = arguments.get("days", 7)
            limit = arguments.get("limit", 15)
            start_date = date.today() - timedelta(days=days)

            stmt = (
                select(AttendanceRecord, Employee, Department)
                .join(Employee, Employee.id == AttendanceRecord.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == org_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.late_minutes > 0
                    )
                )
                .order_by(AttendanceRecord.date.desc(), AttendanceRecord.late_minutes.desc())
                .limit(limit)
            )
            res = (await db.execute(stmt)).all()
            return {
                "window_days": days,
                "count": len(res),
                "late_arrivals": [
                    {
                        "date": str(r.date),
                        "employee": f"{emp.first_name} {emp.last_name}",
                        "employee_code": emp.employee_code,
                        "department": dept.name if dept else "General",
                        "late_minutes": r.late_minutes,
                        "clock_in": r.clock_in.strftime("%H:%M") if r.clock_in else None
                    }
                    for r, emp, dept in res
                ]
            }

        elif name == "get_employee_overtime":
            if user.role == "employee":
                return {"error": "Unauthorized to view workforce overtime reports."}
            days = arguments.get("days", 30)
            limit = arguments.get("limit", 10)
            start_date = date.today() - timedelta(days=days)

            stmt = (
                select(
                    Employee.id,
                    Employee.first_name,
                    Employee.last_name,
                    Employee.employee_code,
                    func.sum(AttendanceRecord.overtime_minutes).label("total_ot")
                )
                .join(AttendanceRecord, AttendanceRecord.employee_id == Employee.id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == org_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.overtime_minutes > 0
                    )
                )
                .group_by(Employee.id, Employee.first_name, Employee.last_name, Employee.employee_code)
                .order_by(desc("total_ot"))
                .limit(limit)
            )
            res = (await db.execute(stmt)).all()
            return {
                "period_days": days,
                "top_overtime_employees": [
                    {
                        "employee": f"{first} {last}",
                        "employee_code": code,
                        "overtime_hours": round((ot or 0) / 60.0, 1)
                    }
                    for emp_id, first, last, code, ot in res
                ]
            }

        elif name == "get_department_analytics":
            if user.role == "employee":
                return {"error": "Unauthorized to view department-level metrics."}
            depts = (await db.execute(select(Department).where(Department.organization_id == org_id))).scalars().all()
            today = date.today()
            analytics = []
            for d in depts:
                emps = (await db.execute(select(Employee).where(Employee.department_id == d.id))).scalars().all()
                total = len(emps)
                emp_ids = [e.id for e in emps]
                present = 0
                if emp_ids:
                    recs = (await db.execute(
                        select(AttendanceRecord).where(
                            and_(
                                AttendanceRecord.date == today,
                                AttendanceRecord.employee_id.in_(emp_ids)
                            )
                        )
                    )).scalars().all()
                    present = sum(1 for r in recs if r.status in ["present", "late", "half_day"])
                analytics.append({
                    "department": d.name,
                    "code": d.code,
                    "total_employees": total,
                    "present_today": present,
                    "rate": round((present / total * 100), 1) if total > 0 else 0.0
                })
            return {"departments": analytics}

        elif name == "search_attendance_policy":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 4)
            matches = await PolicyService.search_policies(db, org_id, query, limit=limit)
            return {
                "query": query,
                "matches": matches
            }

        elif name == "get_anomaly_reports":
            if user.role == "employee":
                return {"error": "Unauthorized to access anomaly investigation records."}
            stmt = select(AttendanceAnomaly, Employee).join(Employee, Employee.id == AttendanceAnomaly.employee_id).where(
                AttendanceAnomaly.organization_id == org_id
            )
            if arguments.get("status"):
                stmt = stmt.where(AttendanceAnomaly.status == arguments["status"])
            if arguments.get("severity"):
                stmt = stmt.where(AttendanceAnomaly.severity == arguments["severity"])
            limit = arguments.get("limit", 10)
            stmt = stmt.order_by(desc(AttendanceAnomaly.created_at)).limit(limit)
            res = (await db.execute(stmt)).all()
            return {
                "anomalies": [
                    {
                        "id": anom.id,
                        "employee": f"{emp.first_name} {emp.last_name}",
                        "date": str(anom.date),
                        "type": anom.anomaly_type,
                        "severity": anom.severity,
                        "method": anom.detection_method,
                        "score": anom.score,
                        "explanation": anom.explanation,
                        "status": anom.status
                    }
                    for anom, emp in res
                ]
            }

        elif name == "get_employee_profile":
            code = arguments.get("employee_code")
            email = arguments.get("email")
            stmt = select(Employee, Department).outerjoin(Department, Department.id == Employee.department_id).where(
                Employee.organization_id == org_id
            )
            if code:
                stmt = stmt.where(Employee.employee_code == code)
            elif email:
                stmt = stmt.where(Employee.email == email)
            else:
                return {"error": "Please provide either employee_code or email."}

            res = (await db.execute(stmt)).first()
            if not res:
                return {"error": "Employee not found."}
            emp, dept = res
            return {
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}",
                "email": emp.email,
                "department": dept.name if dept else "General",
                "designation": emp.designation,
                "date_of_joining": str(emp.date_of_joining),
                "is_active": emp.is_active
            }

        else:
            return {"error": f"Unknown tool: {name}"}
