import io
import csv
from datetime import date
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import AttendanceRecord, Employee, Department

class ExportService:
    @staticmethod
    async def export_attendance_csv(db: AsyncSession, organization_id: str, start_date: date, end_date: date) -> io.StringIO:
        stmt = (
            select(AttendanceRecord, Employee, Department)
            .join(Employee, Employee.id == AttendanceRecord.employee_id)
            .outerjoin(Department, Department.id == Employee.department_id)
            .where(
                and_(
                    AttendanceRecord.organization_id == organization_id,
                    AttendanceRecord.date >= start_date,
                    AttendanceRecord.date <= end_date
                )
            )
            .order_by(AttendanceRecord.date.desc())
        )
        results = (await db.execute(stmt)).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Date", "Employee Code", "Employee Name", "Department",
            "Clock In", "Clock Out", "Worked Hours", "Late Minutes", "Overtime Minutes", "Status", "Corrected"
        ])

        for r, emp, dept in results:
            writer.writerow([
                str(r.date),
                emp.employee_code,
                f"{emp.first_name} {emp.last_name}",
                dept.name if dept else "General",
                r.clock_in.strftime("%Y-%m-%d %H:%M:%S") if r.clock_in else "",
                r.clock_out.strftime("%Y-%m-%d %H:%M:%S") if r.clock_out else "",
                round(r.worked_minutes / 60.0, 2),
                r.late_minutes,
                r.overtime_minutes,
                r.status,
                "Yes" if r.is_corrected else "No"
            ])

        output.seek(0)
        return output

    @staticmethod
    async def export_attendance_xlsx(db: AsyncSession, organization_id: str, start_date: date, end_date: date) -> io.BytesIO:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance Records"

        headers = [
            "Date", "Employee Code", "Employee Name", "Department",
            "Clock In", "Clock Out", "Worked Hours", "Late Minutes", "Overtime Minutes", "Status", "Corrected"
        ]
        ws.append(headers)

        stmt = (
            select(AttendanceRecord, Employee, Department)
            .join(Employee, Employee.id == AttendanceRecord.employee_id)
            .outerjoin(Department, Department.id == Employee.department_id)
            .where(
                and_(
                    AttendanceRecord.organization_id == organization_id,
                    AttendanceRecord.date >= start_date,
                    AttendanceRecord.date <= end_date
                )
            )
            .order_by(AttendanceRecord.date.desc())
        )
        results = (await db.execute(stmt)).all()

        for r, emp, dept in results:
            ws.append([
                str(r.date),
                emp.employee_code,
                f"{emp.first_name} {emp.last_name}",
                dept.name if dept else "General",
                r.clock_in.strftime("%Y-%m-%d %H:%M:%S") if r.clock_in else "",
                r.clock_out.strftime("%Y-%m-%d %H:%M:%S") if r.clock_out else "",
                round(r.worked_minutes / 60.0, 2),
                r.late_minutes,
                r.overtime_minutes,
                r.status,
                "Yes" if r.is_corrected else "No"
            ])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output
