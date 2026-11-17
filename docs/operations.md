# AttendAI — Operations & Runbook Guide

---

## 1. System Monitoring & Health Checks
- **Health Endpoint**: `GET /api/v1/system/health`
  - Validates PostgreSQL database read connectivity
  - Validates Redis ping
  - Measures server-side response latency (ms)
  - Reports active LLM provider
- **Readiness Probe**: `GET /api/v1/system/readiness` (returns HTTP 200 when ready to accept traffic)
- **Liveness Probe**: `GET /api/v1/system/liveness` (returns HTTP 200 when process is alive)

---

## 2. Common Operational Runbooks

### Runbook 1: Re-seeding Demo Workforce Data
```powershell
.\.venv\Scripts\python sample_data\seed.py
```
Inserts 200 employees, 6 departments, 4 shifts, 60 days of attendance history, 40 anomalies, and 2 sample policies.

### Runbook 2: Manual Anomaly Detection Run
Trigger the pipeline manually across recent records:
```bash
curl -X POST http://localhost:8000/api/v1/anomalies/detect -H "Authorization: Bearer <token>"
```

### Runbook 3: Inspecting Application Logs
Structured JSON logs include request IDs and latency metrics:
```bash
# Docker logs
docker logs -f attendai-backend-1
```
