# AttendAI
### Intelligent Workforce. Smarter Decisions.

AttendAI is a production-grade, AI-powered workforce time-and-attendance management platform engineered with a Dayforce-inspired enterprise user experience.

---

## Key Capabilities

1. **Deterministic Attendance Engine**:
   - Server-timestamped clock-in and clock-out with grace period enforcement (15 mins default).
   - Dynamic break tracking (start/end breaks, duration calculation).
   - Automatic overtime calculation, late arrival detection, and half-day status classification.
   - Missing punch identification and audit-logged attendance correction history.

2. **Hybrid Anomaly Detection**:
   - **Deterministic Rules**: Repeated late arrivals (&ge;3 occurrences), excessive overtime (&gt;3 hours), abnormally long shifts (&gt;12 hours), extended breaks (&gt;2 hours), missing clock-outs.
   - **Machine Learning (Isolation Forest)**: Multivariate outlier detection trained on employee arrival deviations, departure deviations, and worked hours.

3. **Secure AI Execution Harness**:
   - Grounded conversational workforce intelligence backed strictly by authorized backend tools.
   - Zero direct SQL exposure; strictly parameterized queries.
   - Prompt injection defense, secret redaction, and record-level RBAC enforcement.
   - Multi-provider abstraction: NVIDIA NIM (Mistral Large 4), GroqCloud (Llama 3.3), Google Gemini, and deterministic local Mock Engine.

4. **Policy-Aware HR Document Retrieval**:
   - Upload and extract PDF, DOCX, and TXT policy files using PyMuPDF and python-docx.
   - Instant full-text chunk search with document title, section, and page citations.

5. **Dayforce-Inspired Enterprise UI**:
   - Light enterprise theme (`#F5F7FB` background, `#FFFFFF` cards, `#2563EB` primary accents).
   - Collapsible navigation sidebar, top navigation with search and notifications, responsive charts (Recharts), and custom error pages (404, 403, 500, 502, 503).

---

## Demo Accounts

The database comes pre-seeded with 200 employees, 6 departments, 4 shifts, 60 days of attendance history, 40 anomalies, and 2 policy documents.

| Role | Email | Password | Access Scope |
|---|---|---|---|
| **Administrator** | `admin@attendai.com` | `Admin@123` | Organization-level access, all AI tools, system diagnostics |
| **HR Manager** | `hrmanager@attendai.com` | `HRManager@123` | Workforce management, leave approvals, anomaly triage, reports |
| **Employee** | `employee@attendai.com` | `Employee@123` | Personal punch portal, worked hours, leave requests, policy search |

---

## Local Development & Startup

### 1. Backend Server
```powershell
# In project root:
$env:PYTHONPATH="backend"
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```
Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Development Server
```bash
cd frontend
npm run dev
```
Web Application: [http://localhost:3000](http://localhost:3000)

---

## Docker Compose (Production Load-Balanced Stack)

To run the complete multi-container stack with Nginx load balancing:
```bash
docker compose up --build -d
```
Stack includes:
- `attendai-loadbalancer`: Nginx reverse proxy on port 80.
- `attendai-backend-1` & `attendai-backend-2`: Dual FastAPI replicas with least-connection load balancing.
- `attendai-frontend`: Compiled React SPA container.
- `attendai-postgres`: PostgreSQL 16 Alpine.
- `attendai-redis`: Redis 7 Alpine.

---

## Automated Verification & Test Commands

### Backend Pytest Suite (Unit, Integration, Security, E2E)
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest backend\tests -v
```
*(All 20 tests pass)*

### Frontend Vitest Suite
```bash
cd frontend
npm test
```
*(All 3 tests pass)*

### Frontend Production Build Check
```bash
cd frontend
npm run build
```
*(TypeScript check & Vite build pass)*

---

## Local Development Guarantee

> [!IMPORTANT]
> **Strict Local Isolation**: This repository is strictly confined to the local machine. In accordance with Section 0.1 of the master prompt, no remote repository has been initialized, no code has been pushed to GitHub, GitLab, or Bitbucket, and no Docker images or credentials have been published externally.
