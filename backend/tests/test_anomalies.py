import pytest
from datetime import datetime, date, timedelta
from app.models.models import AttendanceRecord, AttendanceBreak
from app.services.anomaly_service import AnomalyService

def test_rule_based_missing_clock_out():
    past_date = date.today() - timedelta(days=2)
    record = AttendanceRecord(
        date=past_date,
        clock_in=datetime.combine(past_date, datetime.min.time().replace(hour=9)),
        clock_out=None,
        worked_minutes=0,
        overtime_minutes=0,
        late_minutes=0,
        status="incomplete"
    )
    anomalies = AnomalyService.detect_rule_based(record, [], [])
    types = [a["type"] for a in anomalies]
    assert "missing_clock_out" in types

def test_rule_based_excessive_overtime():
    record = AttendanceRecord(
        date=date.today(),
        clock_in=datetime.now(),
        clock_out=datetime.now(),
        worked_minutes=700,
        overtime_minutes=220, # > 180 min
        late_minutes=0,
        status="present"
    )
    anomalies = AnomalyService.detect_rule_based(record, [], [])
    types = [a["type"] for a in anomalies]
    assert "excessive_overtime" in types

def test_rule_based_abnormal_break():
    record = AttendanceRecord(
        date=date.today(),
        clock_in=datetime.now(),
        clock_out=datetime.now(),
        worked_minutes=480,
        overtime_minutes=0,
        late_minutes=0,
        status="present"
    )
    b = AttendanceBreak(
        break_start=datetime.now(),
        break_end=datetime.now() + timedelta(minutes=140),
        duration_minutes=140, # > 120 min
        reason="Extended appointment"
    )
    anomalies = AnomalyService.detect_rule_based(record, [b], [])
    types = [a["type"] for a in anomalies]
    assert "abnormal_break_duration" in types

def test_isolation_forest_ml_detection():
    # Construct 20 synthetic attendance records where one is an extreme outlier
    records = []
    for i in range(25):
        records.append(AttendanceRecord(
            id=f"rec_{i}",
            employee_id="emp_test",
            date=date.today() - timedelta(days=i),
            worked_minutes=480,
            overtime_minutes=0,
            late_minutes=0
        ))
    # Extreme outlier
    records.append(AttendanceRecord(
        id="rec_outlier",
        employee_id="emp_test",
        date=date.today() - timedelta(days=26),
        worked_minutes=950,
        overtime_minutes=470,
        late_minutes=120
    ))

    ml_anomalies = AnomalyService.train_and_predict_isolation_forest(records)
    assert len(ml_anomalies) > 0
    outlier_ids = [m["record_id"] for m in ml_anomalies]
    assert "rec_outlier" in outlier_ids
