# AttendAI — REST API Reference (`/api/v1`)

All endpoints require standard `Authorization: Bearer <access_token>` unless marked public.

---

## Authentication (`/api/v1/auth`)

- `POST /api/v1/auth/login`: Authenticate with work email and password. Returns `access_token`, `refresh_token`, and user profile.
- `POST /api/v1/auth/refresh`: Rotate refresh token and issue fresh access token.
- `POST /api/v1/auth/logout`: Revoke active refresh token.
- `GET /api/v1/auth/me`: Fetch authenticated user profile.
- `POST /api/v1/auth/change-password`: Update account password.

---

## Employees (`/api/v1/employees`)

- `GET /api/v1/employees`: Search and list workforce employees with department and status filters.
- `POST /api/v1/employees`: Create employee and provision linked user account (Admin/HR).
- `GET /api/v1/employees/{id}`: Retrieve detailed employee profile.
- `PUT /api/v1/employees/{id}`: Update employee details or active status.

---

## Attendance (`/api/v1/attendance`)

- `POST /api/v1/attendance/clock-in`: Record server-timestamped clock-in. Validates grace period.
- `POST /api/v1/attendance/clock-out`: Record clock-out, close ongoing breaks, compute worked and overtime minutes.
- `POST /api/v1/attendance/break`: Start or end ongoing break.
- `GET /api/v1/attendance`: Query attendance sheet with date range and department filters.
- `GET /api/v1/attendance/today`: Get current user's today attendance status.
- `POST /api/v1/attendance/{id}/correct`: Submit audited time correction with mandatory reason (Admin/HR).

---

## Shifts (`/api/v1/shifts`)

- `GET /api/v1/shifts`: List defined working shifts.
- `POST /api/v1/shifts`: Create new shift with start/end time, grace period, and overnight flag.
- `POST /api/v1/shifts/assign`: Assign shift to an employee with effective date.

---

## Leave (`/api/v1/leave`)

- `POST /api/v1/leave`: Submit leave application (annual, sick, casual, unpaid).
- `GET /api/v1/leave`: List leave requests (scoped to employee or organization).
- `PUT /api/v1/leave/{id}/review`: Approve or reject leave application with manager notes.

---

## Anomaly Detection (`/api/v1/anomalies`)

- `GET /api/v1/anomalies`: List flagged anomalies with severity and type filters.
- `POST /api/v1/anomalies/detect`: Run the hybrid anomaly detection pipeline (Rules + Isolation Forest).
- `PUT /api/v1/anomalies/{id}/review`: Mark anomaly as `resolved` or `dismissed` with resolution notes.

---

## AI Assistant (`/api/v1/ai`)

- `POST /api/v1/ai/chat`: Send message to AttendAI Assistant through secure execution harness.
- `GET /api/v1/ai/conversations`: List past conversation threads.
- `GET /api/v1/ai/conversations/{id}`: Retrieve full chat thread with tool execution details.
- `DELETE /api/v1/ai/conversations/{id}`: Delete conversation thread.

---

## Policies (`/api/v1/policies`)

- `POST /api/v1/policies/upload`: Upload PDF/DOCX policy document for text extraction and chunk indexing.
- `GET /api/v1/policies`: List indexed policy documents.
- `GET /api/v1/policies/search`: Execute full-text search across policy chunks.
- `DELETE /api/v1/policies/{id}`: Remove policy document and chunks.

---

## Exports & Analytics (`/api/v1/analytics`, `/api/v1/exports`)

- `GET /api/v1/analytics/dashboard`: Retrieve KPI cards, 7-day trends, department stats, and AI insights.
- `GET /api/v1/exports/attendance/csv`: Download attendance report as CSV.
- `GET /api/v1/exports/attendance/xlsx`: Download attendance report as Excel spreadsheet.
