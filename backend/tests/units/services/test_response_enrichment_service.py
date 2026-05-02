"""
Unit tests for ResponseEnrichmentService.

Example-based tests covering passthrough, enrichment, evidence envelope,
failure fallback, partial failure, boundary conditions, and empty/failed results.

Requirements: 1.5, 1.6, 2.4, 2.5, 3.5, 4.4, 5.2, 5.4, 6.2, 6.3, 7.2, 7.3
"""

from __future__ import annotations

import copy
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.ai.services.response_enrichment_service import ResponseEnrichmentService
from app.schemas.reevu_envelope import EvidenceRef


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MODULE = "app.modules.ai.services.response_enrichment_service"


def _make_search_result(function_name: str, items: list[dict], message: str | None = None) -> dict:
    return {
        "success": True,
        "function": function_name,
        "result_type": "trial_list" if "trial" in function_name else "germplasm_list",
        "data": {
            "total": len(items),
            "items": items,
            "message": message or f"Found {len(items)} items",
        },
        "demo": False,
    }


def _trial_item(tid: int, name: str) -> dict:
    return {
        "id": tid,
        "name": name,
        "crop": "Wheat",
        "program": "Breeding Program A",
        "location": "Field Station 1",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "study_count": 3,
    }


def _germplasm_item(gid: int, name: str) -> dict:
    return {
        "id": gid,
        "name": name,
        "accession": f"ACC-{gid}",
        "species": "Triticum aestivum",
        "origin": "India",
    }


def _evidence_ref(domain: str, function_name: str) -> EvidenceRef:
    return EvidenceRef(
        source_type="database",
        entity_id=f"enrichment:{domain}:{function_name}",
        query_or_method=f"Batch {domain} for 2 items",
    )


# ---------------------------------------------------------------------------
# Mock return values for trial helpers
# ---------------------------------------------------------------------------

def _mock_trial_obs_counts():
    """observation counts for trial ids 1, 2"""
    return {1: 150, 2: 80}, _evidence_ref("trial_observation_counts", "search_trials")


def _mock_trial_germ_counts():
    """germplasm counts + latest dates for trial ids 1, 2"""
    return (
        {
            1: {"germplasm_count": 12, "latest_observation_date": "2025-06-15"},
            2: {"germplasm_count": 8, "latest_observation_date": "2025-05-20"},
        },
        _evidence_ref("trial_germplasm_counts_and_dates", "search_trials"),
    )


def _mock_trial_traits():
    """primary traits for trial ids 1, 2"""
    return (
        {1: ["Yield", "Height", "Maturity"], 2: ["Yield", "Protein"]},
        _evidence_ref("trial_primary_traits", "search_trials"),
    )


# ---------------------------------------------------------------------------
# Mock return values for germplasm helpers
# ---------------------------------------------------------------------------

def _mock_germ_obs_counts():
    return {10: 200, 20: 50}, _evidence_ref("germplasm_observation_counts", "search_germplasm")


def _mock_germ_trial_participation():
    return {10: 5, 20: 2}, _evidence_ref("germplasm_trial_participation", "search_germplasm")


def _mock_germ_key_traits():
    return (
        {
            10: [{"name": "Yield", "value": "4.5"}, {"name": "Height", "value": "95cm"}],
            20: [{"name": "Protein", "value": "12%"}],
        },
        _evidence_ref("germplasm_key_traits", "search_germplasm"),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestResponseEnrichmentService:
    """Example-based unit tests for ResponseEnrichmentService.enrich()."""

    async def test_unsupported_function_passthrough(self):
        """Unsupported function names return the exact same object (identity check)."""
        db = AsyncMock()
        result = {"success": True, "data": {"total": 1, "items": [{"id": 1}], "message": "ok"}}
        returned = await ResponseEnrichmentService.enrich("search_locations", result, db, 1)
        assert returned is result

    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    async def test_trial_enrichment_replaces_message(
        self, mock_obs, mock_germ, mock_traits
    ):
        """Trial enrichment replaces data.message with structured markdown."""
        mock_obs.return_value = _mock_trial_obs_counts()
        mock_germ.return_value = _mock_trial_germ_counts()
        mock_traits.return_value = _mock_trial_traits()

        items = [_trial_item(1, "Trial A"), _trial_item(2, "Trial B")]
        result = _make_search_result("search_trials", items, "Found 2 trials")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        msg = enriched["data"]["message"]
        assert msg.startswith("## Found 2 trials")
        assert "### Trial A" in msg
        assert "### Trial B" in msg

    @patch(f"{_MODULE}._query_germplasm_key_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_germplasm_trial_participation", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_germplasm_observation_counts", new_callable=AsyncMock)
    async def test_germplasm_enrichment_replaces_message(
        self, mock_obs, mock_trials, mock_traits
    ):
        """Germplasm enrichment replaces data.message with structured markdown."""
        mock_obs.return_value = _mock_germ_obs_counts()
        mock_trials.return_value = _mock_germ_trial_participation()
        mock_traits.return_value = _mock_germ_key_traits()

        items = [_germplasm_item(10, "Germ A"), _germplasm_item(20, "Germ B")]
        result = _make_search_result("search_germplasm", items, "Found 2 germplasm")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_germplasm", result, db, 1)

        msg = enriched["data"]["message"]
        assert msg.startswith("## Found 2 germplasm records")
        assert "### Germ A" in msg
        assert "### Germ B" in msg


    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    async def test_evidence_key_attached(self, mock_obs, mock_germ, mock_traits):
        """After enrichment, result['evidence'] exists with evidence_refs list."""
        mock_obs.return_value = _mock_trial_obs_counts()
        mock_germ.return_value = _mock_trial_germ_counts()
        mock_traits.return_value = _mock_trial_traits()

        items = [_trial_item(1, "Trial A"), _trial_item(2, "Trial B")]
        result = _make_search_result("search_trials", items, "Found 2 trials")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        assert "evidence" in enriched
        evidence = enriched["evidence"]
        assert "evidence_refs" in evidence
        assert len(evidence["evidence_refs"]) == 3  # one per domain query

    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    async def test_all_domains_fail_returns_original(self, mock_obs, mock_germ, mock_traits):
        """When all 3 domain queries raise, the original terse message is preserved."""
        mock_obs.side_effect = Exception("db down")
        mock_germ.side_effect = Exception("db down")
        mock_traits.side_effect = Exception("db down")

        items = [_trial_item(1, "Trial A"), _trial_item(2, "Trial B")]
        result = _make_search_result("search_trials", items, "Found 2 trials")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        assert enriched["data"]["message"] == "Found 2 trials"
        assert "evidence" not in enriched

    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    async def test_partial_domain_failure(self, mock_obs, mock_germ, mock_traits):
        """When 1 helper raises and 2 succeed, message is enriched and missing_evidence_signals has 1 entry."""
        mock_obs.return_value = _mock_trial_obs_counts()
        mock_germ.side_effect = Exception("timeout")
        mock_traits.return_value = _mock_trial_traits()

        items = [_trial_item(1, "Trial A"), _trial_item(2, "Trial B")]
        result = _make_search_result("search_trials", items, "Found 2 trials")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        # Message should be enriched (not the original terse message)
        msg = enriched["data"]["message"]
        assert msg.startswith("## Found 2 trials")

        # Evidence envelope should track the missing domain
        evidence = enriched["evidence"]
        assert len(evidence["missing_evidence_signals"]) == 1
        assert "germplasm_counts_and_dates" in evidence["missing_evidence_signals"][0]

    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    async def test_max_items_boundary(self, mock_obs, mock_germ, mock_traits):
        """Pass 25 items — enrichment still works and data.total is 25."""
        # Return counts for all 25 ids
        all_counts = {i: 10 for i in range(1, 26)}
        all_germ = {i: {"germplasm_count": 5, "latest_observation_date": None} for i in range(1, 26)}
        all_traits = {i: ["Yield"] for i in range(1, 26)}

        mock_obs.return_value = (all_counts, _evidence_ref("trial_observation_counts", "search_trials"))
        mock_germ.return_value = (all_germ, _evidence_ref("trial_germplasm_counts_and_dates", "search_trials"))
        mock_traits.return_value = (all_traits, _evidence_ref("trial_primary_traits", "search_trials"))

        items = [_trial_item(i, f"Trial {i}") for i in range(1, 26)]
        result = _make_search_result("search_trials", items, "Found 25 trials")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        assert enriched["data"]["total"] == 25
        # Should not crash — message should be enriched
        assert enriched["data"]["message"].startswith("## Found 25 trials")

    async def test_empty_items_returns_unchanged(self):
        """Result with items: [] is returned unchanged."""
        db = AsyncMock()
        result = _make_search_result("search_trials", [], "Found 0 trials")
        original_msg = result["data"]["message"]

        returned = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        assert returned["data"]["message"] == original_msg

    async def test_failed_result_returns_unchanged(self):
        """Result with success: False is returned unchanged."""
        db = AsyncMock()
        result = {
            "success": False,
            "function": "search_trials",
            "data": {"total": 0, "items": [], "message": "Search failed"},
            "demo": False,
        }
        original = copy.deepcopy(result)

        returned = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        assert returned["data"]["message"] == original["data"]["message"]
