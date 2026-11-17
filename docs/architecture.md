# AttendAI — System Architecture

AttendAI is an enterprise-grade AI-powered workforce time-and-attendance platform engineered for high accuracy, deterministic compliance, and secure conversational intelligence.

---

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    Client["Enterprise Client (Web / Mobile)"] -->|HTTPS / WSS| LB["Nginx Reverse Proxy & Load Balancer"]
    
    subgraph "DMZ & Ingress"
        LB -->|Static Assets| Frontend["React SPA (Vite / Tailwind)"]
        LB -->|/api/v1/ Load Balanced| FastAPIRep1["FastAPI Replica 1"]
        LB -->|/api/v1/ Load Balanced| FastAPIRep2["FastAPI Replica 2"]
    end

    subgraph "Core Business & AI Layer"
        FastAPIRep1 --> ServiceLayer["Attendance Engine & Business Services"]
        FastAPIRep2 --> ServiceLayer
        ServiceLayer --> AnomalyEngine["Hybrid Anomaly Engine (Rules + Isolation Forest)"]
        ServiceLayer --> AIHarness["AI Security & Execution Harness"]
    end

    subgraph "Storage & Caching"
        ServiceLayer -->|SQLAlchemy 2.0 Async| PostgreSQL[("PostgreSQL 16 Primary DB")]
        ServiceLayer -->|Aioredis / FakeRedis| RedisCache[("Redis 7 Cache & Queues")]
    end

    subgraph "External Inference"
        AIHarness -->|HTTPS / Tool Calling| NIM["NVIDIA NIM (Mistral Large)"]
        AIHarness -->|Failover| Groq["GroqCloud"]
        AIHarness -->|Fallback| Mock["Deterministic Mock Provider"]
    end
```

---

## 2. Attendance Lifecycle State Diagram

```mermaid
stateDiagram-v2
    [*] --> Scheduled: Shift Assigned
    Scheduled --> Present: Clock-In (Within Grace Window)
    Scheduled --> Late: Clock-In (Past Grace Window)
    Scheduled --> Absent: No Clock-In Recorded
    
    Present --> OnBreak: Start Break
    OnBreak --> Present: End Break
    
    Late --> OnBreak: Start Break
    OnBreak --> Late: End Break

    Present --> Completed: Clock-Out
    Late --> Completed: Clock-Out
    
    Present --> Incomplete: Missing Clock-Out (Past Day)
    Late --> Incomplete: Missing Clock-Out (Past Day)

    Incomplete --> Audited: Attendance Correction (Manager)
    Completed --> Audited: Attendance Correction (Manager)
    Audited --> [*]
    Completed --> [*]
    Absent --> [*]
```

---

## 3. High Availability vs Load Balancing

> [!NOTE]
> **Load Balancing vs High Availability**:
> The Nginx load balancer distributes HTTP requests across multiple stateless FastAPI backend replicas using the `least_conn` strategy. However, database high availability requires PostgreSQL replication (such as Patroni or AWS Aurora Multi-AZ) with automated failover. Running a single PostgreSQL container provides local persistence, not database fault tolerance.
