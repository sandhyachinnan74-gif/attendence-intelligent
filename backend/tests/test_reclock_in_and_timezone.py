import pytest
from datetime import datetime, date
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_sessionmaker
from app.core.security import create_access_token
from app.models.models import User, Employee, AttendanceRecord
from sqlalchemy import select, delete

@pytest.mark.asyncio
async def test_clock_in_timezone_and_reclock_lifecycle():
    sm = get_sessionmaker()
    async with sm() as db:
        user = (await db.execute(select(User).where(User.email == "employee@attendai.com"))).scalars().first()
        emp = (await db.execute(select(Employee).where(Employee.user_id == user.id))).scalars().first()
        assert user is not None and emp is not None

        # Clean any today record for clean test
        today = date.today()
        await db.execute(delete(AttendanceRecord).where(AttendanceRecord.employee_id == emp.id, AttendanceRecord.date == today))
        await db.commit()

        token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role, "org_id": user.organization_id})

    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Clock In
        cin_res = await ac.post("/api/v1/attendance/clock-in", json={}, headers=headers)
        assert cin_res.status_code == 200, cin_res.text
        cin_data = cin_res.json()

        # Verify time matches local wall-clock hour (not UTC offset by 5.5 hours)
        local_now = datetime.now()
        clock_in_dt = datetime.fromisoformat(cin_data["clock_in"])
        assert clock_in_dt.hour == local_now.hour, f"Expected clock_in hour {local_now.hour}, got {clock_in_dt.hour}"
        assert cin_data["clock_out"] is None

        # 2. Clock Out
        cout_res = await ac.post("/api/v1/attendance/clock-out", json={}, headers=headers)
        assert cout_res.status_code == 200, cout_res.text
        cout_data = cout_res.json()
        assert cout_data["clock_out"] is not None

        # 3. Test Re-clock In (resume shift)
        reclock_res = await ac.post("/api/v1/attendance/re-clock-in", json={}, headers=headers)
        assert reclock_res.status_code == 200, reclock_res.text
        reclock_data = reclock_res.json()
        assert reclock_data["clock_out"] is None
        assert reclock_data["is_corrected"] is True

        # 4. Verify employee dashboard reflects actively working
        dash_res = await ac.get("/api/v1/analytics/employee-dashboard", headers=headers)
        assert dash_res.status_code == 200, dash_res.text
        dash_data = dash_res.json()
        assert dash_data["today_record"] is not None
        assert dash_data["today_record"]["clock_out"] is None
        assert dash_data["kpis"]["today_status"] == "actively_working"

        # 5. Clean up today's record after test
        async with sm() as db:
            await db.execute(delete(AttendanceRecord).where(AttendanceRecord.employee_id == emp.id, AttendanceRecord.date == today))
            await db.commit()
