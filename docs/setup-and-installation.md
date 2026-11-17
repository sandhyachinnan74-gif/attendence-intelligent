# AttendAI — Complete Setup & Installation Guide

This guide provides end-to-end instructions for installing, configuring, and running AttendAI locally on **Windows PowerShell** and **Linux/macOS**.

---

## 1. System Prerequisites

Ensure the following tools are installed on your host machine:

| Component | Minimum Version | Verified Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | `3.11+` | `3.12.10` | FastAPI backend runtime, SQLAlchemy ORM, ML libraries |
| **Node.js** | `18.0+` | `22.x` / `20.x` | Vite build tool & React 18 runtime |
| **npm** | `9.0+` | `10.x` | Frontend package manager |
| **Git** | `2.30+` | `2.40+` | Version control |
| **Docker & Docker Compose** | Optional | `24+` | Containerized deployment (PostgreSQL, Redis, Nginx) |
| **PostgreSQL** | Optional | `16.x` | Production database (SQLite fallback supported locally) |
| **Redis** | Optional | `7.x` | Production cache & sessions (FakeRedis fallback supported) |

---

## 2. Quickstart with Docker Compose

If you have **Docker Desktop** installed and running, you can launch the complete AttendAI cluster (Nginx, 2 FastAPI replicas, Frontend, PostgreSQL, Redis) with a single command:

```bash
docker-compose up -d --build
```

- **Frontend Application**: `http://localhost:80` (or `http://localhost:3000` in dev)
- **API Endpoints**: `http://localhost:80/api/v1` (or `http://localhost:8000`)
- **API Swagger Documentation**: `http://localhost:8000/docs`
- **Load Balancer Health Check**: `http://localhost:80/lb-health`

---

## 3. Manual Local Installation (Without Docker)

### Step 1: Clone the Repository

#### Windows PowerShell:
```powershell
git clone https://github.com/shuvendu-kumar-mohapatra/attendai-intelligent-workforce.git
cd attendai-intelligent-workforce
```

#### Linux / macOS:
```bash
git clone https://github.com/shuvendu-kumar-mohapatra/attendai-intelligent-workforce.git
cd attendai-intelligent-workforce
```

---

### Step 2: Configure Environment Variables

Copy the example environment configuration:

#### Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

#### Linux / macOS:
```bash
cp .env.example .env
```

Open `.env` in your text editor and review the parameters:
```ini
APP_ENV=development
SECRET_KEY=attendai-super-secret-key-32chars-minimum-token
JWT_SECRET_KEY=attendai-jwt-secret-key-32chars-minimum-token

# Database Configuration (Uses SQLite fallback if PostgreSQL is not running)
DATABASE_URL=postgresql+asyncpg://attendai:password@localhost:5432/attendai
SQLITE_DATABASE_URL=sqlite+aiosqlite:///./attendai.db
USE_SQLITE_FALLBACK=true

# Redis Configuration (Uses FakeRedis fallback if Redis server is not running)
REDIS_URL=redis://localhost:6379/0
USE_FAKEREDIS_FALLBACK=true

# AI Provider Keys (Optional: Default 'mock' runs offline without keys)
LLM_PROVIDER=mock
NVIDIA_API_KEY=
GROQ_API_KEY=
```

---

### Step 3: Backend Python Environment Setup

Create and activate a virtual environment, then install dependencies:

#### Windows PowerShell:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### Step 4: Frontend Node Environment Setup

Install React, TypeScript, and Vite dependencies:

#### Windows PowerShell & Linux / macOS:
```bash
npm --prefix frontend install
```

---

### Step 5: Initialize Database & Seed Demonstration Data

Run the database seeder to create tables, default organizations, 6 departments, 4 shifts, and 200 demo employees with attendance and leave records:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\python.exe sample_data/seed.py
```

#### Linux / macOS:
```bash
PYTHONPATH=backend ./venv/bin/python sample_data/seed.py
```

**Output Confirmation**:
```
Initializing database schema...
Creating Organization...
Creating Departments...
Creating Shifts...
Creating Primary Demo Accounts (Admin, HR, Employee)...
Generating 198 additional workforce employees (Total 200)...
Seeding attendance history, anomalies, and leave records...
Database seeding completed successfully!
```

---

### Step 6: Start the Backend Server

Start the FastAPI application with Uvicorn on port `8000`:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Linux / macOS:
```bash
PYTHONPATH=backend ./venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify the backend is running by opening:
- `http://127.0.0.1:8000/api/v1/system/health` (should return status `"healthy"`)
- `http://127.0.0.1:8000/docs` (interactive Swagger UI)

---

### Step 7: Start the Frontend Development Server

In a new terminal window, launch the Vite dev server on port `3000`:

#### Windows PowerShell & Linux / macOS:
```bash
npm --prefix frontend run dev -- --port 3000 --host 127.0.0.1
```

Access the AttendAI web application at:
**`http://localhost:3000`** (or `http://127.0.0.1:3000`)

---

## 4. Default Demonstration Login Credentials

Use the following accounts to access each role's dedicated experience:

| Role | Email | Password | Primary Features |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@attendai.com` | `Admin@123` | Full org dashboard, employee directory, shift setup, diagnostics, audit logs, all reports |
| **HR Manager** | `hrmanager@attendai.com` | `HRManager@123` | Department workforce overview, employee onboarding submissions, leave/attendance reviews |
| **Employee** | `employee@attendai.com` | `Employee@123` | Personal clock-in/out, break tracker, schedule, leave application, personal policy search |

---

## 5. Verification Commands

Run the comprehensive automated test suite to verify full installation health:

```powershell
# Windows PowerShell
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest.exe backend/tests/ -v

# Linux / macOS
PYTHONPATH=backend ./venv/bin/pytest backend/tests/ -v
```

All **85 / 85 tests** should pass with 100% green status.
