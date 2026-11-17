import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_full_e2e_workforce_journey():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Admin login
        admin_login = await client.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Department Creation
        dept_res = await client.post("/api/v1/departments", json={
            "name": "Quality Assurance",
            "code": "QA"
        }, headers=admin_headers)
        # 201 or 409 if already exists
        assert dept_res.status_code in [201, 409]

        # 3. Employee Creation
        emp_code = "EMP999"
        emp_res = await client.post("/api/v1/employees", json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user999@attendai.com",
            "employee_code": emp_code,
            "designation": "QA Analyst",
            "date_of_joining": "2026-01-01",
            "password": "Password@123"
        }, headers=admin_headers)
        assert emp_res.status_code in [201, 409]
        if emp_res.status_code == 201:
            emp_id = emp_res.json()["id"]
        else:
            # retrieve
            list_res = await client.get("/api/v1/employees", params={"search": emp_code}, headers=admin_headers)
            emp_id = list_res.json()[0]["id"]

        # 4. Shift Retrieval & Assignment
        shifts_res = await client.get("/api/v1/shifts", headers=admin_headers)
        assert shifts_res.status_code == 200
        shifts = shifts_res.json()
        assert len(shifts) > 0
        target_shift_id = shifts[0]["id"]

        assign_res = await client.post("/api/v1/shifts/assign", json={
            "employee_id": emp_id,
            "shift_id": target_shift_id,
            "effective_from": "2026-01-01"
        }, headers=admin_headers)
        assert assign_res.status_code == 201

        # 5. Employee Login
        emp_login = await client.post("/api/v1/auth/login", json={
            "email": "employee@attendai.com",
            "password": "Employee@123"
        })
        assert emp_login.status_code == 200
        emp_token = emp_login.json()["access_token"]
        emp_headers = {"Authorization": f"Bearer {emp_token}"}

        # 6. Employee Punch Clock-in
        # Might already be clocked in or can punch
        clock_in_res = await client.post("/api/v1/attendance/clock-in", json={}, headers=emp_headers)
        assert clock_in_res.status_code in [200, 409] # 409 if already punched today

        # 7. Break Toggle
        break_res = await client.post("/api/v1/attendance/break", json={"reason": "Coffee Break"}, headers=emp_headers)
        # May succeed or conflict if already clocked out
        assert break_res.status_code in [200, 409, 422]

        # 8. HR Review of Leave Applications
        hr_login = await client.post("/api/v1/auth/login", json={
            "email": "hrmanager@attendai.com",
            "password": "HRManager@123"
        })
        assert hr_login.status_code == 200
        hr_token = hr_login.json()["access_token"]
        hr_headers = {"Authorization": f"Bearer {hr_token}"}

        leave_list = await client.get("/api/v1/leave", headers=hr_headers)
        assert leave_list.status_code == 200
        leaves = leave_list.json()
        if len(leaves) > 0:
            target_leave = leaves[0]
            review_res = await client.put(f"/api/v1/leave/{target_leave['id']}/review", json={
                "status": "approved",
                "resolution_notes": "Verified by HR Director"
            }, headers=hr_headers)
            assert review_res.status_code == 200
            assert review_res.json()["status"] == "approved"

        # 9. Anomaly Detection Pipeline Trigger
        detect_res = await client.post("/api/v1/anomalies/detect", headers=hr_headers)
        assert detect_res.status_code == 200
        assert "anomalies_detected" in detect_res.json()

        # 10. Anomaly Resolution Workflow
        anom_list = await client.get("/api/v1/anomalies", headers=hr_headers)
        assert anom_list.status_code == 200
        anomalies = anom_list.json()
        if len(anomalies) > 0:
            target_anom = anomalies[0]
            res_review = await client.put(f"/api/v1/anomalies/{target_anom['id']}/review", json={
                "status": "resolved",
                "resolution_notes": "Supervisor reviewed punch log; time validated."
            }, headers=hr_headers)
            assert res_review.status_code == 200
            assert res_review.json()["status"] == "resolved"

        # 11. Policy Q&A / Full Text Search
        policy_search = await client.get("/api/v1/policies/search", params={"query": "grace period"}, headers=emp_headers)
        assert policy_search.status_code == 200
        chunks = policy_search.json()
        assert len(chunks) > 0
        assert "grace" in chunks[0]["content"].lower() or "period" in chunks[0]["content"].lower()

        # 12. Conversational Workforce AI Assistant
        chat_res = await client.post("/api/v1/ai/chat", json={
            "content": "What is our attendance policy on grace periods?"
        }, headers=emp_headers)
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert "message" in chat_data
        assert len(chat_data["message"]["content"]) > 0

        # 13. Reports and Exports
        csv_res = await client.get("/api/v1/exports/attendance/csv", headers=hr_headers)
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        assert "Employee Code" in csv_res.text

        xlsx_res = await client.get("/api/v1/exports/attendance/xlsx", headers=hr_headers)
        assert xlsx_res.status_code == 200
        assert len(xlsx_res.content) > 100

        # 14. RBAC Security Check: Employee cannot access organization anomalies
        unauth_anom = await client.get("/api/v1/anomalies", headers=emp_headers)
        assert unauth_anom.status_code == 403

        # 15. Invalid endpoint returns 404
        not_found_res = await client.get("/api/v1/unknown-resource-endpoint", headers=admin_headers)
        assert not_found_res.status_code == 404
