from types import SimpleNamespace

import pytest

from app.modules.ai.services.tool_search_handlers import (
    SearchHandlerSharedContext,
    handle_search,
)


@pytest.mark.asyncio
async def test_search_trials_reports_database_total_not_page_size():
    class FakeTrialSearchService:
        async def search(self, **kwargs):
            assert kwargs["limit"] == 20
            assert kwargs["offset"] == 0
            return [{"id": str(i), "name": f"Trial {i}"} for i in range(1, 21)]

        async def count(self, **kwargs):
            assert kwargs["organization_id"] == 2
            assert kwargs["status"] == "active"
            return 142

    executor = SimpleNamespace(
        db=SimpleNamespace(),
        trial_search_service=FakeTrialSearchService(),
    )

    result = await handle_search(
        executor,
        "search_trials",
        {"organization_id": 2, "status": "active"},
        shared=SearchHandlerSharedContext(
            seedlot_search_service=SimpleNamespace(),
            program_search_service=SimpleNamespace(),
            trait_search_service=SimpleNamespace(),
        ),
        logger=SimpleNamespace(error=lambda *args, **kwargs: None),
    )

    assert result["data"]["total"] == 142
    assert result["data"]["returned"] == 20
    assert result["data"]["has_more"] is True
    assert result["data"]["limit"] == 20
    assert result["data"]["offset"] == 0
    assert result["data"]["page"] == 1
    assert result["data"]["next_page"] == 2
    assert result["data"]["message"].startswith("There are 142 active trials in the accessible database.")
    assert "Here are records 1-20" in result["data"]["message"]
    assert "Trial 1" in result["data"]["message"]
    assert "Ask for 'active trials page 2'" in result["data"]["message"]


@pytest.mark.asyncio
async def test_search_trials_count_request_returns_summary_without_preview():
    class FakeTrialSearchService:
        async def search(self, **kwargs):
            return [{"id": str(i), "name": f"Trial {i}"} for i in range(1, 21)]

        async def count(self, **kwargs):
            return 142

    executor = SimpleNamespace(
        db=SimpleNamespace(),
        trial_search_service=FakeTrialSearchService(),
    )

    result = await handle_search(
        executor,
        "search_trials",
        {"organization_id": 2, "status": "active", "summary_only": True},
        shared=SearchHandlerSharedContext(
            seedlot_search_service=SimpleNamespace(),
            program_search_service=SimpleNamespace(),
            trait_search_service=SimpleNamespace(),
        ),
        logger=SimpleNamespace(error=lambda *args, **kwargs: None),
    )

    assert result["data"]["message"] == "There are 142 active trials in the accessible database."
    assert "Trial 1" not in result["data"]["message"]


@pytest.mark.asyncio
async def test_search_trials_supports_explicit_result_pages():
    class FakeTrialSearchService:
        async def search(self, **kwargs):
            assert kwargs["limit"] == 20
            assert kwargs["offset"] == 20
            return [{"id": str(i), "name": f"Trial {i}"} for i in range(21, 41)]

        async def count(self, **kwargs):
            return 142

    executor = SimpleNamespace(
        db=SimpleNamespace(),
        trial_search_service=FakeTrialSearchService(),
    )

    result = await handle_search(
        executor,
        "search_trials",
        {"organization_id": 2, "status": "active", "page": 2},
        shared=SearchHandlerSharedContext(
            seedlot_search_service=SimpleNamespace(),
            program_search_service=SimpleNamespace(),
            trait_search_service=SimpleNamespace(),
        ),
        logger=SimpleNamespace(error=lambda *args, **kwargs: None),
    )

    assert result["data"]["offset"] == 20
    assert result["data"]["page"] == 2
    assert result["data"]["next_page"] == 3
    assert "Here are records 21-40" in result["data"]["message"]
