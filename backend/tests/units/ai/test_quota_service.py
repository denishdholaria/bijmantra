from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.ai.services.quota import AIQuotaService


@pytest.mark.asyncio
async def test_get_usage_stats_returns_richer_snapshot_with_soft_alerts():
    usage_record = SimpleNamespace(
        request_count=42,
        token_count_input=2100,
        token_count_output=540,
    )
    organization = SimpleNamespace(ai_daily_limit=50)
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                SimpleNamespace(scalar_one_or_none=lambda: usage_record),
                SimpleNamespace(scalar_one_or_none=lambda: organization),
            ]
        )
    )

    stats = await AIQuotaService.get_usage_stats(
        db,
        7,
        provider_status={
            "active_provider": "openai",
            "active_model": "gpt-4.1-mini",
            "active_provider_source": "organization_config",
            "active_provider_source_label": "Organization AI settings",
        },
    )

    assert stats["used"] == 42
    assert stats["limit"] == 50
    assert stats["remaining"] == 8
    assert stats["quota_authority"] == "request_count"
    assert stats["provider"]["active_provider"] == "openai"
    assert stats["token_telemetry"]["total_tokens"] == 2640
    assert stats["token_telemetry"]["coverage_state"] == "supplemental"
    assert stats["soft_alert"]["state"] == "watch"
    assert stats["attribution"]["mission"]["supported"] is False


@pytest.mark.asyncio
async def test_record_generation_usage_updates_existing_daily_row():
    usage_record = SimpleNamespace(token_count_input=2100, token_count_output=540)
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(scalar_one_or_none=lambda: usage_record)
        ),
        add=MagicMock(),
        commit=AsyncMock(),
    )

    await AIQuotaService.record_generation_usage(
        db,
        7,
        tokens_input=120,
        tokens_output=45,
    )

    assert usage_record.token_count_input == 2220
    assert usage_record.token_count_output == 585
    db.add.assert_called_once_with(usage_record)
    db.commit.assert_awaited_once()