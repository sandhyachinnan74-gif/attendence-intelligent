from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.models import AttendanceRecord, AttendanceAnomaly, AttendanceBreak, Employee, Shift
from app.core.exceptions import NotFoundException

class AnomalyService:
    @staticmethod
    def detect_rule_based(record: AttendanceRecord, breaks: List[AttendanceBreak], recent_records: List[AttendanceRecord]) -> List[Dict[str, Any]]:
        anomalies = []

        # 1. Missing clock-out
        if record.clock_in and not record.clock_out:
            # Check if current time is past date
            if date.today() > record.date:
                anomalies.append({
                    "type": "missing_clock_out",
                    "severity": "high",
                    "score": 0.85,
                    "method": "rule_based",
                    "explanation": f"Employee clocked in at {record.clock_in.strftime('%H:%M')} on {record.date} but never clocked out."
                })

        # 2. Excessive overtime
        if record.overtime_minutes > 180: # > 3 hours
            anomalies.append({
                "type": "excessive_overtime",
                "severity": "medium",
                "score": 0.70,
                "method": "rule_based",
                "explanation": f"Overtime duration of {record.overtime_minutes} minutes ({record.overtime_minutes // 60}h {record.overtime_minutes % 60}m) exceeds standard threshold of 180 minutes."
            })

        # 3. Unusually long shift
        if record.worked_minutes > 720: # > 12 hours
            anomalies.append({
                "type": "unusually_long_shift",
                "severity": "critical",
                "score": 0.95,
                "method": "rule_based",
                "explanation": f"Total worked time of {record.worked_minutes} minutes ({record.worked_minutes // 60}h) exceeds safety threshold of 12 hours."
            })

        # 4. Abnormal break duration
        total_break = sum(b.duration_minutes for b in breaks)
        if total_break > 120:
            anomalies.append({
                "type": "abnormal_break_duration",
                "severity": "low",
                "score": 0.50,
                "method": "rule_based",
                "explanation": f"Cumulative break duration of {total_break} minutes exceeds typical 60-120 minute allowance."
            })

        # 5. Repeated late arrivals (>= 3 times in last 7 days)
        lates_in_window = sum(1 for r in recent_records if r.late_minutes > 0 or r.status == "late")
        if (record.late_minutes > 0 or record.status == "late") and lates_in_window >= 3:
            anomalies.append({
                "type": "repeated_late_arrival",
                "severity": "medium",
                "score": 0.75,
                "method": "rule_based",
                "explanation": f"Employee has arrived late {lates_in_window} times within the recent tracking period."
            })

        return anomalies

    @staticmethod
    def train_and_predict_isolation_forest(
        records: List[AttendanceRecord]
    ) -> List[Dict[str, Any]]:
        """
        Trains IsolationForest on historical records and detects outlier points.
        Returns anomaly flags for records identified as outliers.
        """
        if len(records) < 15:
            # Insufficient samples for statistical isolation forest
            return []

        try:
            from sklearn.ensemble import IsolationForest

            # Features: [worked_minutes, overtime_minutes, late_minutes]
            features = []
            for r in records:
                features.append([
                    float(r.worked_minutes or 0),
                    float(r.overtime_minutes or 0),
                    float(r.late_minutes or 0),
                ])

            X = np.array(features)
            # Contamination rate ~ 5%
            clf = IsolationForest(contamination=0.05, random_state=42)
            clf.fit(X)
            preds = clf.predict(X) # -1 is anomaly, 1 is normal
            scores = clf.decision_function(X) # lower score = more anomalous

            results = []
            for i, pred in enumerate(preds):
                if pred == -1:
                    raw_score = float(scores[i])
                    # Normalize score to 0..1 scale
                    normalized_score = round(max(0.0, min(1.0, 0.5 - raw_score)), 2)
                    r = records[i]
                    results.append({
                        "record_id": r.id,
                        "employee_id": r.employee_id,
                        "date": r.date,
                        "type": "isolation_forest_outlier",
                        "severity": "high" if normalized_score > 0.8 else "medium",
                        "score": normalized_score,
                        "method": "isolation_forest",
                        "explanation": f"Unusual multivariate attendance profile: worked {r.worked_minutes}m, overtime {r.overtime_minutes}m, late {r.late_minutes}m (Outlier score: {normalized_score})."
                    })
            return results
        except Exception:
            return []

    @staticmethod
    async def run_detection_pipeline(db: AsyncSession, organization_id: str, target_date: Optional[date] = None) -> int:
        """
        Runs hybrid anomaly detection pipeline across recent records for organization.
        """
        date_filter = target_date or date.today()
        # Fetch records for the past 30 days
        start_date = date_filter - timedelta(days=30)

        stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.organization_id == organization_id,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= date_filter
            )
        )
        records = (await db.execute(stmt)).scalars().all()

        created_count = 0

        # Group by employee for window analysis
        emp_records: Dict[str, List[AttendanceRecord]] = {}
        for r in records:
            emp_records.setdefault(r.employee_id, []).append(r)

        # 1. Rule based
        for r in records:
            # fetch breaks
            break_stmt = select(AttendanceBreak).where(AttendanceBreak.attendance_record_id == r.id)
            breaks = (await db.execute(break_stmt)).scalars().all()

            recent = emp_records.get(r.employee_id, [])
            rule_anomalies = AnomalyService.detect_rule_based(r, breaks, recent)

            for a in rule_anomalies:
                # check if already exists
                check_stmt = select(AttendanceAnomaly).where(
                    and_(
                        AttendanceAnomaly.employee_id == r.employee_id,
                        AttendanceAnomaly.date == r.date,
                        AttendanceAnomaly.anomaly_type == a["type"]
                    )
                )
                existing = (await db.execute(check_stmt)).scalars().first()
                if not existing:
                    anomaly = AttendanceAnomaly(
                        organization_id=organization_id,
                        employee_id=r.employee_id,
                        attendance_record_id=r.id,
                        date=r.date,
                        anomaly_type=a["type"],
                        severity=a["severity"],
                        score=a["score"],
                        detection_method=a["method"],
                        explanation=a["explanation"],
                        status="pending"
                    )
                    db.add(anomaly)
                    created_count += 1

        # 2. Isolation Forest
        if len(records) >= 15:
            ml_anomalies = AnomalyService.train_and_predict_isolation_forest(records)
            for m in ml_anomalies:
                check_stmt = select(AttendanceAnomaly).where(
                    and_(
                        AttendanceAnomaly.employee_id == m["employee_id"],
                        AttendanceAnomaly.date == m["date"],
                        AttendanceAnomaly.anomaly_type == m["type"]
                    )
                )
                existing = (await db.execute(check_stmt)).scalars().first()
                if not existing:
                    anomaly = AttendanceAnomaly(
                        organization_id=organization_id,
                        employee_id=m["employee_id"],
                        attendance_record_id=m["record_id"],
                        date=m["date"],
                        anomaly_type=m["type"],
                        severity=m["severity"],
                        score=m["score"],
                        detection_method=m["method"],
                        explanation=m["explanation"],
                        status="pending"
                    )
                    db.add(anomaly)
                    created_count += 1

        await db.commit()
        return created_count
