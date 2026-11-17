# AttendAI — Comprehensive Role-Based User Guide

AttendAI provides three tailored, role-specific user portals designed to present relevant operational data while eliminating unnecessary administrative clutter.

---

## 1. Administrator User Guide

The **Administrator** role (`admin@attendai.com`) exercises global organization governance, system configuration, diagnostics, and security controls.

### 1.1 Executive Dashboard
- **Location**: `/` (My Dashboard)
- **KPI Metrics**: Total Headcount, Present Today, Absent Today, Late Arrivals, Employees on Leave, Pending Approvals, Total Overtime Hours, Organization Attendance Rate.
- **Visual Analytics**: Workforce overview charts, departmental performance cards, overtime distribution graphs, and AI workforce insights.

### 1.2 Managing Employees & Authorizing Onboarding
- **Employee Directory** (`/employees`):
  - View, search, and paginate through all workforce employees across departments.
  - Filter by department, designation, or employment status (`Active` / `Inactive`).
  - Click **Add Employee** to directly create a new employee profile with credentials.
- **Onboarding Requests Queue**:
  - Review employee onboarding requests submitted by HR Managers.
  - Inspect proposed details: employee code, name, department, role, joining date.
  - Click **Authorize & Add** to automatically provision user and employee accounts, or **Reject** with an explanation.

### 1.3 Shifts & Scheduling Configuration
- **Location**: `/shifts`
- **Shift Templates**:
  - Click **Create Shift** to add a new shift schedule.
  - Define shift name, unique code (e.g. `GEN`, `MOR`, `NOC`), start time, end time, grace period in minutes (default: 15), required hours (default: 8.0), and overnight flag.
- **Assigning Shifts**:
  - Assign individual employees or whole departments to specific shift schedules with an effective date range.

### 1.4 Workforce Attendance & Correction Audits
- **Location**: `/attendance`
- View organization-wide attendance records by date or date range.
- Filter by department, attendance status (`Present`, `Late`, `Half Day`, `Absent`), or search by employee.
- **Attendance Correction Modal**:
  - For missing or contested punches, click **Correct Punch**.
  - Enter adjusted clock-in/clock-out timestamps and supply a mandatory audit justification (e.g., *"Terminal sync outage"*).

### 1.5 Leave Administration
- **Location**: `/leave`
- Review leave applications across all departments (`Annual`, `Sick`, `Casual`, `Unpaid`).
- Approve or reject applications with reviewer remarks.

### 1.6 Anomaly Detection & Investigation
- **Location**: `/anomalies`
- Inspect anomalies flagged by deterministic rules or the Isolation Forest machine learning model.
- Filter by severity (`Critical`, `High`, `Medium`, `Low`) and review status (`Pending`, `Investigating`, `Resolved`, `Dismissed`).
- Open anomaly details, evaluate multivariate metrics, and record resolution remarks.

### 1.7 Policy Document Management
- **Location**: `/policies`
- Click **Upload Policy** to upload `.pdf`, `.docx`, or `.txt` policy manuals.
- Specify category (`Attendance & Punctuality`, `Leave Guidelines`, etc.).
- The system automatically chunks the text using PyMuPDF / python-docx and indexes it for citations in the AI Assistant.

### 1.8 AI Workforce Assistant
- **Location**: `/ai`
- Ask questions about organization-wide workforce metrics:
  - *"Which department logged the highest overtime this month?"*
  - *"List all employees who arrived late more than three times this week."*
  - *"Compare attendance trends between Engineering and Customer Success."*

### 1.9 Generating Custom Reports
- Click any **Export Report** button.
- Select from 10 Administrator report types (*Complete Organization Report, Department Report, Attendance Report, Overtime Report, Anomaly Report*, etc.).
- Choose data scope (*Entire Organization, Department, Employee*), date range, and desired columns.
- Click **Preview** to view matching record counts, then download as CSV or executive-grade Excel (`.xlsx`).

### 1.10 System Diagnostics & Audit Logs
- **Diagnostics** (`/diagnostics`): Real-time telemetry on database connection pool, Redis cache status, memory usage, and AI provider health.
- **Audit Logs** (`/audit-logs`): Immutable ledger tracking sensitive system events, actor user IDs, IP addresses, and payload diffs.

---

## 2. HR Manager User Guide

The **HR Manager** role (`hrmanager@attendai.com`) oversees authorized departments, handles operational attendance adjustments, and submits new hire onboarding requests.

### 2.1 Department Workforce Overview
- **Location**: `/` (HR Dashboard)
- Real-time KPIs tailored to authorized departments: Headcount, Present Today, Absent Today, Pending Leave Requests, Pending Punch Corrections, Overtime Logged.

### 2.2 Submitting New Employee Onboarding Requests
- **Location**: `/employees`
- Click **Request New Employee**.
- Fill in candidate information: First Name, Last Name, Employee Code, Corporate Email, Department, Designation, and Date of Joining.
- Submit to route the proposal into the Administrator's authorization queue.

### 2.3 Attendance Monitoring & Approvals
- **Location**: `/attendance`
- Monitor daily clock-in/out timestamps and break activity for department staff.
- Apply manager-level punch corrections with mandatory rationale logs.

### 2.4 Reviewing Leave Applications
- **Location**: `/leave`
- Review leave submissions from team members.
- Check requested dates against departmental shift schedules to avoid understaffing before clicking **Approve** or **Reject**.

### 2.5 Anomaly Investigation
- **Location**: `/anomalies`
- Review department-specific anomalies (repeated late arrivals, excessive breaks, overtime spikes) and document resolution notes.

### 2.6 Departmental Custom Reports
- Open custom export popup via **Export Attendance** or **Export Leave**.
- Select **Authorized Department Report** or **Individual Employee Report**.
- Preview matching record counts and download formatted workbooks for payroll and compliance audits.

---

## 3. Employee User Guide

The **Employee** role (`employee@attendai.com` / Alex Mercer) has access to a focused personal workspace without administrative navigation clutter.

### 3.1 Personal Clock-In & Shift Punch Tracking
- **Location**: `/` (My Dashboard)
- **Live Clock**: Displays local operating time and active shift name (e.g. `General Shift (09:00 - 17:30)`).
- **Daily Clock-In**:
  - Click the **Clock In** button upon commencing work.
  - The system records server-side UTC time, compares against shift start and the 15-minute grace period, and displays your punctuality status (`Present` or `Late Arrival`).
- **Taking Breaks**:
  - Click **Start Break** (specify reason: *Lunch*, *Personal*, etc.).
  - The dashboard displays active break duration. Click **End Break** upon returning.
- **Clocking Out**:
  - Click **Clock Out** when finishing your workday.
  - The system computes net worked hours, checks for overtime, and marks today's status as `Completed for Today`.
- **Re-Clock-In / Resume Shift**:
  - If you accidentally clocked out or need to resume active duties, click **Resume Shift** / **Re-Clock In** to reopen the punch record.

### 3.2 Schedule & Shift Visibility
- **Schedule Card**: Displays assigned shift code, expected working hours (e.g. 8h required), and punctuality grace window.

### 3.3 Applying for Leave & Checking Balances
- **Location**: `/leave`
- View current available leave balances (e.g. 18 days Paid Time Off remaining).
- Click **Apply for Leave**.
- Select leave type (*Annual Leave, Sick Leave, Casual Leave*), date range, and reason.
- Track application status in the list (`Pending`, `Approved`, `Rejected`).

### 3.4 In-Browser Policy Document Reading & Downloading
- **Location**: `/policies`
- Browse published company policies (e.g., *Attendance & Working Hours Policy*, *Time-Off Guidelines*).
- **Read**: Click **Read** to open the in-browser document viewer. For PDFs, navigate pages, zoom in/out, and read full text. For DOCX, view structured headings and tables.
- **Download**: Click **Download** to obtain the original document file.

### 3.5 Personal AI Assistant
- **Location**: `/ai`
- Ask questions about your personal records and company policies:
  - *"How many hours have I worked this week?"*
  - *"How much overtime have I logged this month?"*
  - *"What is our grace period policy for clock-ins?"*
  - *"What is my remaining paid time off balance?"*
- *Privacy Guarantee*: Your personal AI assistant strictly accesses your own verified records and cannot access peer or executive data.

### 3.6 Downloading Personal Reports
- Click **Export Report** from any personal page.
- Choose from personal report types: *My Monthly Attendance, My Attendance History, My Overtime Report, My Working Hours, My Leave History, My Shift History*.
- Select date range and format (CSV or Excel `.xlsx`).
- Click **Generate & Download** to receive your personal spreadsheet.
