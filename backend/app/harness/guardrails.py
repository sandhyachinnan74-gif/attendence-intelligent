import re
from typing import Tuple

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above)\s+instructions",
    r"disregard\s+(all\s+)?(prior|previous)\s+prompts",
    r"you\s+are\s+now\s+(an\s+unrestricted|root|admin)",
    r"reveal\s+(the\s+)?(system\s+prompt|secret\s+key|api\s+key|credentials)",
    r"drop\s+table",
    r"select\s+\*\s+from\s+users",
    r"delete\s+from\s+attendance",
    r"bypass\s+(permission|security|authorization)",
    r"leak\s+(private|sensitive)\s+data"
]

class HarnessGuardrails:
    @staticmethod
    def inspect_input(prompt: str) -> Tuple[bool, str]:
        """
        Returns (is_safe, reason).
        """
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False, f"Prompt injection or unauthorized instruction pattern detected: '{pattern}'"
        return True, "Safe"

    @staticmethod
    def sanitize_output(text: str) -> str:
        """
        Redacts leaked keys, JWTs, or passwords if accidentally echoed.
        """
        # Redact JWT tokens
        sanitized = re.sub(r"ey[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}", "[REDACTED_TOKEN]", text)
        # Redact potential API keys
        sanitized = re.sub(r"nvapi-[A-Za-z0-9_-]{20,}", "[REDACTED_NVIDIA_KEY]", sanitized)
        sanitized = re.sub(r"gsk_[A-Za-z0-9]{20,}", "[REDACTED_GROQ_KEY]", sanitized)
        return sanitized
