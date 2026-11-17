from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from app.models.models import (
    Employee, Department, AttendanceRecord, AttendanceAnomaly, AttendanceBreak, LeaveRecord
)

class AnalyticsService:
    @staticmethod
    async def get_dashboard_data(
        db: AsyncSession,
        organization_id: str,
        target_date: Optional[date] = None,
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        today = target_date or date.today()
        yesterday = today - timedelta(days=1)

        # Base query for employees
        emp_query = select(Employee).where(
            and_(
                Employee.organization_id == organization_id,
                Employee.is_active == True
            )
        )
        if department_id:
            emp_query = emp_query.where(Employee.department_id == department_id)
        
        all_employees = (await db.execute(emp_query)).scalars().all()
        total_employees = len(all_employees)
        emp_ids = [e.id for e in all_employees]

        if not emp_ids:
            return {
                "kpis": {
                    "total_employees": 0,
                    "present_today": 0,
                    "absent_today": 0,
                    "late_arrivals": 0,
                    "overtime_hours": 0.0,
                    "attendance_rate": 0.0,
                    "comparison": {"present": 0.0, "late": 0.0, "overtime": 0.0}
                },
                "trends": [],
                "department_stats": [],
                "needs_attention": [],
                "recent_activity": [],
                "ai_insights": []
            }

        # Today's attendance records
        today_stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.organization_id == organization_id,
                AttendanceRecord.date == today,
                AttendanceRecord.employee_id.in_(emp_ids)
            )
        )
        today_records = (await db.execute(today_stmt)).scalars().all()

        present_today = sum(1 for r in today_records if r.status in ["present", "late", "half_day"])
        late_today = sum(1 for r in today_records if r.late_minutes > 0 or r.status == "late")
        absent_today = max(0, total_employees - present_today)
        overtime_mins = sum(r.overtime_minutes for r in today_records)
        overtime_hours = round(overtime_mins / 60.0, 1)
        attendance_rate = round((present_today / total_employees * 100), 1) if total_employees > 0 else 0.0

        # Yesterday's comparison
        yest_stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.organization_id == organization_id,
                AttendanceRecord.date == yesterday,
                AttendanceRecord.employee_id.in_(emp_ids)
            )
        )
        yest_records = (await db.execute(yest_stmt)).scalars().all()
        yest_present = sum(1 for r in yest_records if r.status in ["present", "late", "half_day"])
        yest_late = sum(1 for r in yest_records if r.late_minutes > 0 or r.status == "late")
        yest_ot = round(sum(r.overtime_minutes for r in yest_records) / 60.0, 1)

        present_change = round(((present_today - yest_present) / max(1, yest_present)) * 100, 1)
        late_change = round(((late_today - yest_late) / max(1, yest_late)) * 100, 1)
        ot_change = round(overtime_hours - yest_ot, 1)

        # 7-day attendance trend
        trend_start = today - timedelta(days=6)
        trend_stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.organization_id == organization_id,
                AttendanceRecord.date >= trend_start,
                AttendanceRecord.date <= today,
                AttendanceRecord.employee_id.in_(emp_ids)
            )
        )
        trend_records = (await db.execute(trend_stmt)).scalars().all()

        trends = []
        for d in range(7):
            cur_date = trend_start + timedelta(days=d)
            cur_day_records = [r for r in trend_records if r.date == cur_date]
            cur_pres = sum(1 for r in cur_day_records if r.status in ["present", "late", "half_day"])
            cur_late = sum(1 for r in cur_day_records if r.late_minutes > 0 or r.status == "late")
            cur_abs = max(0, total_employees - cur_pres)
            cur_rate = round((cur_pres / total_employees * 100), 1) if total_employees > 0 else 0.0
            trends.append({
                "date": cur_date.strftime("%b %d"),
                "present": cur_pres,
                "absent": cur_abs,
                "late": cur_late,
                "rate": cur_rate
            })

        # Department-wise breakdown
        dept_stmt = select(Department).where(Department.organization_id == organization_id)
        departments = (await db.execute(dept_stmt)).scalars().all()
        dept_stats = []
        for dept in departments:
            dept_emps = [e.id for e in all_employees if e.department_id == dept.id]
            if not dept_emps:
                continue
            dept_today_rec = [r for r in today_records if r.employee_id in dept_emps]
            dept_pres = sum(1 for r in dept_today_rec if r.status in ["present", "late", "half_day"])
            dept_abs = len(dept_emps) - dept_pres
            dept_rate = round((dept_pres / len(dept_emps) * 100), 1) if dept_emps else 0.0
            dept_stats.append({
                "department": dept.name,
                "present": dept_pres,
                "absent": dept_abs,
                "rate": dept_rate
            })

        # Needs attention items: Pending anomalies & Missing clock-outs
        anom_stmt = select(AttendanceAnomaly, Employee).join(Employee, Employee.id == AttendanceAnomaly.employee_id).where(
            and_(
                AttendanceAnomaly.organization_id == organization_id,
                AttendanceAnomaly.status == "pending"
            )
        ).order_by(desc(AttendanceAnomaly.created_at)).limit(5)
        anomalies_res = await db.execute(anom_stmt)
        needs_attention = []
        for anom, emp in anomalies_res.all():
            needs_attention.append({
                "id": anom.id,
                "type": anom.anomaly_type,
                "severity": anom.severity,
                "employee": f"{emp.first_name} {emp.last_name}",
                "date": str(anom.date),
                "explanation": anom.explanation
            })

        # Recent activity
        recent_stmt = (
            select(AttendanceRecord, Employee, Department)
            .join(Employee, Employee.id == AttendanceRecord.employee_id)
            .outerjoin(Department, Department.id == Employee.department_id)
            .where(
                and_(
                    AttendanceRecord.organization_id == organization_id,
                    AttendanceRecord.date == today
                )
            )
            .order_by(desc(AttendanceRecord.updated_at))
            .limit(10)
        )
        recent_res = await db.execute(recent_stmt)
        recent_activity = []
        for r, emp, dept in recent_res.all():
            recent_activity.append({
                "id": r.id,
                "employee": f"{emp.first_name} {emp.last_name}",
                "department": dept.name if dept else "General",
                "clock_in": r.clock_in.strftime("%H:%M") if r.clock_in else "-",
                "clock_out": r.clock_out.strftime("%H:%M") if r.clock_out else "-",
                "worked_hours": round(r.worked_minutes / 60.0, 1),
                "status": r.status
            })

        # AI Insights generated from actual database stats
        ai_insights = [
            {
                "title": "Attendance Health",
                "insight": f"Overall organization attendance rate is currently {attendance_rate}%, with {present_today} employees present.",
                "level": "positive" if attendance_rate >= 90 else "warning"
            },
            {
                "title": "Punctuality Observation",
                "insight": f"{late_today} employees arrived past the shift grace period today ({late_change}% change vs yesterday).",
                "level": "neutral" if late_today <= 3 else "warning"
            },
            {
                "title": "Overtime Utilization",
                "insight": f"Accumulated {overtime_hours} hours of overtime today across active workforce shifts.",
                "level": "neutral"
            }
        ]

        return {
            "kpis": {
                "total_employees": total_employees,
                "present_today": present_today,
                "absent_today": absent_today,
                "late_arrivals": late_today,
                "overtime_hours": overtime_hours,
                "attendance_rate": attendance_rate,
                "comparison": {
                    "present": present_change,
                    "late": late_change,
                    "overtime": ot_change
                }
            },
            "trends": trends,
            "department_stats": dept_stats,
            "needs_attention": needs_attention,
            "recent_activity": recent_activity,
            "ai_insights": ai_insights
        }
