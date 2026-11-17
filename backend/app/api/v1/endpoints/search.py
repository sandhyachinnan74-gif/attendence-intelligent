from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from app.core.database import get_db
from app.models.models import (
    User, Employee, Department, Shift, EmployeeShiftAssignment, Policy, AttendanceRecord, LeaveRecord, AttendanceAnomaly
)
from app.schemas.schemas import SearchResultGroup
from app.api.deps import get_current_user

router = APIRouter(prefix="/search", tags=["Global Search"])

@router.get("", response_model=SearchResultGroup)
async def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(5, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query_term = f"%{q.strip()}%"
    role = user.role
    org_id = user.organization_id

    # Resolve linked employee record for employee or HR
    emp_stmt = select(Employee).where(Employee.user_id == user.id)
    current_employee = (await db.execute(emp_stmt)).scalars().first()

    employees_res = []
    departments_res = []
    attendance_res = []
    shifts_res = []
    leave_res = []
    policies_res = []
    anomalies_res = []

    # 1. Employees Search
    if role in ["admin", "hr_manager"]:
        stmt = select(Employee, Department).outerjoin(
            Department, Department.id == Employee.department_id
        ).where(
            and_(
                Employee.organization_id == org_id,
                or_(
                    Employee.first_name.ilike(query_term),
                    Employee.last_name.ilike(query_term),
                    Employee.employee_code.ilike(query_term),
                    Employee.email.ilike(query_term),
                    Employee.designation.ilike(query_term)
                )
            )
        ).limit(limit)
        res = await db.execute(stmt)
        for emp, dept in res.all():
            employees_res.append({
                "id": emp.id,
                "title": f"{emp.first_name} {emp.last_name}",
                "subtitle": f"{emp.designation or 'Staff'} • {dept.name if dept else 'General'} ({emp.employee_code})",
                "link": f"/employees",
                "tag": "Employee"
            })
    elif role == "employee" and current_employee:
        full_name = f"{current_employee.first_name} {current_employee.last_name}"
        if q.lower() in full_name.lower() or q.lower() in current_employee.employee_code.lower() or "profile" in q.lower():
            employees_res.append({
                "id": current_employee.id,
                "title": f"{full_name} (My Profile)",
                "subtitle": f"{current_employee.designation or 'Staff'} • {current_employee.employee_code}",
                "link": "/settings",
                "tag": "My Profile"
            })

    # 2. Departments Search
    if role in ["admin", "hr_manager"]:
        dept_stmt = select(Department).where(
            and_(
                Department.organization_id == org_id,
                or_(
                    Department.name.ilike(query_term),
                    Department.code.ilike(query_term)
                )
            )
        ).limit(limit)
        res = await db.execute(dept_stmt)
        for d in res.scalars().all():
            departments_res.append({
                "id": d.id,
                "title": d.name,
                "subtitle": f"Code: {d.code}",
                "link": "/departments",
                "tag": "Department"
            })

    # 3. Shifts Search
    if role in ["admin", "hr_manager"]:
        shift_stmt = select(Shift).where(
            and_(
                Shift.organization_id == org_id,
                or_(
                    Shift.name.ilike(query_term),
                    Shift.code.ilike(query_term)
                )
            )
        ).limit(limit)
        res = await db.execute(shift_stmt)
        for s in res.scalars().all():
            shifts_res.append({
                "id": s.id,
                "title": s.name,
                "subtitle": f"{s.start_time.strftime('%H:%M')} – {s.end_time.strftime('%H:%M')} ({s.code})",
                "link": "/shifts",
                "tag": "Shift"
            })
    elif role == "employee" and current_employee:
        s_stmt = (
            select(Shift)
            .join(EmployeeShiftAssignment, EmployeeShiftAssignment.shift_id == Shift.id)
            .where(
                and_(
                    EmployeeShiftAssignment.employee_id == current_employee.id,
                    EmployeeShiftAssignment.is_active == True
                )
            )
        )
        s = (await db.execute(s_stmt)).scalars().first()
        if s and (q.lower() in s.name.lower() or q.lower() in s.code.lower() or "shift" in q.lower() or "schedule" in q.lower()):
            shifts_res.append({
                "id": s.id,
                "title": f"My Shift: {s.name}",
                "subtitle": f"{s.start_time.strftime('%H:%M')} – {s.end_time.strftime('%H:%M')} ({s.code})",
                "link": "/shifts",
                "tag": "My Shift"
            })

    # 4. Policies & Documents Search (Applicable to all roles)
    policy_stmt = select(Policy).where(
        and_(
            Policy.organization_id == org_id,
            or_(
                Policy.title.ilike(query_term),
                Policy.category.ilike(query_term)
            )
        )
    ).limit(limit)
    res = await db.execute(policy_stmt)
    for p in res.scalars().all():
        policies_res.append({
            "id": p.id,
            "title": p.title,
            "subtitle": f"Category: {p.category.replace('_', ' ').title()}",
            "link": "/policies",
            "tag": "Policy"
        })

    # 5. Attendance Records Search
    if role in ["admin", "hr_manager"]:
        att_stmt = (
            select(AttendanceRecord, Employee)
            .join(Employee, Employee.id == AttendanceRecord.employee_id)
            .where(
                and_(
                    AttendanceRecord.organization_id == org_id,
                    or_(
                        Employee.first_name.ilike(query_term),
                        Employee.last_name.ilike(query_term),
                        AttendanceRecord.status.ilike(query_term)
                    )
                )
            )
            .order_by(desc(AttendanceRecord.date))
            .limit(limit)
        )
        res = await db.execute(att_stmt)
        for r, emp in res.all():
            attendance_res.append({
                "id": r.id,
                "title": f"{emp.first_name} {emp.last_name} – {r.date}",
                "subtitle": f"Status: {r.status.title()} • Worked: {round(r.worked_minutes / 60, 1)}h",
                "link": "/attendance",
                "tag": "Attendance"
            })
    elif role == "employee" and current_employee:
        att_stmt = (
            select(AttendanceRecord)
            .where(
                and_(
                    AttendanceRecord.organization_id == org_id,
                    AttendanceRecord.employee_id == current_employee.id,
                    or_(
                        AttendanceRecord.status.ilike(query_term)
                    )
                )
            )
            .order_by(desc(AttendanceRecord.date))
            .limit(limit)
        )
        res = await db.execute(att_stmt)
        for r in res.scalars().all():
            attendance_res.append({
                "id": r.id,
                "title": f"My Attendance – {r.date}",
                "subtitle": f"Status: {r.status.title()} • Worked: {round(r.worked_minutes / 60, 1)}h",
                "link": "/attendance",
                "tag": "My Attendance"
            })

    # 6. Leave Records Search
    if role in ["admin", "hr_manager"]:
        leave_stmt = (
            select(LeaveRecord, Employee)
            .join(Employee, Employee.id == LeaveRecord.employee_id)
            .where(
                and_(
                    LeaveRecord.organization_id == org_id,
                    or_(
                        Employee.first_name.ilike(query_term),
                        Employee.last_name.ilike(query_term),
                        LeaveRecord.leave_type.ilike(query_term),
                        LeaveRecord.status.ilike(query_term)
                    )
                )
            )
            .order_by(desc(LeaveRecord.created_at))
            .limit(limit)
        )
        res = await db.execute(leave_stmt)
        for l, emp in res.all():
            leave_res.append({
                "id": l.id,
                "title": f"{emp.first_name} {emp.last_name} – {l.leave_type.title()} Leave",
                "subtitle": f"{l.start_date} to {l.end_date} ({l.days_count} days) • {l.status.upper()}",
                "link": "/leave",
                "tag": "Leave"
            })
    elif role == "employee" and current_employee:
        leave_stmt = (
            select(LeaveRecord)
            .where(
                and_(
                    LeaveRecord.organization_id == org_id,
                    LeaveRecord.employee_id == current_employee.id,
                    or_(
                        LeaveRecord.leave_type.ilike(query_term),
                        LeaveRecord.reason.ilike(query_term),
                        LeaveRecord.status.ilike(query_term)
                    )
                )
            )
            .order_by(desc(LeaveRecord.created_at))
            .limit(limit)
        )
        res = await db.execute(leave_stmt)
        for l in res.scalars().all():
            leave_res.append({
                "id": l.id,
                "title": f"My {l.leave_type.title()} Leave",
                "subtitle": f"{l.start_date} to {l.end_date} ({l.days_count} days) • {l.status.upper()}",
                "link": "/leave",
                "tag": "My Leave"
            })

    # 7. Anomalies (Admin & HR Manager Only)
    if role in ["admin", "hr_manager"]:
        anom_stmt = (
            select(AttendanceAnomaly, Employee)
            .join(Employee, Employee.id == AttendanceAnomaly.employee_id)
            .where(
                and_(
                    AttendanceAnomaly.organization_id == org_id,
                    or_(
                        AttendanceAnomaly.anomaly_type.ilike(query_term),
                        AttendanceAnomaly.explanation.ilike(query_term),
                        Employee.first_name.ilike(query_term),
                        Employee.last_name.ilike(query_term)
                    )
                )
            )
            .order_by(desc(AttendanceAnomaly.created_at))
            .limit(limit)
        )
        res = await db.execute(anom_stmt)
        for a, emp in res.all():
            anomalies_res.append({
                "id": a.id,
                "title": f"{a.anomaly_type.replace('_', ' ').title()} – {emp.first_name} {emp.last_name}",
                "subtitle": f"Severity: {a.severity.upper()} • Date: {a.date}",
                "link": "/anomalies",
                "tag": "Anomaly"
            })

    total_count = (
        len(employees_res) + len(departments_res) + len(attendance_res) +
        len(shifts_res) + len(leave_res) + len(policies_res) + len(anomalies_res)
    )

    return {
        "query": q,
        "total_results": total_count,
        "employees": employees_res,
        "departments": departments_res,
        "attendance": attendance_res,
        "shifts": shifts_res,
        "leave": leave_res,
        "policies": policies_res,
        "anomalies": anomalies_res
    }
