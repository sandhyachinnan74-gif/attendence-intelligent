# LLM Provider Setup Guide — AttendAI

AttendAI features an enterprise AI execution harness that abstracts LLM providers while enforcing row-level permissions, prompt injection guardrails, tool calling constraints, and citation verification.

---

## 1. NVIDIA NIM (Primary Provider)

Official Website: [https://build.nvidia.com/](https://build.nvidia.com/)

### Step-by-Step Configuration:
1. Navigate to [https://build.nvidia.com/](https://build.nvidia.com/) and click **Sign In** or create a free NVIDIA Developer account.
2. In the model catalog, search for **Mistral Large** (`mistralai/mistral-large-2407`).
3. Open the model page and verify availability for API access.
4. Click **Get API Key** to generate an API key (`nvapi-...`).
5. Open your local `.env` file and configure:
   ```env
   LLM_PROVIDER=nvidia
   NVIDIA_API_KEY=nvapi-your-key-here
   NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
   NVIDIA_MODEL=mistralai/mistral-large-2407
   ```

---

## 2. GroqCloud (Fast Inference Backup Provider)

Official Website: [https://console.groq.com/](https://console.groq.com/)

### Step-by-Step Configuration:
1. Go to [https://console.groq.com/](https://console.groq.com/) and register or sign in.
2. Navigate to **API Keys** in the left sidebar.
3. Click **Create API Key**, name it `attendai-local`, and copy the generated key (`gsk_...`).
4. Update `.env`:
   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk-your-key-here
   GROQ_MODEL=llama-3.3-70b-versatile
   ```

---

## 3. Google Gemini API (Optional Provider)

Official Website: [https://aistudio.google.com/](https://aistudio.google.com/)

### Step-by-Step Configuration:
1. Navigate to [https://aistudio.google.com/](https://aistudio.google.com/) and sign in with your Google account.
2. Click **Get API key** in the left sidebar.
3. Create a new key and copy the token.
4. Configure in `.env`:
   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODEL=gemini-1.5-pro
   ```

---

## 4. Deterministic Mock Engine (Local Zero-Config Fallback)

If no live API keys are provided, AttendAI automatically runs on its built-in `mock` provider.
- Full tool calling emulation (`get_my_attendance`, `get_late_arrivals`, `search_attendance_policy`, etc.)
- Deterministic response synthesis
- Fully offline, reproducible testing with zero token cost
```env
LLM_PROVIDER=mock
```
