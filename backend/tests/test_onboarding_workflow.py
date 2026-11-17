import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.models import Employee, User, EmployeeOnboardingRequest
from app.core.database import get_sessionmaker
from app.core.security import create_access_token
from sqlalchemy import select

@pytest.mark.asyncio
async def test_hr_onboarding_request_and_admin_approval():
    sm = get_sessionmaker()
    async with sm() as db:
        hr_user = (await db.execute(select(User).where(User.role == "hr_manager"))).scalars().first()
        admin_user = (await db.execute(select(User).where(User.role == "admin"))).scalars().first()
        assert hr_user is not None
        assert admin_user is not None

        hr_token = create_access_token(data={"sub": hr_user.id, "email": hr_user.email, "role": hr_user.role, "org_id": hr_user.organization_id})
        admin_token = create_access_token(data={"sub": admin_user.id, "email": admin_user.email, "role": admin_user.role, "org_id": admin_user.organization_id})

    hr_headers = {"Authorization": f"Bearer {hr_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. HR creates onboarding request
        unique_code = "EMP-TEST-99"
        unique_email = "test.candidate99@attendai.com"
        create_res = await ac.post(
            "/api/v1/employees/request",
            json={
                "first_name": "Test",
                "last_name": "Candidate",
                "email": unique_email,
                "employee_code": unique_code,
                "designation": "QA Engineer",
                "phone": "+1-555-0199",
                "role": "employee"
            },
            headers=hr_headers
        )
        assert create_res.status_code == 201, create_res.text
        req_data = create_res.json()
        request_id = req_data["id"]
        assert req_data["status"] == "pending_approval"
        assert req_data["employee_code"] == unique_code

        # 2. List onboarding requests as Admin
        list_res = await ac.get("/api/v1/employees/onboarding-requests", headers=admin_headers)
        assert list_res.status_code == 200
        items = list_res.json()
        assert any(item["id"] == request_id and item["status"] == "pending_approval" for item in items)

        # 3. Admin reviews and approves the request
        review_res = await ac.post(
            f"/api/v1/employees/onboarding-requests/{request_id}/review",
            json={"status": "approved"},
            headers=admin_headers
        )
        assert review_res.status_code == 200, review_res.text
        assert review_res.json()["status"] == "approved"

        # 4. Verify employee was created in database
        async with sm() as db:
            emp = (await db.execute(select(Employee).where(Employee.employee_code == unique_code))).scalars().first()
            assert emp is not None
            assert emp.email == unique_email
            assert emp.is_active is True

            user_obj = (await db.execute(select(User).where(User.email == unique_email))).scalars().first()
            assert user_obj is not None
            assert user_obj.role == "employee"
