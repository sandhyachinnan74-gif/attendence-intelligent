import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.models import User, Employee, AuditLog
from app.harness.providers.base import BaseLLMProvider
from app.harness.providers.nvidia import NvidiaNIMProvider
from app.harness.providers.groq import GroqProvider
from app.harness.providers.gemini import GeminiProvider
from app.harness.providers.mock import MockLLMProvider
from app.harness.tool_registry import ToolRegistry, TOOL_DEFINITIONS
from app.harness.permissions import HarnessPermissions
from app.harness.guardrails import HarnessGuardrails
from app.harness.output_validator import OutputValidator

logger = logging.getLogger(__name__)

class AIOrchestrator:
    def __init__(self):
        self._provider = None

    def get_provider(self) -> BaseLLMProvider:
        provider_name = settings.LLM_PROVIDER.lower()
        if provider_name == "nvidia" and settings.NVIDIA_API_KEY:
            return NvidiaNIMProvider()
        elif provider_name == "groq" and settings.GROQ_API_KEY:
            return GroqProvider()
        elif provider_name == "gemini" and settings.GEMINI_API_KEY:
            return GeminiProvider()
        else:
            return MockLLMProvider()

    def get_providers_chain(self) -> List[BaseLLMProvider]:
        chain: List[BaseLLMProvider] = []
        primary = settings.LLM_PROVIDER.lower()

        # Add primary provider first if configured
        if primary == "nvidia" and settings.NVIDIA_API_KEY:
            chain.append(NvidiaNIMProvider())
        elif primary == "groq" and settings.GROQ_API_KEY:
            chain.append(GroqProvider())
        elif primary == "gemini" and settings.GEMINI_API_KEY:
            chain.append(GeminiProvider())

        # Add fallback providers
        if settings.GROQ_API_KEY and not any(isinstance(p, GroqProvider) for p in chain):
            chain.append(GroqProvider())
        if settings.NVIDIA_API_KEY and not any(isinstance(p, NvidiaNIMProvider) for p in chain):
            chain.append(NvidiaNIMProvider())

        # Ultimate offline fallback
        chain.append(MockLLMProvider())
        return chain

    async def generate_with_fallback(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        override_provider: Optional[BaseLLMProvider] = None
    ) -> tuple[Dict[str, Any], BaseLLMProvider, bool]:
        if override_provider:
            resp = await override_provider.generate_response(messages=messages, tools=tools)
            return resp, override_provider, False

        providers = self.get_providers_chain()
        for i, provider in enumerate(providers):
            try:
                resp = await provider.generate_response(messages=messages, tools=tools)
                return resp, provider, (i > 0)
            except Exception as e:
                logger.warning(
                    f"LLM Provider '{type(provider).__name__}' failed: {e}. "
                    f"Attempting fallback to next provider in chain."
                )
                continue

        mock = MockLLMProvider()
        resp = await mock.generate_response(messages=messages, tools=tools)
        return resp, mock, True

    async def execute_turn(
        self,
        db: AsyncSession,
        user: User,
        employee: Optional[Employee],
        user_message: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes a complete AI turn with security harness, tool resolution, and audit logging.
        """
        # 1. Guardrails check
        is_safe, reason = HarnessGuardrails.inspect_input(user_message)
        if not is_safe:
            return {
                "content": f"Security Notice: Request blocked by AttendAI AI harness. {reason}",
                "tool_calls": [],
                "tool_results": [],
                "citations": [],
                "model": "attendai-guardrails",
                "provider": "security_harness"
            }

        # 2. Build system instructions
        role_label = user.role.replace("_", " ").title()
        system_prompt = (
            f"You are AttendAI Assistant, an enterprise workforce intelligence AI. "
            f"The calling user is authenticated as '{user.email}' with role '{role_label}'. "
            f"You have access to authorized backend tools to query verified workforce attendance records and HR policies. "
            f"Always ground your answers in actual tool results. If information is not available, explicitly state so. "
            f"Never invent records, metrics or policies."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for hist in conversation_history[-6:]:  # Keep recent context
            messages.append({"role": hist["role"], "content": hist["content"]})
        messages.append({"role": "user", "content": user_message})

        # 3. Filter permitted tools
        allowed_tools = HarnessPermissions.filter_tools_for_user(user.role, TOOL_DEFINITIONS)

        # 4. First LLM call with resilient multi-provider failover
        first_resp, active_provider, fallback_used = await self.generate_with_fallback(
            messages=messages,
            tools=allowed_tools if allowed_tools else None
        )

        tool_calls = first_resp.get("tool_calls")
        tool_results = []

        # 5. Execute tools if called
        if tool_calls:
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}

                # Check permission
                if not HarnessPermissions.is_tool_allowed(user.role, func_name):
                    res = {"error": f"Permission denied: role '{user.role}' cannot invoke tool '{func_name}'"}
                else:
                    res = await ToolRegistry.execute_tool(
                        name=func_name,
                        arguments=args,
                        db=db,
                        user=user,
                        employee=employee
                    )

                # Record audit log
                audit = AuditLog(
                    organization_id=user.organization_id,
                    user_id=user.id,
                    action=f"AI_TOOL_CALL:{func_name}",
                    resource_type="ai_harness",
                    resource_id=func_name,
                    details={"arguments": args, "result_preview": str(res)[:300]}
                )
                db.add(audit)

                tool_results.append({
                    "tool_call_id": tc.get("id"),
                    "tool_name": func_name,
                    "output": res
                })

            await db.commit()

            # Second turn to generate synthesized response
            messages.append({
                "role": "assistant",
                "content": first_resp.get("content") or "",
                "tool_calls": tool_calls
            })
            for tr in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tr["tool_call_id"],
                    "content": json.dumps(tr["output"])
                })

            try:
                second_resp = await active_provider.generate_response(messages=messages)
            except Exception as e:
                logger.warning(f"Second turn with {type(active_provider).__name__} failed: {e}. Falling back.")
                second_resp, _, _ = await self.generate_with_fallback(messages=messages)

            final_content = second_resp.get("content") or first_resp.get("content") or ""
        else:
            final_content = first_resp.get("content") or ""

        # 6. Sanitize and validate
        final_content = HarnessGuardrails.sanitize_output(final_content)
        validated = OutputValidator.validate_and_format(final_content, tool_results, user.role)

        return {
            "content": validated["validated_text"],
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "citations": validated["citations"],
            "model": first_resp.get("model", "default"),
            "provider": first_resp.get("provider", "default"),
            "fallback_used": fallback_used,
            "latency_ms": first_resp.get("latency_ms", 0)
        }

ai_orchestrator = AIOrchestrator()
