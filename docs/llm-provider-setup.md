# AttendAI — LLM Provider Setup & Failover Configuration

AttendAI features a resilient, multi-tiered AI execution harness capable of seamlessly transitioning between NVIDIA NIM, GroqCloud, Google Gemini, and a deterministic local Mock engine.

---

## 1. Obtaining Cloud API Keys

> [!CAUTION]
> **Secret Hygiene**: Never commit actual API keys to version control. Keys must be stored in the root `.env` file (which is git-ignored) or passed as environment variables in production containers.

### 1.1 NVIDIA NIM (Primary Provider)
1. Navigate to the [NVIDIA API Catalog](https://build.nvidia.com/).
2. Sign in with an NVIDIA developer account.
3. Locate the model: **`mistralai/mistral-large-4-1t-a52b`** (or `mistral-large-2407`).
4. Click **Get API Key** and generate a personal key starting with `nvapi-`.
5. Copy the key for your `.env` file.

### 1.2 GroqCloud (Secondary Fallback Provider)
1. Navigate to the [GroqCloud Console](https://console.groq.com/).
2. Create an account or sign in.
3. In the sidebar, select **API Keys**.
4. Click **Create API Key**, provide a label (e.g. `AttendAI-Failover`), and generate a key starting with `gsk_`.
5. Copy the key for your `.env` file.

### 1.3 Google Gemini (Tertiary Optional Provider)
1. Navigate to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with a Google account.
3. Click **Get API Key** and generate a key for Gemini models (`gemini-1.5-pro` or `gemini-1.5-flash`).
4. Copy the key for your `.env` file.

---

## 2. Environment Configuration

Open or create your `.env` file in the repository root and configure the LLM section:

```ini
# ==============================================================================
# LLM Provider Configuration
# ==============================================================================
# Primary Provider selector: nvidia | groq | gemini | mock
LLM_PROVIDER=nvidia

# ------------------------------------------------------------------------------
# 1. NVIDIA NIM (Primary High-Reasoning Engine)
# ------------------------------------------------------------------------------
NVIDIA_API_KEY=nvapi-your_actual_nvidia_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=mistralai/mistral-large-4-1t-a52b

# ------------------------------------------------------------------------------
# 2. GroqCloud (Ultra-Fast Automated Secondary Fallback)
# ------------------------------------------------------------------------------
GROQ_API_KEY=gsk_your_actual_groq_key_here
GROQ_MODEL=openai/gpt-oss-120b

# ------------------------------------------------------------------------------
# 3. Google Gemini (Optional Tertiary Fallback)
# ------------------------------------------------------------------------------
GEMINI_API_KEY=AIzaSy_your_optional_gemini_key_here
GEMINI_MODEL=gemini-1.5-pro
```

---

## 3. Testing Provider Connectivity

AttendAI provides automated verification scripts and pytest test suites to validate provider connectivity.

### 3.1 Live Connectivity Test Script
Run the dedicated verification script to test inference and tool calling on your configured keys:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\python.exe backend/tests/verify_live_llm.py
```

#### Linux / macOS:
```bash
PYTHONPATH=backend ./venv/bin/python backend/tests/verify_live_llm.py
```

**Expected Output**:
```
============================================================
ATTENDAI — LIVE LLM PROVIDER VERIFICATION SUITE
============================================================
[1/4] Testing NVIDIA NIM Live Connectivity...
  Model: mistralai/mistral-large-4-1t-a52b
  Status: 200 OK — VERIFIED (Latency: 2450ms)
[2/4] Testing GroqCloud Live Connectivity...
  Model: openai/gpt-oss-120b
  Status: 200 OK — VERIFIED (Latency: 480ms)
[3/4] Testing Tool Calling with Real Attendance Query...
  Function invoked: get_late_arrivals
  Status: SUCCESS
[4/4] Testing Automated Failover Simulation...
  Simulating NVIDIA 401 Unauthorized...
  Failover to GroqCloud: SUCCESS (fallback_used: True)
============================================================
ALL LIVE PROVIDERS VERIFIED AND OPERATIONAL
============================================================
```

### 3.2 Running the Live Provider Pytest Suite
Run the automated test suite covering live provider integration:

#### Windows PowerShell:
```powershell
$env:PYTHONPATH="backend"
.\venv\Scripts\pytest.exe backend/tests/test_live_llm_providers.py -v
```

#### Linux / macOS:
```bash
PYTHONPATH=backend ./venv/bin/pytest backend/tests/test_live_llm_providers.py -v
```

---

## 4. Rate Limits, Timeouts & Error Handling

### 4.1 Automated Fallback Triggers
The `AIOrchestrator` automatically engages the next provider in the chain under the following conditions:
- **HTTP 401 / 403**: Invalid or revoked API credentials.
- **HTTP 429**: Rate limit exceeded (quota throttling).
- **HTTP 500 / 502 / 503**: Upstream cloud infrastructure outage.
- **Request Timeout**: NVIDIA requests exceeding 45 seconds or Groq requests exceeding 20 seconds.

### 4.2 Exponential Backoff & Retry
For transient rate limits (HTTP 429), the Groq provider executes an exponential backoff with jitter up to 3 retry attempts before proceeding down the fallback chain.

### 4.3 Fallback Audit Logging
Every failover event is recorded in the application logs and attached to the response payload:
```json
{
  "provider": "groq",
  "model": "openai/gpt-oss-120b",
  "fallback_used": true,
  "fallback_reason": "NvidiaNIMProvider returned HTTP 429 (Rate limit reached)"
}
```
This guarantees operational visibility without interrupting user workflows.
