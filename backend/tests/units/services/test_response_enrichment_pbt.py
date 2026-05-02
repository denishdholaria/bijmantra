"""
Property-based tests for ResponseEnrichmentService.

Uses Hypothesis to validate correctness properties from the design spec.
Each test maps to a numbered property in the design document.

Feature: reevu-response-enrichment
"""

from __future__ import annotations

import copy
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.modules.ai.services.response_enrichment_service import ResponseEnrichmentService
from app.schemas.reevu_envelope import EvidenceRef


_MODULE = "app.modules.ai.services.response_enrichment_service"

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_id_st = st.integers(min_value=1, max_value=10000)
_count_st = st.integers(min_value=0, max_value=100000)
_trait_name_st = st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N")))
_date_st = st.one_of(st.none(), st.from_regex(r"20\d{2}-\d{2}-\d{2}", fullmatch=True))
_value_st = st.one_of(st.none(), st.text(min_size=1, max_size=20))


def _trial_item_st():
    return st.fixed_dictionaries({
        "id": _id_st,
        "name": st.text(min_size=1, max_size=50),
        "crop": st.one_of(st.none(), st.text(min_size=1, max_size=20)),
        "program": st.one_of(st.none(), st.text(min_size=1, max_size=20)),
        "location": st.one_of(st.none(), st.text(min_size=1, max_size=30)),
        "start_date": _date_st,
        "end_date": _date_st,
        "study_count": st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    })


def _germplasm_item_st():
    return st.fixed_dictionaries({
        "id": _id_st,
        "name": st.text(min_size=1, max_size=50),
        "accession": st.one_of(st.none(), st.text(min_size=1, max_size=20)),
        "species": st.one_of(st.none(), st.text(min_size=1, max_size=30)),
        "origin": st.one_of(st.none(), st.text(min_size=1, max_size=30)),
    })


def _trial_enrichment_map_st(trial_ids):
    """Build an enrichment map for given trial IDs."""
    entries = {}
    for tid in trial_ids:
        entries[tid] = {
            "observation_count": 0,
            "germplasm_count": 0,
            "latest_observation_date": None,
            "primary_traits": [],
        }
    return entries


def _germplasm_enrichment_map_st(germplasm_ids):
    entries = {}
    for gid in germplasm_ids:
        entries[gid] = {
            "observation_count": 0,
            "trial_count": 0,
            "key_traits": [],
        }
    return entries


def _make_evidence_ref(domain: str, fn: str) -> EvidenceRef:
    return EvidenceRef(
        source_type="database",
        entity_id=f"enrichment:{domain}:{fn}",
        query_or_method=f"Batch {domain} for test",
    )


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


# ---------------------------------------------------------------------------
# Property 3: Summary header contains count and search context
# ---------------------------------------------------------------------------


class TestProperty3SummaryHeader:
    """Feature: reevu-response-enrichment, Property 3: Summary header contains count and search context"""

    @given(
        total=st.integers(min_value=0, max_value=1000),
        context=st.text(min_size=0, max_size=50),
    )
    @settings(max_examples=100)
    def test_trial_summary_header(self, total, context):
        items = [{"id": i, "name": f"T{i}"} for i in range(min(total, 5))]
        enrichment = {item["id"]: {"observation_count": 0} for item in items}
        summary = ResponseEnrichmentService._build_trial_summary(items, enrichment, total, context)
        assert summary.startswith(f"## Found {total} trials")
        if context:
            assert context in summary

    @given(
        total=st.integers(min_value=0, max_value=1000),
        context=st.text(min_size=0, max_size=50),
    )
    @settings(max_examples=100)
    def test_germplasm_summary_header(self, total, context):
        items = [{"id": i, "name": f"G{i}"} for i in range(min(total, 5))]
        enrichment = {item["id"]: {"observation_count": 0} for item in items}
        summary = ResponseEnrichmentService._build_germplasm_summary(items, enrichment, total, context)
        assert summary.startswith(f"## Found {total} germplasm records")
        if context:
            assert context in summary


# ---------------------------------------------------------------------------
# Property 4: Summary per-item sections contain all required fields
# ---------------------------------------------------------------------------


class TestProperty4SummarySections:
    """Feature: reevu-response-enrichment, Property 4: Summary per-item sections contain all required fields"""

    @given(item=_trial_item_st())
    @settings(max_examples=100)
    def test_trial_section_fields(self, item):
        enrichment = {
            item["id"]: {
                "observation_count": 42,
                "germplasm_count": 10,
                "latest_observation_date": "2025-06-01",
                "primary_traits": ["Yield", "Height"],
            }
        }
        summary = ResponseEnrichmentService._build_trial_summary([item], enrichment, 1, "")
        name = item["name"] or "\u2014"
        assert f"### {name}" in summary
        assert "**Crop:**" in summary
        assert "**Program:**" in summary
        assert "**Location:**" in summary
        assert "**Date range:**" in summary
        assert "**Studies:**" in summary
        assert "**Observations:**" in summary
        assert "**Germplasm entries:**" in summary
        assert "**Latest observation:**" in summary
        assert "**Primary traits:**" in summary

    @given(item=_germplasm_item_st())
    @settings(max_examples=100)
    def test_germplasm_section_fields(self, item):
        enrichment = {
            item["id"]: {
                "observation_count": 30,
                "trial_count": 3,
                "key_traits": [{"name": "Yield", "value": "4.5"}],
            }
        }
        summary = ResponseEnrichmentService._build_germplasm_summary([item], enrichment, 1, "")
        name = item["name"] or "\u2014"
        assert f"### {name}" in summary
        assert "**Accession:**" in summary
        assert "**Species:**" in summary
        assert "**Origin:**" in summary
        assert "**Observations:**" in summary
        assert "**Trial participation:**" in summary
        assert "**Key traits:**" in summary


# ---------------------------------------------------------------------------
# Property 5: Summary builder is deterministic (idempotent output)
# ---------------------------------------------------------------------------


class TestProperty5SummaryDeterminism:
    """Feature: reevu-response-enrichment, Property 5: Summary builder is deterministic"""

    @given(items=st.lists(_trial_item_st(), min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_trial_summary_idempotent(self, items):
        # Deduplicate IDs
        seen = set()
        unique_items = []
        for item in items:
            if item["id"] not in seen:
                seen.add(item["id"])
                unique_items.append(item)
        items = unique_items

        enrichment = {item["id"]: {"observation_count": 10} for item in items}
        s1 = ResponseEnrichmentService._build_trial_summary(items, enrichment, len(items), "test")
        s2 = ResponseEnrichmentService._build_trial_summary(items, enrichment, len(items), "test")
        assert s1 == s2

    @given(items=st.lists(_germplasm_item_st(), min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_germplasm_summary_idempotent(self, items):
        seen = set()
        unique_items = []
        for item in items:
            if item["id"] not in seen:
                seen.add(item["id"])
                unique_items.append(item)
        items = unique_items

        enrichment = {item["id"]: {"observation_count": 5} for item in items}
        s1 = ResponseEnrichmentService._build_germplasm_summary(items, enrichment, len(items), "ctx")
        s2 = ResponseEnrichmentService._build_germplasm_summary(items, enrichment, len(items), "ctx")
        assert s1 == s2


# ---------------------------------------------------------------------------
# Property 6: Evidence envelope contains one ref per successful query
# ---------------------------------------------------------------------------


class TestProperty6EvidenceEnvelope:
    """Feature: reevu-response-enrichment, Property 6: Evidence envelope correctness"""

    @given(k=st.integers(min_value=0, max_value=3))
    @settings(max_examples=100)
    def test_envelope_ref_count(self, k):
        refs = [_make_evidence_ref(f"domain_{i}", "search_trials") for i in range(k)]
        signals = [f"domain_{i}: failed" for i in range(3 - k)]
        envelope = ResponseEnrichmentService._build_evidence_envelope(refs, signals)
        assert len(envelope.evidence_refs) == k
        for ref in envelope.evidence_refs:
            assert ref.source_type == "database"
            assert ref.entity_id
            assert ref.query_or_method
            assert ref.retrieved_at

    @given(k=st.integers(min_value=0, max_value=3))
    @settings(max_examples=100)
    def test_envelope_missing_signals(self, k):
        refs = [_make_evidence_ref(f"d{i}", "fn") for i in range(3 - k)]
        signals = [f"domain_{i}: error" for i in range(k)]
        envelope = ResponseEnrichmentService._build_evidence_envelope(refs, signals)
        assert len(envelope.missing_evidence_signals) == k
        assert envelope.uncertainty.missing_data == signals


# ---------------------------------------------------------------------------
# Property 7: Safe-failure domain isolation
# ---------------------------------------------------------------------------


class TestProperty7SafeFailure:
    """Feature: reevu-response-enrichment, Property 7: Safe-failure domain isolation"""

    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    async def test_one_domain_fails_others_succeed(self, mock_obs, mock_germ, mock_traits):
        """When exactly one domain fails, the other two still produce correct enrichment."""
        mock_obs.return_value = ({1: 100}, _make_evidence_ref("obs", "search_trials"))
        mock_germ.side_effect = Exception("db error")
        mock_traits.return_value = ({1: ["Yield"]}, _make_evidence_ref("traits", "search_trials"))

        items = [{"id": 1, "name": "Trial A"}]
        result = _make_search_result("search_trials", items, "Found 1 trials")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        msg = enriched["data"]["message"]
        assert "### Trial A" in msg
        assert "100" in msg  # observation count from domain 1
        evidence = enriched["evidence"]
        assert len(evidence["missing_evidence_signals"]) == 1


# ---------------------------------------------------------------------------
# Property 8: Missing evidence signals track failed domains
# ---------------------------------------------------------------------------


class TestProperty8MissingSignals:
    """Feature: reevu-response-enrichment, Property 8: Missing evidence signals track failed domains"""

    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    async def test_two_domains_fail(self, mock_obs, mock_germ, mock_traits):
        mock_obs.side_effect = Exception("fail1")
        mock_germ.side_effect = Exception("fail2")
        mock_traits.return_value = ({1: ["Yield"]}, _make_evidence_ref("traits", "search_trials"))

        items = [{"id": 1, "name": "T"}]
        result = _make_search_result("search_trials", items, "Found 1 trials")
        db = AsyncMock()

        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        evidence = enriched["evidence"]
        assert len(evidence["missing_evidence_signals"]) == 2
        signal_text = " ".join(evidence["missing_evidence_signals"])
        assert "observation_counts" in signal_text
        assert "germplasm_counts_and_dates" in signal_text


# ---------------------------------------------------------------------------
# Property 9: Enrichment preserves all non-message fields
# ---------------------------------------------------------------------------


class TestProperty9FieldPreservation:
    """Feature: reevu-response-enrichment, Property 9: Enrichment preserves all non-message fields"""

    @patch(f"{_MODULE}._query_trial_primary_traits", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_germplasm_counts_and_dates", new_callable=AsyncMock)
    @patch(f"{_MODULE}._query_trial_observation_counts", new_callable=AsyncMock)
    @given(extra_key=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("L",))))
    @settings(max_examples=50)
    async def test_extra_fields_preserved(self, mock_obs, mock_germ, mock_traits, extra_key):
        assume(extra_key not in ("total", "items", "message", "search_context"))

        mock_obs.return_value = ({1: 10}, _make_evidence_ref("obs", "search_trials"))
        mock_germ.return_value = ({1: {"germplasm_count": 5, "latest_observation_date": None}}, _make_evidence_ref("germ", "search_trials"))
        mock_traits.return_value = ({1: ["Yield"]}, _make_evidence_ref("traits", "search_trials"))

        items = [{"id": 1, "name": "T1"}]
        result = _make_search_result("search_trials", items, "Found 1 trials")
        result["data"][extra_key] = "preserved_value"
        result["custom_top_level"] = "also_preserved"
        original_items = copy.deepcopy(result["data"]["items"])
        original_total = result["data"]["total"]

        db = AsyncMock()
        enriched = await ResponseEnrichmentService.enrich("search_trials", result, db, 1)

        assert enriched["data"][extra_key] == "preserved_value"
        assert enriched["custom_top_level"] == "also_preserved"
        assert enriched["data"]["items"] == original_items
        assert enriched["data"]["total"] == original_total


# ---------------------------------------------------------------------------
# Property 10: Unsupported function names pass through unchanged
# ---------------------------------------------------------------------------


class TestProperty10Passthrough:
    """Feature: reevu-response-enrichment, Property 10: Unsupported function names pass through unchanged"""

    @given(fn_name=st.text(min_size=1, max_size=30).filter(lambda x: x not in ("search_trials", "search_germplasm")))
    @settings(max_examples=100)
    async def test_unsupported_passthrough(self, fn_name):
        result = {"success": True, "data": {"total": 1, "items": [{"id": 1}], "message": "ok"}, "extra": 42}
        db = AsyncMock()
        returned = await ResponseEnrichmentService.enrich(fn_name, result, db, 1)
        assert returned is result
