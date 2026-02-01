import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.llm_service import MultiTierLLMService, LLMProvider, LLMConfig

# Ralph Wiggum Technique Test Suite
# "Build systems that assume users (and AI) will misunderstand, misuse, or behave unpredictably—and still succeed safely."

@pytest.mark.asyncio
async def test_ralph_wiggum_fail_softly():
    """
    Principle: Fail Softly, Never Hard.
    Scenario: All LLM providers are down / API keys missing.
    Expectation: Service falls back to TEMPLATE provider and returns a helpful message.
    Ralph quote: "I'm in danger." -> System says "I'm in safe mode."
    """
    # Simulate environment with no API keys
    with patch.dict("os.environ", {}, clear=True):
        service = MultiTierLLMService()

        # Mock network checks to fail
        service.check_ollama_available = AsyncMock(return_value=False)

        # Ensure all non-template providers are marked unavailable
        for p in service.providers.values():
            if p.provider != LLMProvider.TEMPLATE:
                p.available = False

        # Attempt chat
        response = await service.chat("Help me with my homework")

        # Verify Fallback
        assert response.provider == LLMProvider.TEMPLATE
        assert response.model == "template-v1"
        # Check for helpful "fail soft" message
        assert "template mode" in response.content.lower() or "offline mode" in response.content.lower()

@pytest.mark.asyncio
async def test_ralph_wiggum_self_awareness():
    """
    Principle: AI Output Must Be Self-Aware of Uncertainty.
    Scenario: System prompts generation logic.
    Expectation:
        - If model is confirmed by API (e.g. OpenAI returns 'gpt-4-0613'), system prompts says "The confirmed model is...".
        - If model is configured but not confirmed, system prompts says "The configured model is...".
        - If model is completely unknown, system prompts says "The exact model version is not confirmed".
        - Prevents "False Authority Syndrome".
    """
    service = MultiTierLLMService()

    # Case 1: Unconfirmed but Configured - AI should admit uncertainty about ACTUAL routing
    prompt_unconfirmed = service.get_system_prompt(LLMProvider.OLLAMA, "llama3", model_confirmed=False)
    assert "The configured model is: llama3" in prompt_unconfirmed
    assert "actual model may vary based on API routing" in prompt_unconfirmed

    # Case 2: Completely Unknown (No model info) - AI should admit total ignorance
    prompt_unknown = service.get_system_prompt(LLMProvider.OLLAMA, model=None, model_confirmed=False)
    assert "exact model version is not confirmed" in prompt_unknown

    # Case 3: Confirmed (API response) - AI can be confident
    prompt_confirmed = service.get_system_prompt(LLMProvider.OPENAI, "gpt-4o", model_confirmed=True)
    assert "The confirmed model is: gpt-4o" in prompt_confirmed

@pytest.mark.asyncio
async def test_ralph_wiggum_naive_input_handling():
    """
    Principle: Assume Incorrect or Naive User Inputs.
    Scenario: User sends nonsensical Ralph Wiggum quote.
    Expectation: System handles it without crashing and provides a safe default response.
    Ralph quote: "Me fail English? That's unpossible!"
    """
    service = MultiTierLLMService()

    nonsense_input = "Me fail English? That's unpossible!"

    # We force the TEMPLATE provider to test the "safety net" logic
    # (since mocking a real LLM would just test the mock)
    response = await service.chat(
        nonsense_input,
        preferred_provider=LLMProvider.TEMPLATE
    )

    assert response.provider == LLMProvider.TEMPLATE
    # The default template response echoes back part of the input (showing it received it)
    # and explains status (showing it didn't crash)
    # Note: Template response converts input to lower case
    assert "me fail english" in response.content.lower()
    assert "template mode" in response.content

@pytest.mark.asyncio
async def test_ralph_wiggum_guardrails_identity():
    """
    Principle: Guardrails Against Over-Interpretation / Hallucination.
    Scenario: Check that the System Prompt explicitly forbids impersonation.
    Expectation: The prompt contains strict identity rules.
    Ralph quote: "I'm a brick!" (AI shouldn't say this)
    """
    service = MultiTierLLMService()
    prompt = service.SYSTEM_PROMPT_TEMPLATE

    # Verify strict identity rules exist in the core prompt
    assert "YOUR IDENTITY (CRITICAL - ALWAYS ACCURATE)" in prompt
    assert "You are Veena, NOT the underlying model directly" in prompt
    assert "NEVER claim to be a model you are not certain about" in prompt
    assert "NEVER say you are \"GPT-4\"" in prompt
