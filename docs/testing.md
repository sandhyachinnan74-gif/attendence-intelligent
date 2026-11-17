# AttendAI — Quality Assurance & Testing Suite Reference

AttendAI is verified across backend unit tests, integration tests, live AI cloud provider suites, frontend component tests, Playwright browser end-to-end tests, and Locust load tests.

---

## 1. Test Suite Summary & Actual Results

| Test Category | Framework | Scope / Coverage | Verified Result |
| :--- | :--- | :--- | :--- |
| **Backend Comprehensive Suite** | `pytest` + `pytest-asyncio` | 85 automated test cases across 16 test files | **85 / 85 Passed (100%)** |
| **Frontend Unit & Component** | `vitest` + React Testing Library | Login flow, role navigation, component guards | **7 / 7 Passed (100%)** |
| **Browser E2E User Journeys** | Playwright (Headless Chromium) | Admin, HR Manager, and Employee end-to-end portals | **3 / 3 Passed (100%)** |
| **Live Cloud LLM Inference** | Custom Async Runner | NVIDIA NIM (Mistral Large 4) & GroqCloud (GPT-OSS-120B) | **100% Live Verified** |
| **Performance & Load Testing** | `locust` (Headless load test) | 10 concurrent users, sub-50ms target latency | **71 Requests, 0 Failures (0.00%)** |

---

## 2. Running Backend Pytest Suites

### 2.1 Complete Backend Test Suite (85 Tests)
Executes all regression, AI, anomaly, policy, security, and export tests:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest.exe backend/tests/ -v
```

#### Linux / macOS:
```bash
PYTHONPATH=backend ./venv/bin/pytest backend/tests/ -v
```

---

### 2.2 Individual Targeted Test Suites

#### 1. Custom Reports & Excel Formatting (`test_custom_reports_and_exports.py`)
Validates role-based export scoping, CSV generation, and Excel formatting:
```bash
pytest backend/tests/test_custom_reports_and_exports.py -v
```
- `test_exports_config_role_scoping`: Verifies report type catalog filtering per role.
- `test_admin_generate_csv_xlsx_pdf`: Verifies CSV and formatted XLSX workbook generation.
- `test_employee_personal_export_enforcement`: Asserts employee cannot export peer data.
- `test_export_history_role_isolation`: Asserts role boundary on export records.

#### 2. Policy Reading & Ingestion (`test_policy_reading_and_download.py` & `test_policy_integration.py`)
Validates PyMuPDF extraction, structured reading endpoints, and original file downloads:
```bash
pytest backend/tests/test_policy_reading_and_download.py backend/tests/test_policy_integration.py -v
```

#### 3. Live LLM Providers & Failover (`test_live_llm_providers.py`)
Validates live NVIDIA NIM and GroqCloud cloud inference, tool calls, and automated failover:
```bash
pytest backend/tests/test_live_llm_providers.py -v
```

#### 4. Security Audit & Guardrails (`test_security_audit.py` & `test_harness.py`)
Validates prompt injection interception, secret scrubbing, and token expiration:
```bash
pytest backend/tests/test_security_audit.py backend/tests/test_harness.py -v
```

#### 5. Employee Personal AI Tools (`test_universal_intelligence_and_employee_tools.py`)
Validates all 8 personal employee tools and IDOR protection:
```bash
pytest backend/tests/test_universal_intelligence_and_employee_tools.py -v
```

#### 6. Onboarding Workflow (`test_onboarding_workflow.py`)
Validates two-tier HR onboarding request submission and Admin authorization:
```bash
pytest backend/tests/test_onboarding_workflow.py -v
```

#### 7. Timezone & Re-Clock-In (`test_reclock_in_and_timezone.py`)
Validates accurate local time punch tracking and shift reopening:
```bash
pytest backend/tests/test_reclock_in_and_timezone.py -v
```

---

## 3. Frontend Unit & Component Testing

Run Vitest in the `frontend` directory:

```bash
npm --prefix frontend test
```

**Verified Output**:
```
✓ src/pages/Login.test.tsx (3 tests)
✓ src/components/layout/AppLayout.test.tsx (2 tests)
✓ src/pages/Dashboard.test.tsx (2 tests)

Test Files  3 passed (3)
     Tests  7 passed (7)
  Duration  1.69s
```

---

## 4. Playwright Browser End-to-End Testing

Playwright drives a headless Chromium browser through live authentication, navigation, and core user actions across all three portals:

```bash
npx playwright test
```

- **Admin Portal Journey**: Log in as `admin@attendai.com`, verify 8 executive KPI cards, navigate to Employee Directory, verify search and pagination.
- **HR Manager Journey**: Log in as `hrmanager@attendai.com`, verify department attendance monitoring, open onboarding modal.
- **Employee Portal Journey**: Log in as `employee@attendai.com`, verify active punch status, check schedule card, verify personal leave balance.

---

## 5. Performance & Load Testing with Locust

The performance test suite in `tests/locustfile.py` evaluates API throughput, concurrent user sessions, and latency distribution:

```bash
locust -f tests/locustfile.py --headless -u 10 -r 2 -t 30s --host http://localhost:8000
```

### Verified Load Test Metrics
- **Total Requests Executed**: 71
- **Failed Requests**: 0 (0.00% failure rate)
- **Median Latency**: 22 ms
- **95th Percentile Latency**: 54 ms
- **Average Latency**: 34.12 ms
- **Throughput**: ~2.4 requests/second under sustained concurrent load.
