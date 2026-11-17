from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.models import (
    AttendanceRecord, AttendanceBreak, Employee, Shift, EmployeeShiftAssignment, AttendanceCorrectionHistory
)
from app.core.exceptions import ConflictException, NotFoundException, ValidationException

class AttendanceService:
    @staticmethod
    async def get_active_shift(db: AsyncSession, employee_id: str, target_date: date) -> Optional[Shift]:
        """Fetch current effective shift for employee on target date."""
        stmt = (
            select(Shift)
            .join(EmployeeShiftAssignment, EmployeeShiftAssignment.shift_id == Shift.id)
            .where(
                and_(
                    EmployeeShiftAssignment.employee_id == employee_id,
                    EmployeeShiftAssignment.is_active == True,
                    EmployeeShiftAssignment.effective_from <= target_date,
                    (EmployeeShiftAssignment.effective_to.is_(None) | (EmployeeShiftAssignment.effective_to >= target_date))
                )
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    def calculate_shift_metrics(
        clock_in: datetime,
        clock_out: Optional[datetime],
        shift: Optional[Shift],
        total_break_minutes: int = 0
    ) -> Tuple[int, int, int, str]:
        """
        Returns (worked_minutes, overtime_minutes, late_minutes, status).
        Deterministic business logic.
        """
        late_minutes = 0
        worked_minutes = 0
        overtime_minutes = 0
        status = "present"

        if shift:
            shift_start_dt = datetime.combine(clock_in.date(), shift.start_time)
            # If overnight shift and clock in after midnight or shift start
            grace_dt = shift_start_dt + timedelta(minutes=shift.grace_period_minutes)
            if clock_in > grace_dt:
                late_diff = (clock_in - shift_start_dt).total_seconds() / 60
                late_minutes = max(0, int(late_diff))
                status = "late"

        if clock_out:
            raw_worked = (clock_out - clock_in).total_seconds() / 60
            worked_minutes = max(0, int(raw_worked) - total_break_minutes)
            
            # Required minutes
            req_minutes = int(shift.required_hours * 60) if shift else 480
            if worked_minutes > req_minutes:
                overtime_minutes = worked_minutes - req_minutes
            elif worked_minutes < (req_minutes / 2):
                status = "half_day"
        else:
            status = "incomplete"

        return worked_minutes, overtime_minutes, late_minutes, status

    @staticmethod
    async def clock_in(db: AsyncSession, organization_id: str, employee_id: str, custom_time: Optional[datetime] = None) -> AttendanceRecord:
        now = custom_time or datetime.now(timezone.utc).replace(tzinfo=None)
        today = now.date()

        # Check existing record for today
        stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date == today
            )
        )
        existing = (await db.execute(stmt)).scalars().first()
        if existing and existing.clock_in is not None:
            raise ConflictException(f"Employee {employee_id} has already clocked in today at {existing.clock_in}")

        shift = await AttendanceService.get_active_shift(db, employee_id, today)
        worked, ot, late, status = AttendanceService.calculate_shift_metrics(now, None, shift)

        if not existing:
            record = AttendanceRecord(
                organization_id=organization_id,
                employee_id=employee_id,
                date=today,
                clock_in=now,
                clock_out=None,
                worked_minutes=worked,
                overtime_minutes=ot,
                late_minutes=late,
                status=status,
                is_corrected=False
            )
            db.add(record)
        else:
            record = existing
            record.clock_in = now
            record.late_minutes = late
            record.status = status

        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def clock_out(db: AsyncSession, organization_id: str, employee_id: str, custom_time: Optional[datetime] = None) -> AttendanceRecord:
        now = custom_time or datetime.now(timezone.utc).replace(tzinfo=None)
        today = now.date()

        stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date == today
            )
        )
        record = (await db.execute(stmt)).scalars().first()
        if not record or not record.clock_in:
            raise ValidationException(f"No active clock-in found for employee {employee_id} on {today}")
        if record.clock_out is not None:
            raise ConflictException(f"Employee has already clocked out at {record.clock_out}")

        # Ensure ongoing breaks are closed
        break_stmt = select(AttendanceBreak).where(
            and_(
                AttendanceBreak.attendance_record_id == record.id,
                AttendanceBreak.break_end.is_(None)
            )
        )
        open_break = (await db.execute(break_stmt)).scalars().first()
        if open_break:
            open_break.break_end = now
            open_break.duration_minutes = max(0, int((now - open_break.break_start).total_seconds() / 60))

        # Calculate total break minutes
        all_breaks_stmt = select(AttendanceBreak).where(AttendanceBreak.attendance_record_id == record.id)
        all_breaks = (await db.execute(all_breaks_stmt)).scalars().all()
        total_breaks = sum(b.duration_minutes for b in all_breaks)

        shift = await AttendanceService.get_active_shift(db, employee_id, today)
        worked, ot, late, status = AttendanceService.calculate_shift_metrics(
            record.clock_in, now, shift, total_break_minutes=total_breaks
        )

        record.clock_out = now
        record.worked_minutes = worked
        record.overtime_minutes = ot
        record.late_minutes = late
        record.status = status

        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def toggle_break(db: AsyncSession, organization_id: str, employee_id: str, reason: str = "Normal Break") -> AttendanceBreak:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        today = now.date()

        stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.date == today
            )
        )
        record = (await db.execute(stmt)).scalars().first()
        if not record or not record.clock_in:
            raise ValidationException("Must clock in before taking a break")
        if record.clock_out is not None:
            raise ValidationException("Cannot take a break after clocking out")

        # Check for open break
        break_stmt = select(AttendanceBreak).where(
            and_(
                AttendanceBreak.attendance_record_id == record.id,
                AttendanceBreak.break_end.is_(None)
            )
        )
        open_break = (await db.execute(break_stmt)).scalars().first()
        if open_break:
            # End break
            open_break.break_end = now
            open_break.duration_minutes = max(0, int((now - open_break.break_start).total_seconds() / 60))
            await db.commit()
            await db.refresh(open_break)
            return open_break
        else:
            # Start new break
            new_break = AttendanceBreak(
                attendance_record_id=record.id,
                break_start=now,
                break_end=None,
                duration_minutes=0,
                reason=reason
            )
            db.add(new_break)
            await db.commit()
            await db.refresh(new_break)
            return new_break

    @staticmethod
    async def correct_attendance(
        db: AsyncSession,
        record_id: str,
        corrected_by: str,
        new_clock_in: Optional[datetime],
        new_clock_out: Optional[datetime],
        reason: str
    ) -> AttendanceRecord:
        stmt = select(AttendanceRecord).where(AttendanceRecord.id == record_id)
        record = (await db.execute(stmt)).scalars().first()
        if not record:
            raise NotFoundException("Attendance record not found")

        # Save history audit
        history = AttendanceCorrectionHistory(
            attendance_record_id=record.id,
            corrected_by=corrected_by,
            previous_clock_in=record.clock_in,
            new_clock_in=new_clock_in or record.clock_in,
            previous_clock_out=record.clock_out,
            new_clock_out=new_clock_out or record.clock_out,
            reason=reason
        )
        db.add(history)

        record.clock_in = new_clock_in or record.clock_in
        record.clock_out = new_clock_out or record.clock_out
        record.is_corrected = True

        # Recalculate
        shift = await AttendanceService.get_active_shift(db, record.employee_id, record.date)
        worked, ot, late, status = AttendanceService.calculate_shift_metrics(
            record.clock_in, record.clock_out, shift
        )
        record.worked_minutes = worked
        record.overtime_minutes = ot
        record.late_minutes = late
        record.status = status

        await db.commit()
        await db.refresh(record)
        return record
