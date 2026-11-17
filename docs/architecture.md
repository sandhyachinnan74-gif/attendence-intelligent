# AttendAI — System Architecture & Component Interaction

AttendAI is an enterprise workforce time-and-attendance management platform engineered with an asynchronous backend, a role-tailored React frontend, deterministic attendance rules, an Isolation Forest machine learning anomaly engine, and an AI execution harness backed by NVIDIA NIM and GroqCloud.

---

## 1. High-Level Architecture Overview

```mermaid
flowchart TD
    subgraph ClientLayer["Client & Presentation Tier"]
        Browser["Enterprise Browser Client\n(Chrome, Edge, Firefox, Safari)"]
        SPA["React 18 + Vite SPA\n(TypeScript, Tailwind CSS, Lucide)"]
        Browser --> SPA
    end

    subgraph GatewayLayer["Reverse Proxy & Load Balancer Tier"]
        Nginx["Nginx Reverse Proxy\n(Port 80 / 443)\nleast_conn load balancing"]
        SPA -->|Static Assets & HTTP API Requests| Nginx
    end

    subgraph ApplicationLayer["Application Services Tier"]
        Backend1["FastAPI Application Replica 1\n(Port 8000)"]
        Backend2["FastAPI Application Replica 2\n(Port 8000)"]
        Nginx -->|/api/v1/*| Backend1
        Nginx -->|/api/v1/*| Backend2
        
        Orchestrator["AI Execution Harness\n(AIOrchestrator)"]
        Backend1 --> Orchestrator
        Backend2 --> Orchestrator
        
        ExportGen["Export Generation Engine\n(OpenPyXL & CSV Streamer)"]
        Backend1 --> ExportGen
        Backend2 --> ExportGen
    end

    subgraph CachingLayer["State & Caching Tier"]
        Redis["Redis 7\n(Port 6379)\nSession Tokens, Rate Limiting & Cache\nFallback: FakeRedis"]
        Backend1 <--> Redis
        Backend2 <--> Redis
    end

    subgraph StorageLayer["Data & Persistence Tier"]
        DB[(PostgreSQL 16\nPrimary Async Engine\nFallback: SQLite + aiosqlite)]
        FileStore["Document & Export Storage\n(./uploads & ./exports)"]
        Backend1 <--> DB
        Backend2 <--> DB
        Backend1 <--> FileStore
        Backend2 <--> FileStore
    end

    subgraph ExternalAILayer["External AI & Cloud Inference Tier"]
        NvidiaNIM["Primary: NVIDIA NIM API\n(Mistral Large 4 1T A52B)"]
        GroqCloud["Secondary Fallback: GroqCloud API\n(OpenAI GPT-OSS-120B / Llama 3.3)"]
        GeminiCloud["Tertiary Fallback: Google Gemini API\n(Gemini 1.5 Pro)"]
        MockLLM["Local Fallback: Deterministic Mock Engine"]
        
        Orchestrator -->|1. Primary Attempt| NvidiaNIM
        Orchestrator -.->|2. On 4xx/5xx/Timeout| GroqCloud
        Orchestrator -.->|3. On Failover| GeminiCloud
        Orchestrator -.->|4. Offline Mode| MockLLM
    end
```

---

## 2. Frontend Architecture

The frontend is a single-page application (SPA) built on React 18, TypeScript, and Vite. It emphasizes a Dayforce-grade corporate user experience, responsive typography, and silent role-based access control.

```mermaid
flowchart TD
    subgraph UIStructure["Frontend Architecture"]
        Entry["main.tsx\n(ReactDOM.createRoot)"] --> App["app/App.tsx\n(BrowserRouter & Global Providers)"]
        
        App --> AuthCtx["context/AuthContext.tsx\n(JWT Lifecycle, User State & Role)"]
        App --> Layout["components/layout/AppLayout.tsx\n(Sidebar, TopNavbar, Main Content Area)"]
        
        Layout --> Guard["RoleGuard Component\n(Path Authorization & Redirection)"]
        
        Guard --> P_Admin["Admin Pages:\nDashboard, Employees, Departments,\nShifts, Anomalies, Policies,\nAnalytics, Diagnostics, AuditLogs"]
        Guard --> P_HR["HR Manager Pages:\nDashboard, Employees (Onboarding),\nDepartments, Shifts, Leave,\nAnomalies, Policies, Analytics"]
        Guard --> P_Emp["Employee Pages:\nDashboard (Personal Punch),\nAttendance, Schedule, Leave,\nPolicies, AI Assistant, Settings"]
        
        P_Admin & P_HR & P_Emp --> SharedComp["Shared Components:\nExportModal, NotificationCenter,\nGlobalSearch, DocumentViewerModal,\nConfirmationDialogs"]
        
        SharedComp --> APIClient["services/api.ts\n(Axios Client with Auto-Bearer & Refresh)"]
        APIClient --> BackendAPI["Backend HTTP API (/api/v1)"]
    end
```

### Key Frontend Components
- **`AuthContext.tsx`**: Manages user authentication state, access tokens, refresh token rotation, and decoded RBAC roles (`admin`, `hr_manager`, `employee`).
- **`AppLayout.tsx`**: Renders the persistent Dayforce-inspired navigation bar, unread notification bell popover, global search bar (`Cmd/Ctrl + K`), and role-scoped sidebar navigation.
- **`RoleGuard.tsx`**: Route protection wrapper that prevents unauthorized URL navigation by redirecting prohibited roles directly to `/403` (Forbidden).
- **`ExportModal.tsx`**: Multi-step report builder dialog (*"What would you like to download?"*) preventing immediate file downloads and allowing users to select report types, scope, date ranges, columns, and formats (CSV / XLSX).
- **`DocumentViewerModal.tsx`**: In-browser document viewer supporting native multi-page PDF rendering (page navigation, zoom) and structured DOCX rendering.

---

## 3. Backend Architecture

The backend is built with FastAPI (Python 3.12+), utilizing asynchronous request handling (`async`/`await`), dependency injection, and declarative Pydantic v2 schemas.

```mermaid
flowchart TD
    subgraph BackendPipeline["FastAPI Request Processing Pipeline"]
        Req["HTTP Request"] --> Mid1["Request-ID Middleware\n(X-Request-ID Header Assignment)"]
        Mid1 --> Mid2["Process-Time Middleware\n(X-Process-Time Header Calculation)"]
        Mid2 --> Mid3["CORS Middleware\n(Origin & Credential Validation)"]
        Mid3 --> Router["api/v1/api.py\n(APIRouter Aggregator)"]
        
        Router --> AuthDep["deps.py: get_current_user\n(JWT Signature & Expiry Verification)"]
        AuthDep --> RoleDep["deps.py: require_role\n(RBAC Enforcement)"]
        RoleDep --> EmpDep["deps.py: get_current_employee_profile\n(User -> Employee Association)"]
        
        EmpDep --> Endpoints["Endpoint Controller Function"]
        Endpoints --> Services["Domain Services\n(AttendanceService, AnomalyService,\nPolicyService, NotificationService)"]
        
        Services --> DBConn["Core Database Session\n(AsyncSession via get_db)"]
        Services --> CacheConn["Redis Cache\n(get_redis)"]
        
        Endpoints --> Resp["JSONResponse / FileResponse / StreamingResponse"]
    end
```

### Middleware Pipeline
1. **`logging_and_request_id_middleware`**: Injects a unique UUIDv4 into `request.state.request_id`, tracks total execution time in milliseconds, logs inbound requests, and attaches `X-Request-ID` and `X-Process-Time` response headers.
2. **`CORSMiddleware`**: Configures authorized client origins (`http://localhost:3000`, `http://localhost:5173`, etc.) and allows credentials, headers, and HTTP methods.
3. **`Exception Handlers`**: Intercepts `AttendAIException` (structured domain errors) and unhandled Python exceptions, returning sanitized JSON payloads with the active `request_id`.

---

## 4. Database Architecture & Multi-Tenancy

AttendAI implements an organization-based data isolation model:
- Every tenant entity links directly to `Organization.id`.
- Users and employees belong to an organization and a department.
- SQLAlchemy 2.0 Async ORM handles connection pooling and queries.
- Primary production engine: **PostgreSQL 16** via `asyncpg`.
- Fallback development engine: **SQLite** via `aiosqlite` with `check_same_thread=False`.

---

## 5. Core Workflows

### 5.1 Authentication & Token Refresh Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Browser
    participant API as FastAPI /api/v1/auth
    participant Sec as Security Engine (Argon2)
    participant DB as Database (Users & Tokens)
    participant Redis as Redis Cache

    User->>API: POST /api/v1/auth/login {email, password}
    API->>DB: Query User by Email
    DB-->>API: User record (hashed_password, role, is_active)
    API->>Sec: verify_password(plain, hashed_password)
    Sec-->>API: True
    API->>DB: Create RefreshToken record (7-day expiry)
    API->>Redis: Cache active session
    API-->>User: 200 OK {access_token (15m), refresh_token (7d), user}

    Note over User,API: When Access Token expires (HTTP 401)
    User->>API: POST /api/v1/auth/refresh {refresh_token}
    API->>DB: Verify RefreshToken exists & not revoked
    DB-->>API: Token valid
    API-->>User: 200 OK {access_token (15m), refresh_token (rotated)}
```

### 5.2 Attendance & Punch Lifecycle Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Emp as Employee
    participant API as FastAPI /api/v1/attendance
    participant Svc as AttendanceService
    participant DB as Database
    participant Anomaly as AnomalyService

    Emp->>API: POST /api/v1/attendance/clock-in
    API->>Svc: record_clock_in(employee_id, server_utc_time)
    Svc->>DB: Check shift assignment & grace period (15 min)
    Svc->>DB: Insert AttendanceRecord (status='present' or 'late')
    DB-->>API: Saved Record
    API-->>Emp: 200 OK {clock_in, status, late_minutes}

    opt Break Tracking
        Emp->>API: POST /api/v1/attendance/break {action: 'start'}
        API->>DB: Create AttendanceBreak (start_time)
        Emp->>API: POST /api/v1/attendance/break {action: 'end'}
        API->>DB: Update AttendanceBreak (end_time, duration)
    end

    Emp->>API: POST /api/v1/attendance/clock-out
    API->>Svc: record_clock_out(record_id, server_utc_time)
    Svc->>Svc: Calculate total worked hours & overtime
    Svc->>DB: Update AttendanceRecord (clock_out, worked_hours, overtime_hours)
    Svc->>Anomaly: check_for_anomalies(record)
    Anomaly-->>DB: Flag anomaly if overtime > 3h or break > 2h
    API-->>Emp: 200 OK {status: 'completed', worked_hours, overtime_hours}

    opt Accidental Clock-Out
        Emp->>API: POST /api/v1/attendance/re-clock-in
        API->>Svc: reopen_attendance_record(record_id)
        Svc->>DB: Nullify clock_out, recalculate active duration
        API-->>Emp: 200 OK {status: 'resumed', message: 'Shift reopened'}
    end
```

### 5.3 Custom Report Generation Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as Admin / HR / Employee
    participant UI as ExportModal.tsx
    participant API as FastAPI /api/v1/exports
    participant QBuild as ExportQueryBuilder
    participant Engine as Excel / CSV Generator
    participant DB as Database
    participant Storage as File Storage / Memory

    User->>UI: Clicks "Export Report" button
    UI->>UI: Opens modal "What would you like to download?"
    UI->>API: GET /api/v1/exports/config (User role)
    API-->>UI: Allowed report types, scopes, column registry
    
    User->>UI: Selects Report Type, Scope, Date Range & Columns
    UI->>API: POST /api/v1/exports/preview {type, scope, range, filters}
    API->>QBuild: Count matching records with role boundary
    QBuild->>DB: SELECT COUNT(*)
    DB-->>API: Record count (e.g., 188)
    API-->>UI: 200 OK {record_count: 188, can_export: true}

    User->>UI: Clicks "Generate & Download" (Format: XLSX)
    UI->>API: POST /api/v1/exports/generate {params, format: 'xlsx'}
    API->>QBuild: Fetch records & metadata
    QBuild->>DB: SELECT detailed rows
    DB-->>QBuild: Records dataset
    API->>Engine: generate_excel_bytes(rows, columns, metadata)
    Engine->>Engine: Build Cover Sheet + KPI Cards + PieChart
    Engine->>Engine: Build Itemized Details + Freeze Panes + Formulas
    Engine->>Engine: Build Department Summary + BarChart (if multi-dept)
    Engine-->>API: Formatted .xlsx binary bytes
    API->>DB: Insert ExportRecord (audit tracking)
    API-->>UI: 200 OK {export_id, download_url, file_size_bytes}
    UI->>API: GET /api/v1/exports/{id}/download?token=<jwt>
    API-->>UI: Binary File Stream (.xlsx with Content-Disposition)
```

### 5.4 Document Ingestion & Citation Retrieval Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrator
    actor Employee as Employee
    participant API as FastAPI /api/v1/policies
    participant Svc as PolicyService
    participant PyMu as PyMuPDF / python-docx
    participant DB as Database
    participant AI as AIOrchestrator

    Admin->>API: POST /api/v1/policies/upload (PDF / DOCX file)
    API->>Svc: Validate MIME type (reject .exe, .sh, .py)
    Svc->>PyMu: Extract text page-by-page / section-by-section
    PyMu-->>Svc: Extracted pages with section titles
    Svc->>DB: Insert Policy record
    Svc->>DB: Insert PolicyChunk records (chunk_index, section, page_number)
    API-->>Admin: 201 Created {policy_id, chunks_created: 14}

    Note over Employee,AI: Natural Language Policy Query
    Employee->>AI: "What is our policy on overtime compensation?"
    AI->>Svc: search_policies("overtime compensation")
    Svc->>DB: Full-text keyword match across PolicyChunks
    DB-->>Svc: Top matched chunks
    Svc-->>AI: Relevant chunks with titles, sections, and page numbers
    AI->>AI: Synthesize grounded response with precise citation
    AI-->>Employee: Grounded answer with citation: [Overtime Policy, Page 2, Section 3]
```

---

## 6. Infrastructure & Deployment Topology

In containerized production deployments via `docker-compose.yml`:
- **Nginx Reverse Proxy**: Listens on ports 80/8000, proxies static UI requests to the `frontend` container, and balances API requests between `backend_1` and `backend_2` using the `least_conn` load balancing algorithm.
- **FastAPI Cluster**: Two identical stateless backend instances with Gunicorn/Uvicorn workers.
- **Database & Cache**: Dedicated PostgreSQL 16 and Redis 7 containers configured with healthchecks, persistent Docker volumes, and container isolation.
