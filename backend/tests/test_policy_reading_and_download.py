import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_policy_listing_all_roles():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Admin login
        admin_login = await ac.post("/api/v1/auth/login", json={"email": "admin@attendai.com", "password": "Admin@123"})
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        
        # Employee login
        emp_login = await ac.post("/api/v1/auth/login", json={"email": "employee@attendai.com", "password": "Employee@123"})
        assert emp_login.status_code == 200
        emp_token = emp_login.json()["access_token"]

        # List policies as admin
        res_admin = await ac.get("/api/v1/policies", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_admin.status_code == 200
        policies_admin = res_admin.json()
        assert len(policies_admin) >= 2

        # List policies as employee
        res_emp = await ac.get("/api/v1/policies", headers={"Authorization": f"Bearer {emp_token}"})
        assert res_emp.status_code == 200
        policies_emp = res_emp.json()
        assert len(policies_emp) == len(policies_admin)

@pytest.mark.asyncio
async def test_policy_detail_no_chunk_index_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        emp_login = await ac.post("/api/v1/auth/login", json={"email": "employee@attendai.com", "password": "Employee@123"})
        token = emp_login.json()["access_token"]

        # Get policy list
        res = await ac.get("/api/v1/policies", headers={"Authorization": f"Bearer {token}"})
        policies = res.json()
        assert len(policies) > 0

        # Fetch detail for each policy - ensure no 500 or chunk_index error!
        for pol in policies:
            detail_res = await ac.get(f"/api/v1/policies/{pol['id']}", headers={"Authorization": f"Bearer {token}"})
            assert detail_res.status_code == 200, f"Failed for policy {pol['id']}: {detail_res.text}"
            data = detail_res.json()
            assert data["id"] == pol["id"]
            assert "chunks" in data
            assert len(data["chunks"]) >= 0

@pytest.mark.asyncio
async def test_policy_content_structured_reader():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        emp_login = await ac.post("/api/v1/auth/login", json={"email": "employee@attendai.com", "password": "Employee@123"})
        token = emp_login.json()["access_token"]

        res = await ac.get("/api/v1/policies", headers={"Authorization": f"Bearer {token}"})
        policies = res.json()
        
        pdf_policy = next((p for p in policies if p["file_path"] and p["file_path"].endswith(".pdf")), policies[0])
        docx_policy = next((p for p in policies if p["file_path"] and p["file_path"].endswith(".docx")), None)

        # Test PDF Content
        res_pdf = await ac.get(f"/api/v1/policies/{pdf_policy['id']}/content", headers={"Authorization": f"Bearer {token}"})
        assert res_pdf.status_code == 200
        pdf_content = res_pdf.json()
        assert pdf_content["id"] == pdf_policy["id"]
        assert "elements" in pdf_content
        assert len(pdf_content["elements"]) > 0
        assert pdf_content["total_pages"] >= 1
        assert "download_url" in pdf_content
        assert "view_url" in pdf_content

        # Test DOCX Content (if available)
        if docx_policy:
            res_docx = await ac.get(f"/api/v1/policies/{docx_policy['id']}/content", headers={"Authorization": f"Bearer {token}"})
            assert res_docx.status_code == 200
            docx_content = res_docx.json()
            assert docx_content["format"] == "docx"
            assert len(docx_content["elements"]) > 0

@pytest.mark.asyncio
async def test_policy_download_and_view_with_headers_and_token_param():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        emp_login = await ac.post("/api/v1/auth/login", json={"email": "employee@attendai.com", "password": "Employee@123"})
        token = emp_login.json()["access_token"]

        res = await ac.get("/api/v1/policies", headers={"Authorization": f"Bearer {token}"})
        policies = res.json()
        test_policy = policies[0]

        # 1. Download via Bearer header
        dl_header = await ac.get(f"/api/v1/policies/{test_policy['id']}/download", headers={"Authorization": f"Bearer {token}"})
        assert dl_header.status_code == 200
        assert "attachment" in dl_header.headers.get("content-disposition", "")
        assert len(dl_header.content) > 0

        # 2. Download via ?token= query parameter (for direct browser clicks)
        dl_query = await ac.get(f"/api/v1/policies/{test_policy['id']}/download?token={token}")
        assert dl_query.status_code == 200
        assert "attachment" in dl_query.headers.get("content-disposition", "")
        assert len(dl_query.content) == len(dl_header.content)

        # 3. View inline via Bearer header
        view_header = await ac.get(f"/api/v1/policies/{test_policy['id']}/view", headers={"Authorization": f"Bearer {token}"})
        assert view_header.status_code == 200
        assert "inline" in view_header.headers.get("content-disposition", "")
        assert len(view_header.content) > 0

        # 4. View inline via ?token= query parameter (for iframe embeds)
        view_query = await ac.get(f"/api/v1/policies/{test_policy['id']}/view?token={token}")
        assert view_query.status_code == 200
        assert "inline" in view_query.headers.get("content-disposition", "")
        assert len(view_query.content) == len(view_header.content)

@pytest.mark.asyncio
async def test_policy_search_citations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        emp_login = await ac.post("/api/v1/auth/login", json={"email": "employee@attendai.com", "password": "Employee@123"})
        token = emp_login.json()["access_token"]

        search_res = await ac.get("/api/v1/policies/search?query=leave", headers={"Authorization": f"Bearer {token}"})
        assert search_res.status_code == 200
        results = search_res.json()
        assert len(results) > 0
        assert "citation" in results[0]
        assert "content" in results[0]
