from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func
from app.models.models import (
    User, Employee, Department, AttendanceRecord, AttendanceBreak,
    Shift, EmployeeShiftAssignment, LeaveRecord, AttendanceAnomaly
)
from app.core.exceptions import ForbiddenException, ValidationException

class ExportQueryBuilder:
    @staticmethod
    async def get_authorized_scope(
        db: AsyncSession,
        user: User,
        current_employee: Optional[Employee],
        scope_type: str,
        requested_dept_ids: Optional[List[str]],
        requested_emp_ids: Optional[List[str]]
    ) -> Tuple[Optional[List[str]], Optional[List[str]], str]:
        """
        Returns (effective_dept_ids, effective_emp_ids, scope_summary).
        Guarantees role isolation:
        - Employee: strictly their own employee profile.
        - HR Manager: strictly their authorized departments/employees.
        - Admin: full organization.
        """
        if user.role == "employee":
            if not current_employee:
                emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()
                if not emp:
                    raise ForbiddenException("No employee profile found for user.")
                current_employee = emp
            return None, [current_employee.id], f"Personal Records ({current_employee.first_name} {current_employee.last_name})"

        # Admin & HR Manager scoping
        hr_allowed_dept_ids = None
        if user.role == "hr_manager":
            # If HR has a specific department
            hr_emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()
            if hr_emp and hr_emp.department_id:
                hr_allowed_dept_ids = [hr_emp.department_id]

        effective_depts = None
        effective_emps = None
        summary = "Entire Organization"

        if scope_type == "organization":
            if user.role == "hr_manager" and hr_allowed_dept_ids:
                effective_depts = hr_allowed_dept_ids
                summary = "Authorized Departments"
            else:
                summary = "Entire Organization"

        elif scope_type in ["department", "specific_department"]:
            if not requested_dept_ids or len(requested_dept_ids) == 0:
                raise ValidationException("Please select a department for the report.")
            dept_id = requested_dept_ids[0]
            if hr_allowed_dept_ids and dept_id not in hr_allowed_dept_ids:
                raise ForbiddenException("Department is outside your authorized HR scope.")
            effective_depts = [dept_id]
            dept = (await db.execute(select(Department).where(Department.id == dept_id))).scalars().first()
            summary = f"Department: {dept.name if dept else 'Selected'}"

        elif scope_type in ["multi_department", "multiple_departments"]:
            if not requested_dept_ids or len(requested_dept_ids) == 0:
                raise ValidationException("Please select at least one department.")
            if hr_allowed_dept_ids:
                for d in requested_dept_ids:
                    if d not in hr_allowed_dept_ids:
                        raise ForbiddenException("One or more selected departments are outside your authorized HR scope.")
            effective_depts = requested_dept_ids
            depts = (await db.execute(select(Department).where(Department.id.in_(requested_dept_ids)))).scalars().all()
            summary = f"Departments: {', '.join(d.name for d in depts)}"

        elif scope_type in ["individual_employee", "employee"]:
            if not requested_emp_ids or len(requested_emp_ids) == 0:
                raise ValidationException("Please select an employee.")
            emp_id = requested_emp_ids[0]
            emp = (await db.execute(select(Employee).where(Employee.id == emp_id))).scalars().first()
            if not emp:
                raise ValidationException("Employee not found.")
            if hr_allowed_dept_ids and emp.department_id not in hr_allowed_dept_ids:
                raise ForbiddenException("Employee is outside your authorized HR departmental scope.")
            effective_emps = [emp.id]
            summary = f"Employee: {emp.first_name} {emp.last_name} ({emp.employee_code})"

        elif scope_type in ["multi_employee", "multiple_employees"]:
            if not requested_emp_ids or len(requested_emp_ids) == 0:
                raise ValidationException("Please select at least one employee.")
            emps = (await db.execute(select(Employee).where(Employee.id.in_(requested_emp_ids)))).scalars().all()
            if hr_allowed_dept_ids:
                for e in emps:
                    if e.department_id not in hr_allowed_dept_ids:
                        raise ForbiddenException(f"Employee {e.first_name} {e.last_name} is outside your authorized scope.")
            effective_emps = [e.id for e in emps]
            summary = f"Employees ({len(emps)} selected)"

        return effective_depts, effective_emps, summary

    @staticmethod
    async def fetch_report_data(
        db: AsyncSession,
        user: User,
        current_employee: Optional[Employee],
        report_type: str,
        scope_type: str,
        department_ids: Optional[List[str]],
        employee_ids: Optional[List[str]],
        start_date: date,
        end_date: date,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes authorized query and formats rows into list of dictionaries.
        """
        eff_depts, eff_emps, scope_summary = await ExportQueryBuilder.get_authorized_scope(
            db, user, current_employee, scope_type, department_ids, employee_ids
        )

        rows: List[Dict[str, Any]] = []
        unique_emps = set()
        unique_depts = set()

        # -------------------------------------------------------------
        # BRANCH A: EMPLOYEE DIRECTORY & WORKFORCE REPORTS
        # -------------------------------------------------------------
        if report_type in ["employee_directory", "workforce_complete"]:
            stmt = (
                select(Employee, Department)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(Employee.organization_id == user.organization_id)
            )
            if eff_depts:
                stmt = stmt.where(Employee.department_id.in_(eff_depts))
            if eff_emps:
                stmt = stmt.where(Employee.id.in_(eff_emps))

            if filters:
                if filters.get("status") == "active":
                    stmt = stmt.where(Employee.is_active == True)
                elif filters.get("status") == "inactive":
                    stmt = stmt.where(Employee.is_active == False)

            stmt = stmt.order_by(Employee.first_name, Employee.last_name)
            res = (await db.execute(stmt)).all()

            for emp, dept in res:
                dept_name = dept.name if dept else "General"
                unique_emps.add(emp.id)
                unique_depts.add(dept_name)
                rows.append({
                    "employee_code": emp.employee_code,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "email": emp.email,
                    "department": dept_name,
                    "designation": emp.designation or "N/A",
                    "phone": emp.phone or "N/A",
                    "date_of_joining": str(emp.date_of_joining),
                    "current_shift": "General Shift (09:00 - 17:30)",
                    "is_active": "Active" if emp.is_active else "Inactive"
                })

        # -------------------------------------------------------------
        # BRANCH B: LEAVE REPORTS
        # -------------------------------------------------------------
        elif "leave" in report_type:
            stmt = (
                select(LeaveRecord, Employee, Department)
                .join(Employee, Employee.id == LeaveRecord.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        LeaveRecord.organization_id == user.organization_id,
                        LeaveRecord.start_date <= end_date,
                        LeaveRecord.end_date >= start_date
                    )
                )
            )
            if eff_depts:
                stmt = stmt.where(Employee.department_id.in_(eff_depts))
            if eff_emps:
                stmt = stmt.where(Employee.id.in_(eff_emps))

            if filters and filters.get("leave_type"):
                stmt = stmt.where(LeaveRecord.leave_type == filters["leave_type"])
            if filters and filters.get("status"):
                stmt = stmt.where(LeaveRecord.status == filters["status"])

            stmt = stmt.order_by(desc(LeaveRecord.start_date))
            res = (await db.execute(stmt)).all()

            for l, emp, dept in res:
                dept_name = dept.name if dept else "General"
                unique_emps.add(emp.id)
                unique_depts.add(dept_name)
                rows.append({
                    "employee_code": emp.employee_code,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "department": dept_name,
                    "leave_type": l.leave_type.capitalize(),
                    "start_date": str(l.start_date),
                    "end_date": str(l.end_date),
                    "days_count": l.days_count,
                    "reason": l.reason or "-",
                    "status": l.status.capitalize(),
                    "created_at": l.created_at.strftime("%Y-%m-%d %H:%M") if l.created_at else "-"
                })

        # -------------------------------------------------------------
        # BRANCH C: SHIFT REPORTS
        # -------------------------------------------------------------
        elif "shift" in report_type:
            stmt = (
                select(EmployeeShiftAssignment, Shift, Employee, Department)
                .join(Shift, Shift.id == EmployeeShiftAssignment.shift_id)
                .join(Employee, Employee.id == EmployeeShiftAssignment.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(Employee.organization_id == user.organization_id)
            )
            if eff_depts:
                stmt = stmt.where(Employee.department_id.in_(eff_depts))
            if eff_emps:
                stmt = stmt.where(Employee.id.in_(eff_emps))

            res = (await db.execute(stmt)).all()
            for sa, s, emp, dept in res:
                dept_name = dept.name if dept else "General"
                unique_emps.add(emp.id)
                unique_depts.add(dept_name)
                rows.append({
                    "employee_code": emp.employee_code,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "department": dept_name,
                    "shift_name": s.name,
                    "shift_code": s.code,
                    "scheduled_start": s.start_time.strftime("%H:%M") if s.start_time else "-",
                    "scheduled_end": s.end_time.strftime("%H:%M") if s.end_time else "-",
                    "required_hours": s.required_hours,
                    "effective_from": str(sa.effective_from)
                })

        # -------------------------------------------------------------
        # BRANCH D: ANOMALY REPORTS
        # -------------------------------------------------------------
        elif "anomaly" in report_type:
            stmt = (
                select(AttendanceAnomaly, AttendanceRecord, Employee, Department)
                .join(AttendanceRecord, AttendanceRecord.id == AttendanceAnomaly.attendance_record_id)
                .join(Employee, Employee.id == AttendanceRecord.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceAnomaly.organization_id == user.organization_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date
                    )
                )
            )
            if eff_depts:
                stmt = stmt.where(Employee.department_id.in_(eff_depts))
            if eff_emps:
                stmt = stmt.where(Employee.id.in_(eff_emps))

            res = (await db.execute(stmt)).all()
            for anom, att, emp, dept in res:
                dept_name = dept.name if dept else "General"
                unique_emps.add(emp.id)
                unique_depts.add(dept_name)
                rows.append({
                    "date": str(att.date),
                    "employee_code": emp.employee_code,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "department": dept_name,
                    "anomaly_type": anom.anomaly_type.replace("_", " ").title(),
                    "severity": anom.severity.upper(),
                    "explanation": anom.explanation or "-",
                    "is_resolved": "Resolved" if anom.is_resolved else "Pending Review"
                })

        # -------------------------------------------------------------
        # BRANCH E: ATTENDANCE, OVERTIME, WORKING HOURS, LATE ARRIVALS
        # -------------------------------------------------------------
        else:
            stmt = (
                select(AttendanceRecord, Employee, Department)
                .join(Employee, Employee.id == AttendanceRecord.employee_id)
                .outerjoin(Department, Department.id == Employee.department_id)
                .where(
                    and_(
                        AttendanceRecord.organization_id == user.organization_id,
                        AttendanceRecord.date >= start_date,
                        AttendanceRecord.date <= end_date
                    )
                )
            )
            if eff_depts:
                stmt = stmt.where(Employee.department_id.in_(eff_depts))
            if eff_emps:
                stmt = stmt.where(Employee.id.in_(eff_emps))

            if report_type in ["late_arrivals", "my_late_arrivals"]:
                stmt = stmt.where(or_(AttendanceRecord.late_minutes > 0, AttendanceRecord.status == "late"))
            elif report_type in ["overtime_report", "my_overtime"]:
                stmt = stmt.where(AttendanceRecord.overtime_minutes > 0)

            if filters:
                if filters.get("status"):
                    stmt = stmt.where(AttendanceRecord.status == filters["status"])
                if filters.get("min_late_minutes"):
                    stmt = stmt.where(AttendanceRecord.late_minutes >= int(filters["min_late_minutes"]))
                if filters.get("min_overtime_hours"):
                    stmt = stmt.where(AttendanceRecord.overtime_minutes >= int(float(filters["min_overtime_hours"]) * 60))

            stmt = stmt.order_by(desc(AttendanceRecord.date), Employee.first_name)
            res = (await db.execute(stmt)).all()

            for att, emp, dept in res:
                dept_name = dept.name if dept else "General"
                unique_emps.add(emp.id)
                unique_depts.add(dept_name)

                worked_hrs = round(att.worked_minutes / 60.0, 2)
                ot_hrs = round(att.overtime_minutes / 60.0, 2)
                reg_hrs = max(0.0, round(worked_hrs - ot_hrs, 2))

                rows.append({
                    "date": str(att.date),
                    "employee_code": emp.employee_code,
                    "employee_name": f"{emp.first_name} {emp.last_name}",
                    "department": dept_name,
                    "shift_name": "General Shift (09:00 - 17:30)",
                    "scheduled_start": "09:00",
                    "scheduled_end": "17:30",
                    "clock_in": att.clock_in.strftime("%H:%M:%S") if att.clock_in else "-",
                    "clock_out": att.clock_out.strftime("%H:%M:%S") if att.clock_out else "-",
                    "break_duration": 0,
                    "worked_hours": worked_hrs,
                    "regular_hours": reg_hrs,
                    "overtime_hours": ot_hrs,
                    "total_hours": worked_hrs,
                    "late_minutes": att.late_minutes,
                    "status": att.status.replace("_", " ").capitalize()
                })

        meta = {
            "scope_summary": scope_summary,
            "employees_count": len(unique_emps),
            "departments_count": len(unique_depts),
            "total_records": len(rows),
            "unique_departments": list(unique_depts)
        }
        return rows, meta
