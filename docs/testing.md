# AttendAI — Testing Strategy & Verification Report

AttendAI enforces strict automated quality assurance across unit, integration, security, and end-to-end layers.

---

## 1. Test Suite Summary

| Test File | Layer | Scope | Status |
|---|---|---|---|
| `backend/tests/test_attendance.py` | Unit | Clock-in, clock-out, worked minutes, overtime, grace period, late arrival, half-day calculation | PASSED (4/4) |
| `backend/tests/test_anomalies.py` | Unit / ML | Rule-based anomaly triggers, Isolation Forest model training and prediction | PASSED (4/4) |
| `backend/tests/test_harness.py` | Unit / Security | Prompt injection detection, JWT token redaction, RBAC tool permissions, Mock LLM provider | PASSED (4/4) |
| `backend/tests/test_api.py` | Integration | System health, Admin login, Employee login, invalid auth, Dashboard analytics, RBAC boundary, AI chat | PASSED (7/7) |
| `backend/tests/test_e2e_workflows.py` | End-to-End | 15-step complete journey: Admin setup &rarr; Shift assignment &rarr; Employee punch &rarr; Break &rarr; HR review &rarr; Anomaly triage &rarr; Policy search &rarr; AI chat &rarr; CSV/XLSX export &rarr; RBAC check | PASSED (1/1) |
| `frontend/tests/login.test.tsx` | Frontend Unit | Branding display, input handling, quick demo account selector buttons | PASSED (3/3) |

---

## 2. Executing Automated Tests

### Backend Test Suite (Pytest)
```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest backend\tests -v
```

### Frontend Test Suite (Vitest)
```bash
cd frontend
npm test
```

### Frontend Production Build (Typecheck + Vite)
```bash
cd frontend
npm run build
```

### Load Testing (Locust)
```powershell
.\.venv\Scripts\locust -f tests\locustfile.py --host=http://localhost:8000
```
Open `http://localhost:8089` in browser to simulate 50–500 concurrent workforce users.
