import os
import pytest
import tempfile
import fitz  # PyMuPDF
import docx
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
def sample_pdf_path():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        path = tmp.name
    
    doc = fitz.open()
    # Page 1
    page1 = doc.new_page()
    page1.insert_text((50, 50), "AttendAI Remote Work Policy Document 2026.")
    page1.insert_text((50, 80), "Employees may request up to two remote days per week with manager pre-approval.")
    # Page 2
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Core working hours for remote staff are 10:00 AM to 4:00 PM EST.")
    page2.insert_text((50, 80), "Daily standup attendance is mandatory regardless of work location.")
    doc.save(path)
    doc.close()
    
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def sample_docx_path():
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        path = tmp.name
    
    doc = docx.Document()
    doc.add_heading("AttendAI Code of Conduct and Anti-Harassment", 0)
    p1 = doc.add_paragraph("AttendAI is committed to providing a safe and respectful work environment for all personnel.")
    p2 = doc.add_paragraph("Workplace bullying, harassment, and discrimination of any kind are strictly prohibited and subject to termination.")
    p3 = doc.add_paragraph("Reports can be filed anonymously with the HR Compliance Office via hr-compliance@attendai.com.")
    doc.save(path)
    
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.mark.asyncio
async def test_pdf_policy_upload_and_extraction(sample_pdf_path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Login as admin
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Upload PDF
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("Remote_Work_Policy.pdf", f, "application/pdf")}
            data = {"title": "Remote Work Guidelines 2026", "category": "Remote Work"}
            upload_res = await ac.post("/api/v1/policies/upload", headers=headers, data=data, files=files)

        assert upload_res.status_code == 201
        upload_data = upload_res.json()
        assert upload_data["title"] == "Remote Work Guidelines 2026"
        assert upload_data["chunk_count"] == 2  # 2 pages extracted

        # 3. Search PDF policy
        search_res = await ac.get(
            "/api/v1/policies/search?query=standup",
            headers=headers
        )
        assert search_res.status_code == 200
        results = search_res.json()
        assert len(results) > 0
        found = any("Daily standup attendance is mandatory" in r["content"] for r in results)
        assert found
        assert "Page 2" in results[0]["citation"] or "Page 2" in results[-1]["citation"]

@pytest.mark.asyncio
async def test_docx_policy_upload_and_extraction(sample_docx_path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Upload DOCX
        with open(sample_docx_path, "rb") as f:
            files = {"file": ("Code_of_Conduct.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            data = {"title": "Workplace Code of Conduct", "category": "Compliance"}
            upload_res = await ac.post("/api/v1/policies/upload", headers=headers, data=data, files=files)

        assert upload_res.status_code == 201
        upload_data = upload_res.json()
        assert upload_data["title"] == "Workplace Code of Conduct"
        assert upload_data["chunk_count"] >= 1

        # Search DOCX policy
        search_res = await ac.get(
            "/api/v1/policies/search?query=bullying",
            headers=headers
        )
        assert search_res.status_code == 200
        results = search_res.json()
        assert len(results) > 0
        assert any("Workplace bullying" in r["content"] for r in results)

@pytest.mark.asyncio
async def test_policy_upload_disallows_executable_files():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@attendai.com",
            "password": "Admin@123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
        files = {"file": ("malicious.exe", fake_exe, "application/x-msdownload")}
        data = {"title": "Exploit File", "category": "Malware"}
        upload_res = await ac.post("/api/v1/policies/upload", headers=headers, data=data, files=files)

        assert upload_res.status_code in [400, 422]
        assert "Unsupported file type" in upload_res.json()["detail"]
