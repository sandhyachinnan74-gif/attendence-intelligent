import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_system_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data

@pytest.mark.asyncio
async def test_auth_login_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["role"] == "admin"

@pytest.mark.asyncio
async def test_auth_login_employee():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": "employee@attendai.com",
            "password": "Employee@123"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "employee"
    assert data["user"]["employee_code"] == "EMP001"

@pytest.mark.asyncio
async def test_auth_invalid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "WrongPassword!"
        })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_dashboard_analytics_authenticated():
    # Login as admin
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
        token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        res = await ac.get("/api/v1/analytics/dashboard", headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert data["kpis"]["total_employees"] >= 200
    assert "trends" in data
    assert "department_stats" in data
    assert "ai_insights" in data

@pytest.mark.asyncio
async def test_employee_cross_access_permission():
    # Login as employee
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "employee@attendai.com",
            "password": "Employee@123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Employee trying to view all anomalies should be forbidden
        res = await ac.get("/api/v1/anomalies", headers=headers)
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_ai_chat_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        chat_res = await ac.post(
            "/api/v1/ai/chat",
            json={"content": "Show recent late arrivals"},
            headers=headers
        )
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "conversation_id" in data
    assert "message" in data
    assert data["message"]["role"] == "assistant"
