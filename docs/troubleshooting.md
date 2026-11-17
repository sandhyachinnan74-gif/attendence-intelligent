# AttendAI — Comprehensive Troubleshooting & Diagnostics Guide

This guide provides targeted diagnostics and verified solutions for common operational issues across the AttendAI stack.

---

## 1. Port Conflicts & Process Management

### 1.1 Port 8000 (Backend) Already in Use

#### Symptom:
`ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): only one usage of each socket address is normally permitted`

#### Resolution:

**Windows PowerShell**:
```powershell
# Identify process using port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# Terminate the process by PID
Stop-Process -Id <PID> -Force
```

**Linux / macOS**:
```bash
# Identify and terminate process using port 8000
lsof -ti:8000 | xargs kill -9
```

---

### 1.2 Port 3000 (Frontend) Already in Use

#### Symptom:
Vite displays `Port 3000 is in use, trying another one...` and serves on 3001, causing CORS or proxy mismatches.

#### Resolution:

**Windows PowerShell**:
```powershell
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
Stop-Process -Id <PID> -Force
```

**Linux / macOS**:
```bash
lsof -ti:3000 | xargs kill -9
```

---

## 2. Backend Startup & Dependency Issues

### 2.1 `ModuleNotFoundError: No module named 'fastapi'` (or similar)

#### Cause:
The command was executed using global system Python instead of the virtual environment.

#### Resolution:
Always prefix commands with the virtual environment interpreter:

**Windows PowerShell**:
```powershell
.\venv\Scripts\Activate.ps1
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Linux / macOS**:
```bash
source venv/bin/activate
./venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

### 2.2 `MissingGreenlet: greenlet_spawn has not been called`

#### Cause:
An asynchronous SQLAlchemy model relationship was accessed synchronously outside an eager load (e.g. `user.employee.first_name`).

#### Resolution:
Ensure relationships accessed inside export generators or endpoints are either eagerly loaded (`selectinload(User.employee)`), or that fields are read from explicitly provided dependency parameters (e.g. `current_employee` from FastAPI dependency injection).

---

## 3. Database Connection & Migration Errors

### 3.1 `asyncpg.exceptions.ConnectionRejectionError: connection refused`

#### Cause:
The PostgreSQL container or service is not running on `localhost:5432`.

#### Resolution:
1. If using Docker, ensure the PostgreSQL service is active:
   ```bash
   docker-compose up -d postgres
   ```
2. If running locally without PostgreSQL, enable the automatic SQLite fallback in `.env`:
   ```ini
   USE_SQLITE_FALLBACK=true
   SQLITE_DATABASE_URL=sqlite+aiosqlite:///./attendai.db
   ```
   Restart the backend to automatically create and bind `attendai.db`.

---

### 3.2 `alembic.util.exc.CommandError: Target database is not up to date`

#### Cause:
Schema revisions in the migration directory conflict with the current database head.

#### Resolution:
```bash
# Apply pending migrations
alembic upgrade head

# If in development with SQLite, delete attendai.db and re-run seed.py to reset cleanly:
python sample_data/seed.py
```

---

## 4. Redis Connection & Session Issues

### 4.1 `ConnectionRefusedError: [Errno 111] Connection refused (redis://localhost:6379)`

#### Cause:
Local Redis server is not running on port 6379.

#### Resolution:
AttendAI includes a zero-dependency in-memory FakeRedis fallback. Ensure this is enabled in `.env`:
```ini
USE_FAKEREDIS_FALLBACK=true
```
The backend will log `[WARNING] Redis connection failed; falling back to FakeRedis` and continue running without interruption.

---

## 5. AI Provider & Cloud LLM Errors

### 5.1 `HTTP 401 Unauthorized` on NVIDIA NIM or GroqCloud

#### Cause:
The API key in `.env` is invalid, expired, or missing.

#### Resolution:
1. Open `.env` and verify your key starts with `nvapi-` (NVIDIA) or `gsk_` (Groq).
2. Check for accidental quotes or whitespace around the key.
3. Test connectivity directly:
   ```bash
   python backend/tests/verify_live_llm.py
   ```
4. If you do not have cloud API keys, switch to offline mock mode:
   ```ini
   LLM_PROVIDER=mock
   ```

---

### 5.2 `HTTP 429 Too Many Requests` (Rate Limit)

#### Cause:
You have exceeded the rate limit or quota on NVIDIA NIM or GroqCloud free tiers.

#### Behavior in AttendAI:
The `AIOrchestrator` catches HTTP 429 automatically and initiates failover:
`NVIDIA NIM -> GroqCloud -> Gemini -> Mock Engine`.
Groq provider also applies an exponential backoff with jitter before failing over.

---

## 6. Document Reading & Download Issues

### 6.1 `HTTP 500` or Blank Modal on Reading Policy Documents

#### Cause:
The physical file on disk was missing or the extracted chunk indices in the database were out of range.

#### Resolution:
1. Check that the `./uploads` directory exists.
2. In `backend/app/services/policy_service.py`, ensure chunk indexing handles zero-based vs one-based indices gracefully.
3. Re-seed demo policy PDF documents:
   ```bash
   python sample_data/seed.py
   ```

---

### 6.2 Browser Download Fails or Downloads Corrupted File

#### Cause:
1. Frontend revoked the Object URL before the browser completed the download stream.
2. The download URL was missing the `/api/v1` prefix.

#### Resolution:
In `frontend/src/utils/download.ts`, ensure downloads trigger via a detached DOM link and defer `URL.revokeObjectURL(blobUrl)` with a `setTimeout(..., 1000)`:
```typescript
const blobUrl = window.URL.createObjectURL(blob);
const link = document.createElement('a');
link.href = blobUrl;
link.download = filename;
document.body.appendChild(link);
link.click();
document.body.removeChild(link);
setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1000);
```

---

## 7. Custom Report & Excel Export Issues

### 7.1 Excel File Fails to Open in Microsoft Excel (`Corrupt Workbook`)

#### Cause:
OpenPyXL chart references (`PieChart` or `BarChart`) pointed to invalid row boundaries or non-numeric categories.

#### Resolution:
In `backend/app/exports/generators/excel_generator.py`, ensure chart data references strictly match non-empty rows:
```python
b_data = Reference(ws_dept, min_col=7, min_row=4, max_row=d_row_idx-1)
b_cats = Reference(ws_dept, min_col=1, min_row=5, max_row=d_row_idx-1)
```

---

## 8. Docker Compose Troubleshooting

### 8.1 Containers Continuously Restarting

#### Diagnosis:
```bash
docker-compose logs backend_1 --tail=50
```

#### Common Causes & Fixes:
1. **PostgreSQL container not healthy**: Run `docker-compose ps` to ensure `postgres` status is `healthy`. If unhealthy, check disk space on host machine.
2. **Environment variable syntax**: Ensure no trailing comments exist in `.env.production`.
