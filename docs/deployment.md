# AttendAI — Deployment & Infrastructure Guide

This guide details how to build, deploy, and scale AttendAI locally and in production.

---

## 1. Local Development (Zero Friction Mode)

AttendAI can run completely locally on Windows/Linux/macOS without requiring live Docker daemon or external cloud API keys:

1. **Activate Python Virtual Environment**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. **Start Backend Server**:
   ```powershell
   $env:PYTHONPATH="backend"
   .\.venv\Scripts\uvicorn app.main:app --reload --port 8000
   ```
3. **Start Frontend Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```
4. Access the web interface at `http://localhost:3000` or `http://localhost:5173`.
5. Access interactive Swagger API documentation at `http://localhost:8000/docs`.

---

## 2. Docker Compose Deployment (Multi-Replica Load Balanced)

When Docker is running, the full production stack can be started with a single command:

```bash
docker compose up --build -d
```

### Stack Architecture:
- `attendai-loadbalancer`: Nginx proxying port 80 to frontend and least-connection load balancing to backend replicas.
- `attendai-backend-1` & `attendai-backend-2`: Stateless FastAPI replicas running Python 3.12 under non-root user `attendai`.
- `attendai-frontend`: Nginx container serving compiled React SPA.
- `attendai-postgres`: PostgreSQL 16 Alpine primary database.
- `attendai-redis`: Redis 7 Alpine cache and job queue.

### Scaling Horizontally:
To scale backend instances further:
```bash
docker compose up -d --scale backend_1=3
```
Update `nginx/nginx.conf` upstream block to include the new replica endpoints.
