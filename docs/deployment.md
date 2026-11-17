# AttendAI — Production Deployment & Infrastructure Guide

> 🚀 **Live Production Deployment:** [https://attend-ai-yne6.onrender.com](https://attend-ai-yne6.onrender.com)

This document describes the production deployment topology, Docker containerization, Nginx load balancing, and operational disaster recovery procedures for AttendAI.

---

## 1. Production Topology & Architecture

In production, AttendAI runs as a containerized microservice cluster behind an Nginx reverse proxy that distributes traffic across two stateless FastAPI application replicas:

```mermaid
flowchart TD
    Client["Inbound Client Traffic (Internet / Corporate LAN)"] --> Nginx["Nginx Reverse Proxy & Load Balancer (Ports 80 & 443)"]
    
    subgraph ContainerNetwork["AttendAI Docker Bridge Network"]
        Nginx -->|"API Proxy /api/*"| BackendServices["FastAPI Application Cluster"]
        Nginx -->|"SPA Root /"| Front["Frontend Container (Nginx Static SPA)"]
        
        BackendServices <--> Postgres[("PostgreSQL 16 Alpine Database")]
        BackendServices <--> Redis[("Redis 7 Alpine Cache")]
    end
```

---

## 2. Docker Compose Configuration

The deployment is orchestrated using `docker-compose.yml` in the root repository.

### Key Service Definitions

1. **`postgres`**:
   - Image: `postgres:16-alpine`
   - Volume: `postgres_data:/var/lib/postgresql/data` (persistent database storage).
   - Healthcheck: `pg_isready -U attendai -d attendai` every 5 seconds.
2. **`redis`**:
   - Image: `redis:7-alpine`
   - Volume: `redis_data:/data` (persistent cache and session tokens).
   - Healthcheck: `redis-cli ping` every 5 seconds.
3. **`backend_1` & `backend_2`**:
   - Built from `./backend/Dockerfile`.
   - Run asynchronous Uvicorn workers.
   - Depends on `postgres` and `redis` being healthy.
   - Environment: `USE_SQLITE_FALLBACK=false`, `USE_FAKEREDIS_FALLBACK=false`.
4. **`frontend`**:
   - Built from `./frontend/Dockerfile` (multi-stage build compiling TypeScript/Vite into optimized static assets served via lightweight Nginx).
5. **`nginx`**:
   - Reverse proxy listening on ports `80` and `8000`.
   - Mounts `./nginx/nginx.conf` in read-only mode.

### Production Environment File (`.env.production`)
Create a production environment file:
```ini
APP_ENV=production
SECRET_KEY=generate_a_cryptographically_secure_random_64_character_string
JWT_SECRET_KEY=generate_another_cryptographically_secure_random_64_character_string

# Production Database (Internal Docker network hostname)
DATABASE_URL=postgresql+asyncpg://attendai:SecureProdPassword123@postgres:5432/attendai
USE_SQLITE_FALLBACK=false

# Production Redis (Internal Docker network hostname)
REDIS_URL=redis://redis:6379/0
USE_FAKEREDIS_FALLBACK=false

# AI Providers
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your_production_nvidia_key
GROQ_API_KEY=gsk_your_production_groq_key

LOG_LEVEL=WARNING
```

---

## 3. Nginx Reverse Proxy & Load Balancing Configuration

The file `nginx/nginx.conf` configures upstream balancing and proxy optimization:

```nginx
# Upstream cluster utilizing least_conn algorithm
upstream backend_cluster {
    least_conn;
    server backend_1:8000 max_fails=3 fail_timeout=10s;
    server backend_2:8000 max_fails=3 fail_timeout=10s;
    keepalive 32;
}

server {
    listen 80;
    server_name attendai.yourcompany.com;
    client_max_body_size 25M;

    # Load Balancer Health Probe
    location /lb-health {
        access_log off;
        return 200 'OK';
        add_header Content-Type text/plain;
    }

    # API Reverse Proxy with Buffering
    location /api/ {
        proxy_pass http://backend_cluster;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
    }

    # Frontend Single-Page Application
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 4. Launching the Production Cluster

Deploy the stack using Docker Compose:

```bash
# 1. Build images and start all containers in detached mode
docker-compose up -d --build

# 2. Verify all 5 containers are running and healthy
docker-compose ps

# 3. Apply database migrations inside backend container
docker-compose exec backend_1 alembic upgrade head

# 4. (Optional) Seed demonstration data
docker-compose exec backend_1 python sample_data/seed.py

# 5. Tail live logs across the cluster
docker-compose logs -f --tail=50
```

---

## 5. Backup & Disaster Recovery Procedures

### 5.1 Database Backups (`pg_dump`)
Execute automated daily snapshots of the PostgreSQL database:

```bash
# Create timestamped database backup
docker exec -t attendai-postgres pg_dump -U attendai -d attendai -F c -b -v -f /var/lib/postgresql/data/backup_$(date +%Y%m%d_%H%M%S).dump

# Copy backup archive to host or offsite storage
docker cp attendai-postgres:/var/lib/postgresql/data/backup_*.dump /opt/backups/attendai/
```

### 5.2 Database Restoration (`pg_restore`)
In the event of database failure or migration rollback:

```bash
# 1. Stop backend containers to terminate active connections
docker-compose stop backend_1 backend_2

# 2. Restore database from archive
docker exec -i attendai-postgres pg_restore -U attendai -d attendai --clean --if-exists -v /var/lib/postgresql/data/backup_target.dump

# 3. Restart backend cluster
docker-compose start backend_1 backend_2
```

---

## 6. Resource Limits & Health Monitoring

### 6.1 Recommended Production Sizing
- **Backend Nodes**: 2 vCPU, 4 GB RAM per FastAPI container.
- **PostgreSQL**: 2 vCPU, 8 GB RAM, SSD with IOPS &ge; 3,000.
- **Redis**: 1 vCPU, 2 GB RAM.
- **Reverse Proxy**: 1 vCPU, 1 GB RAM.

### 6.2 Health Probes
- **Infrastructure Health**: `GET /lb-health` (Nginx status, returns 200 OK).
- **Backend Health**: `GET /api/v1/system/health` (Checks DB connection, Redis connection, and reports latency in ms).
- **Kube / Docker Readiness**: `GET /api/v1/system/readiness`.
- **Kube / Docker Liveness**: `GET /api/v1/system/liveness`.
