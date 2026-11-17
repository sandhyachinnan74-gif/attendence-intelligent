import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_sessionmaker, init_db
from app.core.security import create_access_token
from app.models.models import User, Employee, Department, Shift

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def admin_token():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        from sqlalchemy import select
        user = (await db.execute(select(User).where(User.role == "admin"))).scalars().first()
        assert user is not None
        return create_access_token(data={"sub": user.id, "email": user.email, "role": user.role, "org_id": user.organization_id})

@pytest.fixture
async def hr_token():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        from sqlalchemy import select
        user = (await db.execute(select(User).where(User.role == "hr_manager"))).scalars().first()
        assert user is not None
        return create_access_token(data={"sub": user.id, "email": user.email, "role": user.role, "org_id": user.organization_id})

@pytest.fixture
async def employee_token():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        from sqlalchemy import select
        user = (await db.execute(select(User).where(User.role == "employee"))).scalars().first()
        assert user is not None
        return create_access_token(data={"sub": user.id, "email": user.email, "role": user.role, "org_id": user.organization_id})

@pytest.mark.asyncio
async def test_notifications_lifecycle(client, employee_token):
    headers = {"Authorization": f"Bearer {employee_token}"}
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        from sqlalchemy import select
        from app.services.notification_service import NotificationService
        user = (await db.execute(select(User).where(User.role == "employee"))).scalars().first()
        await NotificationService.create_notification(
            db=db,
            organization_id=user.organization_id,
            user_id=user.id,
            category="attendance",
            title="Punctuality Notice",
            message="Test notice for lifecycle verification."
        )

    # 1. List notifications (seeds default if empty)
    res = await client.get("/api/v1/notifications", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["total"] >= 1
    assert "unread_count" in data

    first_notif = data["items"][0]
    notif_id = first_notif["id"]

    # 2. Get unread count
    count_res = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 1

    # 3. Mark single as read
    read_res = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["success"] is True

    # 4. Mark all as read
    read_all_res = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert read_all_res.status_code == 200
    assert read_all_res.json()["success"] is True

    # Verify unread count is now 0
    count_res2 = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res2.json()["unread_count"] == 0

    # 5. Archive notification
    arch_res = await client.patch(f"/api/v1/notifications/{notif_id}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["success"] is True

@pytest.mark.asyncio
async def test_global_search_role_scoping(client, admin_token, employee_token):
    # Admin Search
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_search = await client.get("/api/v1/search?q=Engineering", headers=admin_headers)
    assert admin_search.status_code == 200
    admin_data = admin_search.json()
    assert admin_data["total_results"] >= 1
    assert len(admin_data["departments"]) >= 1

    # Employee Search - Cannot see organization-wide employees or anomalies
    emp_headers = {"Authorization": f"Bearer {employee_token}"}
    emp_search = await client.get("/api/v1/search?q=Engineering", headers=emp_headers)
    assert emp_search.status_code == 200
    emp_data = emp_search.json()
    # Employee cannot see anomalies
    assert len(emp_data["anomalies"]) == 0
    # Employee cannot see other employees
    assert len(emp_data["employees"]) <= 1

@pytest.mark.asyncio
async def test_employee_dashboard_endpoint(client, employee_token):
    headers = {"Authorization": f"Bearer {employee_token}"}
    res = await client.get("/api/v1/analytics/employee-dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "today_status" in data["kpis"]
    assert "hours_worked_today" in data["kpis"]
    assert "monthly_working_hours" in data["kpis"]
    assert "monthly_overtime" in data["kpis"]
    assert "available_leave_balance" in data["kpis"]
    assert "assigned_shift" in data
    assert "recent_punches" in data
    assert "leave_summary" in data
    assert "attendance_trends" in data
    assert "company_announcements" in data

@pytest.mark.asyncio
async def test_admin_system_diagnostics_rbca(client, admin_token, hr_token, employee_token):
    # Admin is allowed 200 OK
    admin_res = await client.get("/api/v1/system/diagnostics", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    diag = admin_res.json()
    assert "llm_diagnostics" in diag
    assert "database_diagnostics" in diag
    assert "redis_diagnostics" in diag
    assert "worker_diagnostics" in diag
    assert "infrastructure" in diag

    # HR Manager is FORBIDDEN (403)
    hr_res = await client.get("/api/v1/system/diagnostics", headers={"Authorization": f"Bearer {hr_token}"})
    assert hr_res.status_code == 403

    # Employee is FORBIDDEN (403)
    emp_res = await client.get("/api/v1/system/diagnostics", headers={"Authorization": f"Bearer {employee_token}"})
    assert emp_res.status_code == 403

@pytest.mark.asyncio
async def test_public_health_does_not_leak_llm_provider(client):
    res = await client.get("/api/v1/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    # LLM provider is not leaked in public health check
    assert "llm_provider" not in data
