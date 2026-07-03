from unittest.mock import AsyncMock

import pytest

from app.modules.ai.services.devguru_service import DevGuruService


@pytest.mark.asyncio
async def test_explain_concept_threads_identity_to_llm_generate(monkeypatch: pytest.MonkeyPatch) -> None:
    service = DevGuruService(db=AsyncMock())
    generate = AsyncMock(return_value=type("Response", (), {"content": "answer", "provider": type("Provider", (), {"value": "groq"})()})())
    llm_service = type("LLMService", (), {"generate": generate})()

    monkeypatch.setattr("app.modules.ai.services.devguru_service.get_llm_service", lambda: llm_service)

    result = await service.explain_concept("genomic selection", organization_id=11, user_id=29)

    assert result["explanation"] == "answer"
    generate.assert_awaited_once()
    assert generate.await_args.kwargs["organization_id"] == 11
    assert generate.await_args.kwargs["user_id"] == 29