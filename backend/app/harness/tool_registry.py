import json
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_, case
from app.models.models import (
    AttendanceRecord, Employee, Department, Shift, AttendanceAnomaly, Policy, PolicyChunk
)
from app.services.policy_service import PolicyService
from app.harness.date_resolver import DateRangeResolver

# Comprehensive Tool schema definitions for OpenAI/NIM/Groq function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_my_attendance",
            "description": "Get current authenticated user's personal attendance history, hours worked, late days, and punctuality stats.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "this_week", "last_week", "this_month", "last_month", "last_30_days"],
                        "description": "Standardized time window (default 'this_month')"
                    },
                    "days": {"type": "integer", "description": "Optional explicit number of past days to retrieve"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_attendance_summary",
            "description": "Get organization or department aggregated attendance metrics (headcount, present, absent, late, overtime) for a specific date or window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "yesterday", "this_week", "this_month"],
                        "description": "Target period (defaults to today)"
                    },
                    "date": {"type": "string", "description": "Target date in YYYY-MM-DD format (defaults to today)"},
                    "department": {"type": "string", "description": "Optional department name or code to filter summary"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_late_arrivals",
            "description": "Retrieve employees with late arrival records past shift grace periods. Supports grouping by employee to identify frequent offenders, filtering by department, numerical threshold (e.g. more than 5 times), and flexible date ranges.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "yesterday", "this_week", "last_week", "this_month", "last_month", "last_30_days", "last_7_days"],
                        "description": "Time window to search (e.g. 'this_month', 'today', 'last_week')"
                    },
                    "days": {"type": "integer", "description": "Days to look back (default 30 if period not specified)"},
                    "department": {"type": "string", "description": "Department name or code to filter (e.g. 'Customer Success', 'Engineering')"},
                    "min_late_count": {
                        "type": "integer",
                        "description": "Filter for employees arriving late at least or more than this number of times in the period (e.g. 5 or 6)"
                    },
                    "group_by_employee": {
                        "type": "boolean",
                        "description": "If true, aggregate frequency per employee to find repeat late arrivals"
                    },
                    "limit": {"type": "integer", "description": "Maximum records or employees to return (default 20)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_overtime",
            "description": "List employees with logged overtime hours beyond scheduled shift durations, ranked by total overtime. Supports department filtering and time periods.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["this_week", "last_week", "this_month", "last_month", "last_30_days"],
                        "description": "Period to analyze (default 'this_month')"
                    },
                    "department": {"type": "string", "description": "Department name or code filter (e.g. 'Engineering', 'Operations')"},
                    "min_overtime_hours": {"type": "number", "description": "Minimum overtime hours threshold"},
                    "limit": {"type": "integer", "description": "Max results to return (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_absenteeism",
            "description": "List absent employees across the organization or for a specific department for today, yesterday, or a given period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "yesterday", "this_week", "this_month"],
                        "description": "Target period (default 'today')"
                    },
                    "department": {"type": "string", "description": "Optional department filter"},
                    "limit": {"type": "integer", "description": "Maximum records to return (default 25)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_department_analytics",
            "description": "Compare attendance rates, absenteeism percentages, overtime hours, headcount, and anomaly counts across departments to identify which department requires management or HR attention.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "this_week", "this_month", "last_30_days"],
                        "description": "Analysis window (default 'this_month')"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_workforce_correlations",
            "description": "Identify employees exhibiting compound attendance patterns: both repeated lateness AND excessive overtime hours simultaneously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["this_month", "last_month", "last_30_days"],
                        "description": "Period to evaluate (default 'this_month')"
                    },
                    "min_late_count": {"type": "integer", "description": "Minimum late arrivals threshold (default 3)"},
                    "min_overtime_hours": {"type": "number", "description": "Minimum overtime hours threshold (default 5.0)"},
                    "department": {"type": "string", "description": "Optional department filter"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_attendance_policy",
            "description": "Search official company HR policies (attendance guidelines, remote work, core hours, overtime rules, leave types, grace periods) and return verifiable citations with page numbers and sections.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keywords or question regarding HR policy"},
                    "limit": {"type": "integer", "description": "Max matching policy chunks (default 4)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_anomaly_reports",
            "description": "List attendance anomalies flagged by deterministic rules or the Isolation Forest machine learning engine with confidence scores and explanations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "status": {"type": "string", "enum": ["pending", "investigating", "resolved", "dismissed"]},
                    "limit": {"type": "integer", "description": "Max records to return (default 10)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_profile",
            "description": "Retrieve comprehensive employee profile (name, code, email, department, designation, joining date, status) by employee code, email, or partial name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Employee first or last name (or partial match)"},
                    "employee_code": {"type": "string", "description": "Employee Code (e.g. EMP001)"},
                    "email": {"type": "string", "description": "Employee email address"}
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
        Executes approved tool with verified permissions, organization isolation, and scope.
        """
        org_id = user.organization_id

        # -------------------------------------------------------------
        # Tool: get_my_attendance
        # -------------------------------------------------------------
        if name == "get_my_attendance":
            if not employee:
                return {"error": "No employee profile linked to current user account."}
            
            period = arguments.get("period")
            days = arguments.get("days")
            start_date, end_date, period_label = DateRangeResolver.resolve_period(
                period=period, days=days or 30
            )

            stmt = select(AttendanceRecord).where(
                and_(
                    AttendanceRecord.employee_id == employee.id,
                    AttendanceRecord.date >= start_date,
                    AttendanceRecord.date <= end_date
                )
            ).order_by(AttendanceRecord.date.desc())
            records = (await db.execute(stmt)).scalars().all()

            total_days = len(records)
            present_days = sum(1 for r in records if r.status in ["present", "half_day", "late"])
            late_days = sum(1 for r in records if r.late_minutes > 0 or r.status == "late")
            total_worked_hours = round(sum(r.worked_minutes for r in records) / 60.0, 1)
            total_ot_hours = round(sum(r.overtime_minutes for r in records) / 60.0, 1)
            punctuality_rate = round(((present_days - late_days) / present_days * 100), 1) if present_days > 0 else 100.0

            return {
                "period": period_label,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "employee": f"{employee.first_name} {employee.last_name}",
                "employee_code": employee.employee_code,
                "summary": {
                    "total_logged_days": total_days,
                    "present_days": present_days,
                    "late_days": late_days,
                    "total_worked_hours": total_worked_hours,
                    "overtime_hours": total_ot_hours,
                    "punctuality_rate": punctuality_rate
                },
                "recent_records": [
                    {
                        "date": str(r.date),
                        "status": r.status,
                        "clock_in": r.clock_in.strftime("%H:%M") if r.clock_in else None,
                        "clock_out": r.clock_out.strftime("%H:%M") if r.clock_out else None,
                        "worked_hours": round(r.worked_minutes / 60.0, 1),
                        "late_minutes": r.late_minutes,
                        "overtime_hours": round(r.overtime_minutes / 60.0, 1)
                    }
                    for r in records[:10]
                ]
            }

        # -------------------------------------------------------------
        # Tool: get_attendance_summary
        # -------------------------------------------------------------
        elif name == "get_attendance_summary":
            if user.role == "employee":
                return {"error": "Employees are not authorized to view organization-wide attendance."}

            period = arguments.get("period", "today")
            target_date_str = arguments.get("date")
            dept_filter = arguments.get("department")

            if target_date_str:
                start_date, end_date, period_label = DateRangeResolver.resolve_period(start_date_str=target_date_str)
            else:
                start_date, end_date, period_label = DateRangeResolver.resolve_period(period=period)

            # Build query
            query = (
                select(AttendanceRecord, Employee, Department)
                .join(Employee, Employee.id == AttendanceRecord.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == org_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date
                    )
                )
            )

            if dept_filter:
                query = query.where(
                    or_(
                        Department.name.ilike(f"%{dept_filter}%"),
                        Department.code.ilike(f"%{dept_filter}%")
                    )
                )

            res = (await db.execute(query)).all()
            total_records = len(res)
            present = sum(1 for r, emp, dept in res if r.status in ["present", "late", "half_day"])
            absent = sum(1 for r, emp, dept in res if r.status == "absent")
            late = sum(1 for r, emp, dept in res if r.late_minutes > 0 or r.status == "late")
            total_ot = round(sum(r.overtime_minutes for r, emp, dept in res) / 60.0, 1)

            # Total headcount in org or dept
            headcount_stmt = select(func.count(Employee.id)).where(
                and_(Employee.organization_id == org_id, Employee.is_active == True)
            )
            if dept_filter:
                headcount_stmt = headcount_stmt.join(Department, Department.id == Employee.department_id).where(
                    or_(
                        Department.name.ilike(f"%{dept_filter}%"),
                        Department.code.ilike(f"%{dept_filter}%")
                    )
                )
            headcount = (await db.execute(headcount_stmt)).scalar() or 0
            attendance_rate = round((present / headcount * 100), 1) if headcount > 0 else 0.0

            return {
                "period": period_label,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "department_filter": dept_filter or "All Departments",
                "headcount": headcount,
                "present_count": present,
                "absent_count": absent,
                "late_count": late,
                "overtime_hours": total_ot,
                "attendance_rate": attendance_rate
            }

        # -------------------------------------------------------------
        # Tool: get_late_arrivals
        # -------------------------------------------------------------
        elif name == "get_late_arrivals":
            if user.role == "employee":
                return {"error": "Unauthorized to view other employees' late arrivals."}

            period = arguments.get("period")
            days = arguments.get("days")
            dept_filter = arguments.get("department")
            min_late_count = arguments.get("min_late_count")
            group_by_emp = arguments.get("group_by_employee") or (min_late_count is not None)
            limit = arguments.get("limit", 20)

            start_date, end_date, period_label = DateRangeResolver.resolve_period(
                period=period, days=days or (7 if not period else None)
            )

            stmt = (
                select(AttendanceRecord, Employee, Department)
                .join(Employee, Employee.id == AttendanceRecord.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == org_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date,
                        AttendanceRecord.late_minutes > 0
                    )
                )
            )

            if dept_filter:
                stmt = stmt.where(
                    or_(
                        Department.name.ilike(f"%{dept_filter}%"),
                        Department.code.ilike(f"%{dept_filter}%")
                    )
                )

            res = (await db.execute(stmt)).all()

            if group_by_emp:
                # Aggregate per employee
                emp_map = {}
                for r, emp, dept in res:
                    key = emp.id
                    if key not in emp_map:
                        emp_map[key] = {
                            "employee": f"{emp.first_name} {emp.last_name}",
                            "employee_code": emp.employee_code,
                            "department": dept.name if dept else "General",
                            "late_count": 0,
                            "total_late_minutes": 0,
                            "dates": []
                        }
                    emp_map[key]["late_count"] += 1
                    emp_map[key]["total_late_minutes"] += r.late_minutes
                    emp_map[key]["dates"].append(str(r.date))

                # Apply min_late_count filter
                aggregated = list(emp_map.values())
                if min_late_count is not None:
                    aggregated = [e for e in aggregated if e["late_count"] >= min_late_count]

                # Sort by late_count desc
                aggregated.sort(key=lambda x: (x["late_count"], x["total_late_minutes"]), reverse=True)

                return {
                    "period": period_label,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "department_filter": dept_filter or "All Departments",
                    "threshold_applied": f">= {min_late_count} times" if min_late_count else None,
                    "total_qualifying_employees": len(aggregated),
                    "employees": aggregated[:limit]
                }
            else:
                records = [
                    {
                        "date": str(r.date),
                        "employee": f"{emp.first_name} {emp.last_name}",
                        "employee_code": emp.employee_code,
                        "department": dept.name if dept else "General",
                        "late_minutes": r.late_minutes,
                        "clock_in": r.clock_in.strftime("%H:%M") if r.clock_in else None
                    }
                    for r, emp, dept in res[:limit]
                ]
                return {
                    "period": period_label,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "department_filter": dept_filter or "All Departments",
                    "total_late_records": len(res),
                    "records": records
                }

        # -------------------------------------------------------------
        # Tool: get_employee_overtime
        # -------------------------------------------------------------
        elif name == "get_employee_overtime":
            if user.role == "employee":
                return {"error": "Unauthorized to view workforce overtime reports."}

            period = arguments.get("period", "this_month")
            dept_filter = arguments.get("department")
            min_ot = arguments.get("min_overtime_hours")
            limit = arguments.get("limit", 10)

            start_date, end_date, period_label = DateRangeResolver.resolve_period(period=period)

            stmt = (
                select(
                    Employee.id,
                    Employee.first_name,
                    Employee.last_name,
                    Employee.employee_code,
                    Department.name.label("department_name"),
                    func.sum(AttendanceRecord.overtime_minutes).label("total_ot")
                )
                .join(AttendanceRecord, AttendanceRecord.employee_id == Employee.id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == org_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date,
                        AttendanceRecord.overtime_minutes > 0
                    )
                )
            )

            if dept_filter:
                stmt = stmt.where(
                    or_(
                        Department.name.ilike(f"%{dept_filter}%"),
                        Department.code.ilike(f"%{dept_filter}%")
                    )
                )

            stmt = (
                stmt.group_by(Employee.id, Employee.first_name, Employee.last_name, Employee.employee_code, Department.name)
                .order_by(desc("total_ot"))
            )

            res = (await db.execute(stmt)).all()
            overtime_list = []
            for emp_id, first, last, code, dept_name, ot_minutes in res:
                ot_hours = round((ot_minutes or 0) / 60.0, 1)
                if min_ot is not None and ot_hours < min_ot:
                    continue
                overtime_list.append({
                    "employee": f"{first} {last}",
                    "employee_code": code,
                    "department": dept_name or "General",
                    "overtime_hours": ot_hours
                })

            total_dept_ot = round(sum(e["overtime_hours"] for e in overtime_list), 1)

            return {
                "period": period_label,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "department_filter": dept_filter or "All Departments",
                "total_overtime_hours": total_dept_ot,
                "top_overtime_employees": overtime_list[:limit]
            }

        # -------------------------------------------------------------
        # Tool: get_absenteeism
        # -------------------------------------------------------------
        elif name == "get_absenteeism":
            if user.role == "employee":
                return {"error": "Unauthorized to view workforce absenteeism."}

            period = arguments.get("period", "today")
            dept_filter = arguments.get("department")
            limit = arguments.get("limit", 25)

            start_date, end_date, period_label = DateRangeResolver.resolve_period(period=period)

            stmt = (
                select(AttendanceRecord, Employee, Department)
                .join(Employee, Employee.id == AttendanceRecord.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == org_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date,
                        AttendanceRecord.status == "absent"
                    )
                )
            )

            if dept_filter:
                stmt = stmt.where(
                    or_(
                        Department.name.ilike(f"%{dept_filter}%"),
                        Department.code.ilike(f"%{dept_filter}%")
                    )
                )

            stmt = stmt.order_by(AttendanceRecord.date.desc(), Employee.last_name)
            res = (await db.execute(stmt)).all()

            absent_list = [
                {
                    "date": str(r.date),
                    "employee": f"{emp.first_name} {emp.last_name}",
                    "employee_code": emp.employee_code,
                    "department": dept.name if dept else "General",
                    "status": "Absent (Unexcused/No Clock-in)"
                }
                for r, emp, dept in res[:limit]
            ]

            return {
                "period": period_label,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "department_filter": dept_filter or "All Departments",
                "total_absent_count": len(res),
                "absent_employees": absent_list
            }

        # -------------------------------------------------------------
        # Tool: get_department_analytics
        # -------------------------------------------------------------
        elif name == "get_department_analytics":
            if user.role == "employee":
                return {"error": "Unauthorized to view department-level metrics."}

            period = arguments.get("period", "this_month")
            start_date, end_date, period_label = DateRangeResolver.resolve_period(period=period)

            depts = (await db.execute(select(Department).where(Department.organization_id == org_id))).scalars().all()
            analytics = []

            for d in depts:
                emps = (await db.execute(select(Employee).where(
                    and_(Employee.department_id == d.id, Employee.is_active == True)
                ))).scalars().all()
                total = len(emps)
                emp_ids = [e.id for e in emps]

                present = 0
                absent = 0
                late = 0
                ot_minutes = 0

                if emp_ids:
                    recs = (await db.execute(
                        select(AttendanceRecord).where(
                            and_(
                                AttendanceRecord.date >= start_date,
                                AttendanceRecord.date <= end_date,
                                AttendanceRecord.employee_id.in_(emp_ids)
                            )
                        )
                    )).scalars().all()

                    present = sum(1 for r in recs if r.status in ["present", "late", "half_day"])
                    absent = sum(1 for r in recs if r.status == "absent")
                    late = sum(1 for r in recs if r.late_minutes > 0 or r.status == "late")
                    ot_minutes = sum(r.overtime_minutes for r in recs)

                total_entries = present + absent
                att_rate = round((present / total_entries * 100), 1) if total_entries > 0 else 0.0
                absent_rate = round((absent / total_entries * 100), 1) if total_entries > 0 else 0.0
                ot_hours = round(ot_minutes / 60.0, 1)

                # Count anomalies for this department
                anom_count = 0
                if emp_ids:
                    anom_stmt = select(func.count(AttendanceAnomaly.id)).where(
                        and_(
                            AttendanceAnomaly.employee_id.in_(emp_ids),
                            AttendanceAnomaly.date >= start_date,
                            AttendanceAnomaly.date <= end_date
                        )
                    )
                    anom_count = (await db.execute(anom_stmt)).scalar() or 0

                # Compute attention priority
                attention = "Low"
                if absent_rate > 20 or late > (total * 3) or anom_count > 5:
                    attention = "High"
                elif absent_rate > 10 or late > total:
                    attention = "Medium"

                analytics.append({
                    "department": d.name,
                    "code": d.code,
                    "total_headcount": total,
                    "present_records": present,
                    "absent_records": absent,
                    "late_records": late,
                    "attendance_rate": att_rate,
                    "absenteeism_rate": absent_rate,
                    "overtime_hours": ot_hours,
                    "anomaly_flags": anom_count,
                    "hr_attention_needed": attention
                })

            # Sort by absenteeism_rate descending to highlight departments needing attention
            analytics.sort(key=lambda x: (x["absenteeism_rate"], x["late_records"]), reverse=True)
            highest_absenteeism_dept = analytics[0]["department"] if analytics else "None"

            return {
                "period": period_label,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "department_count": len(analytics),
                "highest_absenteeism_department": highest_absenteeism_dept,
                "departments": analytics
            }

        # -------------------------------------------------------------
        # Tool: get_workforce_correlations
        # -------------------------------------------------------------
        elif name == "get_workforce_correlations":
            if user.role == "employee":
                return {"error": "Unauthorized to view workforce correlation reports."}

            period = arguments.get("period", "this_month")
            dept_filter = arguments.get("department")
            min_late = arguments.get("min_late_count", 3)
            min_ot = arguments.get("min_overtime_hours", 5.0)

            start_date, end_date, period_label = DateRangeResolver.resolve_period(period=period)

            stmt = (
                select(
                    Employee.id,
                    Employee.first_name,
                    Employee.last_name,
                    Employee.employee_code,
                    Department.name.label("department_name"),
                    func.sum(case((AttendanceRecord.late_minutes > 0, 1), else_=0)).label("late_count"),
                    func.sum(AttendanceRecord.overtime_minutes).label("total_ot")
                )
                .join(AttendanceRecord, AttendanceRecord.employee_id == Employee.id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == org_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date
                    )
                )
            )

            if dept_filter:
                stmt = stmt.where(
                    or_(
                        Department.name.ilike(f"%{dept_filter}%"),
                        Department.code.ilike(f"%{dept_filter}%")
                    )
                )

            case_late_calc = func.sum(case((AttendanceRecord.late_minutes > 0, 1), else_=0))
            stmt = (
                stmt.group_by(Employee.id, Employee.first_name, Employee.last_name, Employee.employee_code, Department.name)
                .having(
                    and_(
                        case_late_calc >= min_late,
                        func.sum(AttendanceRecord.overtime_minutes) >= int(min_ot * 60)
                    )
                )
                .order_by(desc("late_count"), desc("total_ot"))
            )

            res = (await db.execute(stmt)).all()
            flagged = []
            for emp_id, first, last, code, dept_name, late_cnt, ot_mins in res:
                flagged.append({
                    "employee": f"{first} {last}",
                    "employee_code": code,
                    "department": dept_name or "General",
                    "late_arrivals": late_cnt,
                    "overtime_hours": round((ot_mins or 0) / 60.0, 1),
                    "pattern": "Repeated Lateness + High Overtime (Fatigue / Burnout Indicator)"
                })

            return {
                "period": period_label,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "criteria": f"Late arrivals >= {min_late} AND Overtime >= {min_ot}h",
                "flagged_employee_count": len(flagged),
                "flagged_employees": flagged
            }

        # -------------------------------------------------------------
        # Tool: search_attendance_policy
        # -------------------------------------------------------------
        elif name == "search_attendance_policy":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 4)
            matches = await PolicyService.search_policies(db, org_id, query, limit=limit)
            return {
                "query": query,
                "matches": matches
            }

        # -------------------------------------------------------------
        # Tool: get_anomaly_reports
        # -------------------------------------------------------------
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
                "total_flagged": len(res),
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

        # -------------------------------------------------------------
        # Tool: get_employee_profile
        # -------------------------------------------------------------
        elif name == "get_employee_profile":
            name_query = arguments.get("name")
            code = arguments.get("employee_code")
            email = arguments.get("email")

            stmt = select(Employee, Department).outerjoin(Department, Department.id == Employee.department_id).where(
                Employee.organization_id == org_id
            )
            if code:
                stmt = stmt.where(Employee.employee_code == code)
            elif email:
                stmt = stmt.where(Employee.email == email)
            elif name_query:
                # Search by first name or last name
                stmt = stmt.where(
                    or_(
                        Employee.first_name.ilike(f"%{name_query}%"),
                        Employee.last_name.ilike(f"%{name_query}%"),
                        func.concat(Employee.first_name, ' ', Employee.last_name).ilike(f"%{name_query}%")
                    )
                )
            else:
                return {"error": "Please provide an employee name, employee_code, or email."}

            res = (await db.execute(stmt)).first()
            if not res:
                return {"error": f"Employee '{name_query or code or email}' not found."}
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
