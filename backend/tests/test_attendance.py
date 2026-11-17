import pytest
from datetime import datetime, date, time, timedelta
from app.models.models import Shift
from app.services.attendance_service import AttendanceService

def test_calculate_shift_metrics_normal():
    shift = Shift(
        name="General Shift",
        start_time=time(9, 0),
        end_time=time(17, 30),
        grace_period_minutes=15,
        required_hours=8.0,
        is_overnight=False
    )
    clock_in = datetime(2026, 11, 17, 8, 55, 0)
    clock_out = datetime(2026, 11, 17, 17, 35, 0)
    worked, ot, late, status = AttendanceService.calculate_shift_metrics(
        clock_in=clock_in,
        clock_out=clock_out,
        shift=shift,
        total_break_minutes=40
    )
    # Total minutes between 8:55 and 17:35 = 8h 40m = 520 min. Minus 40 min break = 480 min (8.0 hours)
    assert worked == 480
    assert late == 0
    assert ot == 0
    assert status == "present"

def test_calculate_shift_metrics_late():
    shift = Shift(
        name="General Shift",
        start_time=time(9, 0),
        end_time=time(17, 30),
        grace_period_minutes=15,
        required_hours=8.0,
        is_overnight=False
    )
    # Arriving at 9:25 (10 mins past 15m grace period)
    clock_in = datetime(2026, 11, 17, 9, 25, 0)
    clock_out = datetime(2026, 11, 17, 17, 30, 0)
    worked, ot, late, status = AttendanceService.calculate_shift_metrics(
        clock_in=clock_in,
        clock_out=clock_out,
        shift=shift,
        total_break_minutes=0
    )
    assert late == 25
    assert status == "late"

def test_calculate_shift_metrics_overtime():
    shift = Shift(
        name="General Shift",
        start_time=time(9, 0),
        end_time=time(17, 30),
        grace_period_minutes=15,
        required_hours=8.0,
        is_overnight=False
    )
    clock_in = datetime(2026, 11, 17, 9, 0, 0)
    # Worked 10 hours without break = 600 min
    clock_out = datetime(2026, 11, 17, 19, 0, 0)
    worked, ot, late, status = AttendanceService.calculate_shift_metrics(
        clock_in=clock_in,
        clock_out=clock_out,
        shift=shift,
        total_break_minutes=0
    )
    assert worked == 600
    assert ot == 120 # 2 hours overtime
    assert late == 0

def test_calculate_shift_metrics_half_day():
    shift = Shift(
        name="General Shift",
        start_time=time(9, 0),
        end_time=time(17, 30),
        grace_period_minutes=15,
        required_hours=8.0,
        is_overnight=False
    )
    clock_in = datetime(2026, 11, 17, 9, 0, 0)
    # Clocked out after only 3 hours (less than half of 8h)
    clock_out = datetime(2026, 11, 17, 12, 0, 0)
    worked, ot, late, status = AttendanceService.calculate_shift_metrics(
        clock_in=clock_in,
        clock_out=clock_out,
        shift=shift,
        total_break_minutes=0
    )
    assert worked == 180
    assert status == "half_day"
