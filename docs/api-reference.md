# AttendAI — Complete REST API Reference

All AttendAI REST API endpoints are served under the `/api/v1` namespace.

---

## Standard Headers & Response Codes

### Request Headers
| Header | Type | Description |
| :--- | :--- | :--- |
| `Authorization` | `string` | `Bearer <access_token>` (Required for authenticated endpoints) |
| `Content-Type` | `string` | `application/json` (or `multipart/form-data` for file uploads) |

### Response Headers
| Header | Type | Description |
| :--- | :--- | :--- |
| `X-Request-ID` | `string` | Unique UUIDv4 identifier assigned to the inbound HTTP request. |
| `X-Process-Time` | `string` | Total server execution duration in milliseconds (e.g. `24.15ms`). |

### Standard HTTP Status Codes
- `200 OK`: Request succeeded.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Validation failure or semantic parameter error.
- `401 Unauthorized`: Missing, expired, or invalid JWT access token.
- `403 Forbidden`: Authenticated user lacks required RBAC role or resource authorization.
- `404 Not Found`: Target entity does not exist within the organization.
- `422 Unprocessable Entity`: Request body violates schema requirements.
- `500 Internal Server Error`: Server exception (details logged with `X-Request-ID`).

---

## 1. Authentication (`/api/v1/auth`)

### `POST /api/v1/auth/login`
Authenticate with email and password to receive JWT credentials.
- **Auth**: Public
- **Request Body**:
  ```json
  {
    "email": "admin@attendai.com",
    "password": "Admin@123"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "refresh_token": "8fbc923a-...",
    "token_type": "bearer",
    "user": {
      "id": "e83a91b2-9183-43ab-82e6-a22109c797e8",
      "email": "admin@attendai.com",
      "role": "admin",
      "organization_id": "01948979-..."
    }
  }
  ```
- **Errors**: `401 Unauthorized` (Invalid credentials), `422 Unprocessable Entity`.

### `POST /api/v1/auth/refresh`
Exchange a valid refresh token for a newly issued access token.
- **Auth**: Public
- **Request Body**: `{"refresh_token": "8fbc923a-..."}`
- **Response `200 OK`**: `{"access_token": "eyJhb...", "refresh_token": "...", "token_type": "bearer"}`
- **Errors**: `401 Unauthorized` (Token revoked or expired).

### `GET /api/v1/auth/me`
Retrieve profile of currently authenticated user.
- **Auth**: Bearer Token (Any role)
- **Response `200 OK`**: User profile, organization ID, and attached employee record details.

### `POST /api/v1/auth/logout`
Revoke refresh token and terminate active session.
- **Auth**: Bearer Token
- **Response `200 OK`**: `{"message": "Logged out successfully"}`

### `POST /api/v1/auth/change-password`
Update authenticated user's password.
- **Auth**: Bearer Token
- **Request Body**: `{"current_password": "...", "new_password": "..."}`
- **Response `200 OK`**: `{"message": "Password updated successfully"}`

---

## 2. Employees & Onboarding (`/api/v1/employees`)

### `GET /api/v1/employees`
List organization employees with pagination and filters.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Query Parameters**: `skip` (default 0), `limit` (default 50), `department_id`, `search`, `is_active`.
- **Response `200 OK`**: `[{"id": "...", "employee_code": "EMP001", "first_name": "Alex", "last_name": "Mercer", ...}]`

### `POST /api/v1/employees`
Direct employee creation by Administrator.
- **Auth**: Bearer Token (`admin`)
- **Request Body**:
  ```json
  {
    "employee_code": "EMP201",
    "first_name": "Marcus",
    "last_name": "Brody",
    "email": "marcus.brody@attendai.com",
    "password": "AttendAI@123",
    "department_id": "...",
    "designation": "Staff Engineer",
    "role": "employee"
  }
  ```
- **Response `201 Created`**: Complete created Employee model.

### `POST /api/v1/employees/request`
Submit a new employee onboarding proposal for Administrator approval.
- **Auth**: Bearer Token (`hr_manager`, `admin`)
- **Request Body**: `{"employee_code": "EMP202", "first_name": "Jane", "last_name": "Doe", "email": "...", "department_id": "...", "designation": "..."}`
- **Response `201 Created`**: `{"id": "...", "status": "pending_approval", ...}`

### `GET /api/v1/employees/onboarding-requests`
List pending or resolved onboarding requests.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Query Parameters**: `status` (`pending_approval`, `approved`, `rejected`).
- **Response `200 OK`**: List of Onboarding Request records.

### `POST /api/v1/employees/onboarding-requests/{request_id}/review`
Admin reviews, authorizes and automatically creates user/employee accounts.
- **Auth**: Bearer Token (`admin`)
- **Request Body**: `{"action": "approve", "rejection_reason": null}`
- **Response `200 OK`**: `{"status": "approved", "employee_id": "...", "user_id": "..."}`

---

## 3. Departments (`/api/v1/departments`)

### `GET /api/v1/departments`
List all departments within the organization.
- **Auth**: Bearer Token (Any role)
- **Response `200 OK`**: `[{"id": "...", "name": "Engineering", "code": "ENG", "employee_count": 42}]`

### `POST /api/v1/departments`
Create a new department.
- **Auth**: Bearer Token (`admin`)
- **Request Body**: `{"name": "Security & Compliance", "code": "SEC"}`
- **Response `201 Created`**: Department record.

### `PUT /api/v1/departments/{department_id}`
Update department name or manager.
- **Auth**: Bearer Token (`admin`)
- **Request Body**: `{"name": "Cybersecurity", "manager_id": "..."}`

---

## 4. Shifts & Scheduling (`/api/v1/shifts`)

### `GET /api/v1/shifts`
List organization shift templates.
- **Auth**: Bearer Token (`admin`, `hr_manager`, `employee`)
- **Response `200 OK`**: `[{"id": "...", "name": "General Shift", "code": "GEN", "start_time": "09:00:00", "end_time": "17:30:00", "grace_period_minutes": 15, "required_hours": 8.0}]`

### `POST /api/v1/shifts`
Create new shift template.
- **Auth**: Bearer Token (`admin`)
- **Request Body**: `{"name": "Night Shift", "code": "NOC", "start_time": "22:00:00", "end_time": "06:30:00", "grace_period_minutes": 15, "required_hours": 8.0, "is_overnight": true}`

### `POST /api/v1/shifts/assign`
Assign an employee to a shift schedule.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Request Body**: `{"employee_id": "...", "shift_id": "...", "effective_from": "2026-11-01"}`

### `GET /api/v1/shifts/my-shift`
Retrieve authenticated employee's active schedule.
- **Auth**: Bearer Token (`employee`)
- **Response `200 OK`**: Active shift assignment details.

---

## 5. Time & Attendance (`/api/v1/attendance`)

### `POST /api/v1/attendance/clock-in`
Record employee clock-in timestamp.
- **Auth**: Bearer Token (`employee`, `hr_manager`, `admin`)
- **Response `200 OK`**:
  ```json
  {
    "id": "...",
    "date": "2026-11-17",
    "clock_in": "2026-11-17T09:02:14Z",
    "status": "present",
    "late_minutes": 0
  }
  ```

### `POST /api/v1/attendance/clock-out`
Record employee clock-out, calculating worked hours and overtime.
- **Auth**: Bearer Token
- **Response `200 OK`**: `{"clock_out": "2026-11-17T17:32:00Z", "worked_minutes": 510, "overtime_minutes": 0, "status": "completed"}`

### `POST /api/v1/attendance/break`
Toggle break state (start or end).
- **Auth**: Bearer Token
- **Request Body**: `{"action": "start", "reason": "Lunch"}`
- **Response `200 OK`**: Break record with start/end timestamps and duration.

### `POST /api/v1/attendance/re-clock-in` (or `/resume-shift`)
Reopen an attendance shift if closed by mistake.
- **Auth**: Bearer Token
- **Response `200 OK`**: `{"status": "resumed", "message": "Attendance shift reopened"}`

### `GET /api/v1/attendance/today`
Fetch current day's active punch state for authenticated employee.
- **Auth**: Bearer Token
- **Response `200 OK`**: Punch status, current break state, active minutes.

### `POST /api/v1/attendance/{record_id}/correct`
Submit a formal attendance correction with audit justification.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Request Body**: `{"new_clock_in": "09:00:00", "new_clock_out": "17:30:00", "reason": "Biometric terminal outage"}`

---

## 6. Leave Management (`/api/v1/leave`)

### `GET /api/v1/leave`
List leave requests. (Employees view personal records; Admin/HR view workforce records).
- **Auth**: Bearer Token

### `POST /api/v1/leave`
Submit a leave request.
- **Auth**: Bearer Token
- **Request Body**:
  ```json
  {
    "leave_type": "annual",
    "start_date": "2026-12-01",
    "end_date": "2026-12-05",
    "reason": "Family vacation"
  }
  ```
- **Response `201 Created`**: Saved LeaveRecord with status `pending`.

### `PUT /api/v1/leave/{leave_id}/review`
Manager decision on pending leave request.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Request Body**: `{"status": "approved", "resolution_notes": "Coverage confirmed"}`

---

## 7. Anomaly Detection (`/api/v1/anomalies`)

### `GET /api/v1/anomalies`
List detected anomalies across the workforce.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Query Parameters**: `severity`, `status`, `department_id`.

### `POST /api/v1/anomalies/detect`
Trigger asynchronous/synchronous anomaly scan over specified date range.
- **Auth**: Bearer Token (`admin`)
- **Request Body**: `{"start_date": "2026-11-01", "end_date": "2026-11-17"}`

### `PUT /api/v1/anomalies/{anomaly_id}/review`
Update anomaly investigation state.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Request Body**: `{"status": "resolved", "resolution_notes": "Employee verified overtime authorization"}`

---

## 8. Policies & Guidelines (`/api/v1/policies`)

### `GET /api/v1/policies`
List all indexed policy documents.
- **Auth**: Bearer Token (Any role)

### `GET /api/v1/policies/search`
Perform full-text search across extracted policy chunks.
- **Auth**: Bearer Token
- **Query Parameters**: `q` (search query).
- **Response `200 OK`**: List of matched chunks with citations.

### `POST /api/v1/policies/upload`
Upload and extract a new policy document (PDF, DOCX, TXT).
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Body**: `multipart/form-data` with `file` and `category`.

### `GET /api/v1/policies/{policy_id}/content`
Retrieve structured content and sections for in-browser modal reading.
- **Auth**: Bearer Token (Any role)

### `GET /api/v1/policies/{policy_id}/download`
Download original uploaded policy document.
- **Auth**: Bearer Token or `?token=<jwt>` query param.

---

## 9. Analytics (`/api/v1/analytics`)

### `GET /api/v1/analytics/dashboard`
Workforce KPI summary and metrics for Admin and HR.
- **Auth**: Bearer Token (`admin`, `hr_manager`)
- **Response `200 OK`**: Headcount, present, absent, late, overtime hours, department performance.

### `GET /api/v1/analytics/employee-dashboard`
Personal workspace metrics for Employee dashboard.
- **Auth**: Bearer Token (`employee`)
- **Response `200 OK`**: Personal worked hours, monthly overtime, punctuality rate, leave balance.

---

## 10. Custom Reporting & Exports (`/api/v1/exports`)

### `GET /api/v1/exports/config`
Fetch allowed report types, scopes, and column registries for user's role.
- **Auth**: Bearer Token

### `POST /api/v1/exports/preview`
Calculate exact matching record count before generating.
- **Auth**: Bearer Token
- **Request Body**: `{"report_type": "attendance_org", "scope_type": "organization", "date_preset": "last_30_days", "format": "xlsx"}`
- **Response `200 OK`**: `{"record_count": 188, "can_export": true}`

### `POST /api/v1/exports/generate`
Generate formatted report workbook or CSV file.
- **Auth**: Bearer Token
- **Request Body**:
  ```json
  {
    "report_type": "attendance_org",
    "scope_type": "organization",
    "date_preset": "last_30_days",
    "columns": ["date", "employee_name", "department", "clock_in", "clock_out", "worked_hours", "overtime_hours", "status"],
    "format": "xlsx"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "export_id": "f3b149...",
    "report_name": "Organization Attendance Report",
    "format": "xlsx",
    "record_count": 188,
    "file_size_bytes": 14210,
    "download_url": "/api/v1/exports/f3b149.../download"
  }
  ```

### `GET /api/v1/exports/{export_id}/download`
Download generated report file.
- **Auth**: Bearer Token or `?token=<jwt>` query parameter.
- **Response `200 OK`**: Binary stream (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` or `text/csv`).

---

## 11. AI Workforce Assistant (`/api/v1/ai`)

### `POST /api/v1/ai/chat`
Execute conversational turn with grounded tool-augmented retrieval.
- **Auth**: Bearer Token (Any role)
- **Request Body**:
  ```json
  {
    "content": "Who arrived late in Engineering this week?",
    "conversation_id": null
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "conversation_id": "...",
    "message": {
      "role": "assistant",
      "content": "### Late Arrivals in Engineering (Nov 10 – Nov 17)\n\n| Employee | Date | Late By |\n| :--- | :--- | :--- |\n| David Miller | 2026-11-12 | 22 min |\n\n*Source: Time & Attendance Records Engine*",
      "tool_calls": [{"name": "get_late_arrivals", "arguments": {"department": "Engineering"}}]
    }
  }
  ```

### `GET /api/v1/ai/conversations`
List user's historical AI conversations.

---

## 12. Notifications (`/api/v1/notifications`)

### `GET /api/v1/notifications`
Fetch notifications for current user with filtering and pagination.
- **Auth**: Bearer Token
- **Query Parameters**: `category`, `priority`, `unread_only`.

### `POST /api/v1/notifications/read-all`
Mark all unread notifications as read.

### `PATCH /api/v1/notifications/{notification_id}/read`
Mark specific notification as read.

---

## 13. Global Search (`/api/v1/search`)

### `GET /api/v1/search`
Cross-entity search with role-level data scoping.
- **Auth**: Bearer Token
- **Query Parameters**: `q` (Search query text).
- **Response `200 OK`**: Grouped results across employees, policies, shifts, and attendance.

---

## 14. System Monitoring (`/api/v1/system`)

### `GET /api/v1/system/health`
Sanitized public health probe.
- **Auth**: Public
- **Response `200 OK`**: `{"status": "healthy", "database": "connected", "redis": "connected", "latency_ms": 73.08}`

### `GET /api/v1/system/diagnostics`
Comprehensive diagnostic telemetry.
- **Auth**: Bearer Token (`admin` only — HTTP 403 for others).
- **Response `200 OK`**: Database pool status, Redis memory, memory usage, AI provider status.

### `GET /api/v1/system/audit-logs`
Audit trail of system actions.
- **Auth**: Bearer Token (`admin` only).
