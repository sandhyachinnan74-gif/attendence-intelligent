# AttendAI — Security Architecture & Threat Mitigations

---

## 1. Authentication & Session Management
- **Password Hashing**: State-of-the-art Argon2id via `argon2-cffi`. No legacy MD5 or plain SHA.
- **JWT Tokens**: Short-lived (15 min) access tokens with HS256 algorithm and unique `jti`.
- **Refresh Token Rotation**: Refresh tokens are single-use SHA-256 hashed database entries. Every refresh request issues a new refresh token and immediately invalidates the previous one.
- **Session Revocation**: Calling `/api/v1/auth/logout` sets `is_revoked = True` on the refresh token.

---

## 2. Authorization & RBAC
- **Strict Role Boundaries**:
  - `admin`: Full organization access, system diagnostics, configuration.
  - `hr_manager`: Department-scoped workforce management, leave approval, anomaly triage, policy uploads.
  - `employee`: Personal attendance sheet, punch clock, personal leave requests, policy search.
- **Zero Client Trust**: All roles and IDs are resolved strictly from the decoded server JWT token, never from client request bodies.

---

## 3. AI Safety & Guardrails
- **Prompt Injection Defense**: Regex and lexical pattern filters scan all incoming prompts for jailbreaks, prompt leaks, or database tampering.
- **Strict Tool Whitelisting**: LLMs cannot execute raw SQL or run unapproved operations.
- **Redaction**: Secret tokens, API keys, or hash fragments are automatically stripped before returning responses to clients.
- **Grounding & Citations**: Answers must cite verified database records or official policy chunk references. Unsupported claims are explicitly stated as unverified.
