import pytest
from app.harness.providers.nvidia import NvidiaNIMProvider
from app.harness.providers.groq import GroqProvider
from app.harness.orchestrator import ai_orchestrator
from app.harness.tool_registry import TOOL_DEFINITIONS
from app.core.database import get_sessionmaker
from app.models.models import User
from sqlalchemy import select

@pytest.mark.asyncio
async def test_live_nvidia_nim_mistral_large_4():
    provider = NvidiaNIMProvider()
    response = await provider.generate_response(
        messages=[{"role": "user", "content": "Respond with the single word: VERIFIED"}],
        temperature=0.1
    )
    assert response["provider"] == "nvidia"
    assert response["model"] == "mistralai/mistral-large-4-1t-a52b"
    assert "VERIFIED" in response["content"].upper()
    assert response["latency_ms"] > 0

@pytest.mark.asyncio
async def test_live_nvidia_nim_tool_calling():
    provider = NvidiaNIMProvider()
    response = await provider.generate_response(
        messages=[{"role": "user", "content": "Which employees arrived late in the last 7 days?"}],
        tools=TOOL_DEFINITIONS[:4],
        temperature=0.1
    )
    assert response["tool_calls"] is not None
    assert len(response["tool_calls"]) > 0
    func_name = response["tool_calls"][0]["function"]["name"]
    assert func_name in ["get_late_arrivals", "get_attendance_summary"]

@pytest.mark.asyncio
async def test_live_groq_provider():
    provider = GroqProvider()
    response = await provider.generate_response(
        messages=[{"role": "user", "content": "Respond with the single word: VERIFIED"}],
        temperature=0.1
    )
    assert response["provider"] == "groq"
    assert response["model"] == "openai/gpt-oss-120b"
    assert "VERIFIED" in response["content"].upper()
    assert response["latency_ms"] > 0

@pytest.mark.asyncio
async def test_live_orchestrator_turn_with_nvidia():
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        user = (await db.execute(select(User).where(User.email == "admin@attendai.com"))).scalars().first()
        assert user is not None

        result = await ai_orchestrator.execute_turn(
            db=db,
            user=user,
            employee=None,
            user_message="Show me recent late arrivals.",
            conversation_history=[]
        )

        assert result["content"] is not None
        assert len(result["content"]) > 10
        assert result["provider"] == "nvidia"
        assert result["model"] == "mistralai/mistral-large-4-1t-a52b"

@pytest.mark.asyncio
async def test_live_groq_fallback_when_primary_fails():
    from app.core.config import settings
    original_key = settings.NVIDIA_API_KEY
    try:
        settings.NVIDIA_API_KEY = "invalid_key_to_force_fallback"
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as db:
            user = (await db.execute(select(User).where(User.email == "admin@attendai.com"))).scalars().first()
            assert user is not None
            result = await ai_orchestrator.execute_turn(
                db=db,
                user=user,
                employee=None,
                user_message="Hello, reply with OK for fallback test.",
                conversation_history=[]
            )
            assert result["fallback_used"] is True
            assert result["provider"] == "groq"
            assert result["model"] == "openai/gpt-oss-120b"
            assert len(result["content"]) > 0
    finally:
        settings.NVIDIA_API_KEY = original_key
