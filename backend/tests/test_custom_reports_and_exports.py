import io
import pytest
import openpyxl
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_sessionmaker
from app.core.security import create_access_token
from app.models.models import User, Employee
from sqlalchemy import select

@pytest.fixture
async def tokens():
    sm = get_sessionmaker()
    async with sm() as db:
        admin = (await db.execute(select(User).where(User.role == "admin"))).scalars().first()
        hr = (await db.execute(select(User).where(User.role == "hr_manager"))).scalars().first()
        emp_user = (await db.execute(select(User).where(User.role == "employee"))).scalars().first()
        emp = (await db.execute(select(Employee).where(Employee.user_id == emp_user.id))).scalars().first()

        admin_t = create_access_token(data={"sub": admin.id, "email": admin.email, "role": admin.role, "org_id": admin.organization_id})
        hr_t = create_access_token(data={"sub": hr.id, "email": hr.email, "role": hr.role, "org_id": hr.organization_id})
        emp_t = create_access_token(data={"sub": emp_user.id, "email": emp_user.email, "role": emp_user.role, "org_id": emp_user.organization_id})

        return {
            "admin": admin_t,
            "hr": hr_t,
            "employee": emp_t,
            "emp_id": emp.id
        }

@pytest.mark.asyncio
async def test_exports_config_role_scoping(tokens):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Admin Config
        res_admin = await ac.get("/api/v1/exports/config", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert res_admin.status_code == 200
        data_admin = res_admin.json()
        assert len(data_admin["report_types"]) >= 10
        assert len(data_admin["departments"]) > 0
        assert len(data_admin["employees"]) > 0

        # 2. Employee Config
        res_emp = await ac.get("/api/v1/exports/config", headers={"Authorization": f"Bearer {tokens['employee']}"})
        assert res_emp.status_code == 200
        data_emp = res_emp.json()
        assert all(t["id"].startswith("my_") for t in data_emp["report_types"])
        assert len(data_emp["departments"]) == 0  # Employees cannot select other departments
        assert len(data_emp["employees"]) == 0    # Employees cannot select other employees

@pytest.mark.asyncio
async def test_admin_generate_csv_xlsx_pdf(tokens):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {tokens['admin']}"}

        for fmt in ["csv", "xlsx", "pdf"]:
            # Preview
            prev_res = await ac.post("/api/v1/exports/preview", json={
                "report_type": "attendance_org",
                "scope_type": "organization",
                "date_preset": "last_30_days",
                "format": fmt
            }, headers=headers)
            assert prev_res.status_code == 200, prev_res.text
            prev_data = prev_res.json()
            assert prev_data["record_count"] >= 0

            # Generate
            gen_res = await ac.post("/api/v1/exports/generate", json={
                "report_type": "attendance_org",
                "scope_type": "organization",
                "date_preset": "last_30_days",
                "format": fmt
            }, headers=headers)
            assert gen_res.status_code == 200, gen_res.text
            gen_data = gen_res.json()
            assert gen_data["format"] == fmt
            assert gen_data["file_size_bytes"] > 0
            export_id = gen_data["export_id"]

            # Download
            dl_res = await ac.get(f"/api/v1/exports/{export_id}/download", headers=headers)
            assert dl_res.status_code == 200
            assert len(dl_res.content) == gen_data["file_size_bytes"]

            if fmt == "xlsx":
                wb = openpyxl.load_workbook(io.BytesIO(dl_res.content))
                assert "Report Summary" in wb.sheetnames
                assert "All Records" in wb.sheetnames
            elif fmt == "pdf":
                assert dl_res.content.startswith(b"%PDF")
            elif fmt == "csv":
                assert len(dl_res.text.strip().split("\n")) >= 1

@pytest.mark.asyncio
async def test_employee_personal_export_enforcement(tokens):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        emp_headers = {"Authorization": f"Bearer {tokens['employee']}"}
        admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}

        # 1. Employee generates personal report
        gen_res = await ac.post("/api/v1/exports/generate", json={
            "report_type": "my_attendance_monthly",
            "scope_type": "personal",
            "date_preset": "last_30_days",
            "format": "xlsx"
        }, headers=emp_headers)
        assert gen_res.status_code == 200
        emp_export_id = gen_res.json()["export_id"]

        # Employee downloads own report -> SUCCESS
        dl_res = await ac.get(f"/api/v1/exports/{emp_export_id}/download", headers=emp_headers)
        assert dl_res.status_code == 200

        # 2. Admin generates report
        admin_gen = await ac.post("/api/v1/exports/generate", json={
            "report_type": "complete_workforce",
            "scope_type": "organization",
            "date_preset": "this_month",
            "format": "csv"
        }, headers=admin_headers)
        assert admin_gen.status_code == 200
        admin_export_id = admin_gen.json()["export_id"]

        # Employee tries to download Admin's report -> FORBIDDEN (403)
        dl_forbidden = await ac.get(f"/api/v1/exports/{admin_export_id}/download", headers=emp_headers)
        assert dl_forbidden.status_code == 403

@pytest.mark.asyncio
async def test_export_history_role_isolation(tokens):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        emp_headers = {"Authorization": f"Bearer {tokens['employee']}"}
        admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}

        # Admin history contains all org exports
        admin_hist = await ac.get("/api/v1/exports/history", headers=admin_headers)
        assert admin_hist.status_code == 200
        assert len(admin_hist.json()) > 0

        # Employee history contains only their own exports
        emp_hist = await ac.get("/api/v1/exports/history", headers=emp_headers)
        assert emp_hist.status_code == 200
        for item in emp_hist.json():
            assert "my_" in item["report_type"] or item["scope_type"] == "personal"

@pytest.mark.asyncio
async def test_hr_manager_export_workflow(tokens):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        hr_headers = {"Authorization": f"Bearer {tokens['hr']}"}

        # 1. HR Config
        hr_cfg = await ac.get("/api/v1/exports/config", headers=hr_headers)
        assert hr_cfg.status_code == 200
        data = hr_cfg.json()
        assert len(data["report_types"]) >= 8

        # 2. HR Generate Department Report
        gen_res = await ac.post("/api/v1/exports/generate", json={
            "report_type": "department_report",
            "scope_type": "organization",
            "date_preset": "last_30_days",
            "format": "csv"
        }, headers=hr_headers)
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert "AttendAI_" in gen_data["report_name"] or gen_data["file_size_bytes"] > 0

        # 3. HR Download
        dl_res = await ac.get(f"/api/v1/exports/{gen_data['export_id']}/download", headers=hr_headers)
        assert dl_res.status_code == 200
        disposition = dl_res.headers.get("content-disposition", "")
        assert "AttendAI_" in disposition
        assert ".csv" in disposition

@pytest.mark.asyncio
async def test_today_attendance_records_exist():
    from datetime import date
    from app.models.models import AttendanceRecord
    sm = get_sessionmaker()
    async with sm() as db:
        today = date.today()
        recs = (await db.execute(select(AttendanceRecord).where(AttendanceRecord.date == today))).scalars().all()
        assert len(recs) > 50, f"Expected active attendance records for today, found {len(recs)}"


