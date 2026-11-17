import pytest
import io
import openpyxl
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_exports_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login Admin
        admin_res = await ac.post("/api/v1/auth/login", json={"email": "admin@attendai.com", "password": "Admin@123"})
        assert admin_res.status_code == 200
        admin_token = admin_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Login Employee
        emp_res = await ac.post("/api/v1/auth/login", json={"email": "employee@attendai.com", "password": "Employee@123"})
        assert emp_res.status_code == 200
        emp_token = emp_res.json()["access_token"]
        emp_headers = {"Authorization": f"Bearer {emp_token}"}

        # 3. Test CSV with Header Auth
        csv_res = await ac.get("/api/v1/exports/attendance/csv", headers=admin_headers)
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        assert "attachment; filename=" in csv_res.headers["content-disposition"]
        assert "Date,Employee Code,Employee Name" in csv_res.text
        lines = csv_res.text.strip().split("\n")
        assert len(lines) > 1

        # 4. Test XLSX with Header Auth
        xlsx_res = await ac.get("/api/v1/exports/attendance/xlsx", headers=admin_headers)
        assert xlsx_res.status_code == 200
        assert "application/vnd.openxmlformats" in xlsx_res.headers["content-type"]
        assert "attachment; filename=" in xlsx_res.headers["content-disposition"]
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_res.content))
        ws = wb.active
        assert ws.title == "Attendance Records"
        assert ws.max_row > 1

        # 5. Test Query Parameter Token Fallback
        query_csv_res = await ac.get(f"/api/v1/exports/attendance/csv?token={admin_token}")
        assert query_csv_res.status_code == 200
        assert "Date,Employee Code,Employee Name" in query_csv_res.text

        # 6. Test Employee Scoped Export (Personal Records)
        emp_csv_res = await ac.get("/api/v1/exports/attendance/csv", headers=emp_headers)
        assert emp_csv_res.status_code == 200
        assert "my_attendance" in emp_csv_res.headers["content-disposition"]

        emp_xlsx_res = await ac.get("/api/v1/exports/attendance/xlsx", headers=emp_headers)
        assert emp_xlsx_res.status_code == 200
        assert "my_attendance" in emp_xlsx_res.headers["content-disposition"]

        # 7. Test Anonymous Unauthorized
        anon_res = await ac.get("/api/v1/exports/attendance/csv")
        assert anon_res.status_code == 401
