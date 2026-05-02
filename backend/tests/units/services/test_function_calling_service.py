import pytest
from hypothesis import given, strategies as st

from app.modules.ai.services.function_calling_service import (
    ClarificationResponse,
    FunctionCallingService,
)
from app.modules.ai.services.reevu.synonym_config import (
    CROP_NAMES,
    QUALIFIER_TERMS,
    SYNONYM_GROUPS,
    TEMPORAL_PATTERNS,
    SynonymExpander,
)


_CROP_ALIAS_CASES = [
    (canonical, canonical)
    for canonical in CROP_NAMES
] + [
    (alias, canonical)
    for canonical, aliases in CROP_NAMES.items()
    for alias in aliases
]


class _MockFunctionGemmaResponse:
    def __init__(self, generated_text: str):
        self.status_code = 200
        self._generated_text = generated_text

    def json(self):
        return [{"generated_text": self._generated_text}]


class _MockFunctionGemmaClient:
    def __init__(self, generated_text: str):
        self._generated_text = generated_text

    async def post(self, *args, **kwargs):
        return _MockFunctionGemmaResponse(self._generated_text)


def test_pattern_detection_routes_trial_summary_requests_to_get_trial_results():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Show trial summary for trial TRIAL-22")

    assert function_call is not None
    assert function_call.name == "get_trial_results"
    assert function_call.parameters == {"trial_id": "TRIAL-22"}


def test_pattern_detection_uses_query_when_trial_summary_lacks_explicit_identifier():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Who were the top performers in the trial summary?")

    assert function_call is not None
    assert function_call.name == "get_trial_results"
    assert function_call.parameters == {"query": "Who were the top performers in the trial summary?"}


def test_pattern_detection_routes_trial_ranking_requests_to_get_trial_results():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Show ranking for trial TRIAL-22 by yield")

    assert function_call is not None
    assert function_call.name == "get_trial_results"
    assert function_call.parameters == {"trial_id": "TRIAL-22"}


def test_pattern_detection_routes_germplasm_detail_requests_to_get_germplasm_details():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Show details for germplasm IR64")

    assert function_call is not None
    assert function_call.name == "get_germplasm_details"
    assert function_call.parameters == {"query": "IR64"}


def test_pattern_detection_routes_numeric_germplasm_context_to_get_germplasm_details():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Show details for germplasm id 12345")

    assert function_call is not None
    assert function_call.name == "get_germplasm_details"
    assert function_call.parameters == {"germplasm_id": "12345"}


def test_pattern_detection_routes_trait_summary_requests_to_get_trait_summary():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Show trait summary statistics for IR64 and Swarna")

    assert function_call is not None
    assert function_call.name == "get_trait_summary"
    assert function_call.parameters == {"germplasm_ids": ["IR64", "Swarna"]}


def test_pattern_detection_routes_trait_summary_benchmark_prompt_to_get_trait_summary():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Summarize yield and disease resistance traits for IR64")

    assert function_call is not None
    assert function_call.name == "get_trait_summary"
    assert function_call.parameters == {"germplasm_ids": ["IR64"]}


def test_pattern_detection_routes_marker_association_requests_to_get_marker_associations():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Find SNP markers linked to blast resistance")

    assert function_call is not None
    assert function_call.name == "get_marker_associations"
    assert function_call.parameters == {"query": "blast resistance"}


def test_pattern_detection_strips_crop_context_from_marker_association_trait_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "What markers are associated with blast resistance in rice?"
    )

    assert function_call is not None
    assert function_call.name == "get_marker_associations"
    assert function_call.parameters == {"query": "blast resistance"}


def test_pattern_detection_routes_compound_breeding_trial_weather_requests_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Which wheat varieties performed best in trials at Ludhiana under current weather?"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["crop"] == "wheat"
    assert function_call.parameters["location"] == "Ludhiana"


def test_pattern_detection_routes_compound_trial_phenotype_environment_requests_to_observations():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Show phenotype observations from trials at Ludhiana under current weather"
    )

    assert function_call is not None
    assert function_call.name == "get_observations"
    assert function_call.parameters["location"] == "Ludhiana"


def test_pattern_detection_routes_observation_requests_to_get_observations():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("List plant height observation data")

    assert function_call is not None
    assert function_call.name == "get_observations"
    assert function_call.parameters["trait"] == "plant height"
    assert function_call.parameters["query"] == "List plant height observation data"


def test_pattern_detection_routes_trait_distribution_requests_to_get_trait_distribution():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "What is the distribution of plant height observations?"
    )

    assert function_call is not None
    assert function_call.name == "get_trait_distribution"
    assert function_call.parameters["trait"] == "plant height"
    assert function_call.parameters["query"] == (
        "What is the distribution of plant height observations?"
    )


def test_pattern_detection_routes_seed_inventory_requests_to_get_seed_inventory():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("How much seed inventory is available for IR64?")

    assert function_call is not None
    assert function_call.name == "get_seed_inventory"
    assert function_call.parameters["query"] == "How much seed inventory is available for IR64?"


def test_pattern_detection_routes_seedlot_search_requests_to_search_seedlots():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Find seed lots in Vault A")

    assert function_call is not None
    assert function_call.name == "search_seedlots"
    assert function_call.parameters["query"] == "Find seed lots in Vault A"


def test_pattern_detection_routes_field_info_requests_to_get_field_info():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Show field details for Ludhiana")

    assert function_call is not None
    assert function_call.name == "get_field_info"
    assert function_call.parameters["query"] == "Show field details for Ludhiana"
    assert function_call.parameters["location"] == "Ludhiana"


def test_pattern_detection_routes_crop_calendar_requests_to_get_crop_calendar():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("What is the crop calendar for wheat?")

    assert function_call is not None
    assert function_call.name == "get_crop_calendar"
    assert function_call.parameters["query"] == "What is the crop calendar for wheat?"
    assert function_call.parameters["crop"] == "wheat"


def test_pattern_detection_routes_location_search_requests_to_search_locations():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns("Find locations in Hyderabad")

    assert function_call is not None
    assert function_call.name == "search_locations"
    assert function_call.parameters["query"] == "Find locations in Hyderabad"


def test_pattern_detection_routes_compound_breeding_trial_requests_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Which wheat varieties performed best in trials at Ludhiana?"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["crop"] == "wheat"
    assert function_call.parameters["location"] == "Ludhiana"


def test_pattern_detection_routes_drought_tolerance_trial_comparison_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Compare breeding lines with the latest trial results for drought tolerance"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["trait"] == "drought tolerance"
    assert "location" not in function_call.parameters


def test_pattern_detection_routes_trial_top_performer_prompt_to_get_trial_results():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Which entry was the top performer in our wheat trial this season?"
    )

    assert function_call is not None
    assert function_call.name == "get_trial_results"
    assert function_call.parameters == {"query": "wheat trial", "crop": "wheat"}


def test_pattern_detection_prefers_specific_trial_phrase_over_generic_action_phrase():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Show trial results for the Ludhiana advanced yield trial this season"
    )

    assert function_call is not None
    assert function_call.name == "get_trial_results"
    assert function_call.parameters == {
        "query": "Ludhiana advanced yield trial",
        "location": "Ludhiana",
    }


def test_pattern_detection_routes_ambiguous_trial_prompt_to_get_trial_results():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Show the results for the Punjab wheat trial because I cannot remember the exact trial name"
    )

    assert function_call is not None
    assert function_call.name == "get_trial_results"
    assert function_call.parameters == {"query": "Punjab wheat trial", "crop": "wheat"}


def test_pattern_detection_routes_compound_breeding_genomics_requests_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Which rice varieties have blast resistance markers?"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["crop"] == "rice"
    assert function_call.parameters["trait"] == "blast resistance"


def test_pattern_detection_routes_germplasm_trait_protocol_requests_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Which rice germplasm support yield improvement under speed breeding protocols?"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["crop"] == "rice"
    assert function_call.parameters["trait"] == "yield"
    assert "germplasm" not in function_call.parameters


def test_pattern_detection_ignores_conjunction_after_germplasm_in_protocol_recommendation():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Recommend the best germplasm and supporting speed-breeding protocol for blast resistance improvement"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["trait"] == "blast resistance"
    assert "germplasm" not in function_call.parameters


def test_pattern_detection_routes_multi_domain_recommendation_requests_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Recommend a wheat variety from trials at Ludhiana under current weather"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["crop"] == "wheat"
    assert function_call.parameters["location"] == "Ludhiana"
    assert "germplasm" not in function_call.parameters


def test_pattern_detection_routes_genomic_selection_requests_to_calculate_breeding_value():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Calculate genomic selection GEBVs for IR64 and Swarna for yield using GBLUP"
    )

    assert function_call is not None
    assert function_call.name == "calculate_breeding_value"
    assert function_call.parameters["method"] == "GBLUP"
    assert function_call.parameters["trait"] == "yield"
    assert function_call.parameters["germplasm_ids"] == ["IR64", "Swarna"]


def test_pattern_detection_routes_training_population_genomic_selection_with_crop():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Run genomic selection with GBLUP for grain yield on our wheat training population"
    )

    assert function_call is not None
    assert function_call.name == "calculate_breeding_value"
    assert function_call.parameters == {
        "method": "GBLUP",
        "trait": "yield",
        "crop": "wheat",
    }


def test_synonym_config_contains_required_agricultural_groups():
    assert set(SYNONYM_GROUPS) == {
        "germplasm",
        "trial",
        "observation",
        "trait",
        "cross",
        "genomics",
    }


def test_synonym_expander_accepts_custom_mapping():
    expander = SynonymExpander({"soil": ["dirt", "field dirt"]})

    assert expander.expand("Show field dirt notes and dirt chemistry") == (
        "Show soil notes and soil chemistry"
    )


def test_crop_config_contains_required_crops():
    assert set(CROP_NAMES) == {
        "wheat",
        "rice",
        "maize",
        "sorghum",
        "pearl millet",
        "chickpea",
        "soybean",
        "cotton",
        "barley",
        "oat",
        "sunflower",
        "groundnut",
    }


@given(st.sampled_from(_CROP_ALIAS_CASES))
def test_crop_detection_maps_aliases_to_canonical_crop(alias_case):
    alias, canonical = alias_case
    service = FunctionCallingService()

    assert service._detect_crop(f"Show results for {alias}") == canonical


@given(st.sampled_from(list(QUALIFIER_TERMS.items())))
def test_qualifier_detection_maps_direction(qualifier_case):
    qualifier, direction = qualifier_case
    service = FunctionCallingService()

    assert service._detect_qualifier(f"Which entries had the {qualifier} yield?") == direction


@given(st.sampled_from(["not", "without", "lacking", "excluding", "non "]))
def test_negation_detection_marks_negative_context(negation_term):
    service = FunctionCallingService()

    has_negation, context = service._detect_negation(
        f"Which varieties are {negation_term} resistant to rust?"
    )

    assert has_negation is True
    assert context


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Show this season trial results", "current_season"),
        ("Show last year trial results", "previous_year"),
        ("Show trial results from 2025", "2025"),
        ("Show rabi trial results", "rabi"),
    ],
)
def test_temporal_detection_normalizes_common_time_filters(message, expected):
    service = FunctionCallingService()

    assert service._detect_temporal(message) == expected


def test_hardened_detection_routes_synonym_expanded_germplasm_detail():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns_hardened("Show profile for cultivar IR64")

    assert function_call is not None
    assert not isinstance(function_call, ClarificationResponse)
    assert function_call.name == "get_germplasm_details"
    assert function_call.parameters == {"query": "IR64"}


def test_hardened_detection_injects_structured_parameters():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns_hardened(
        "Which pearl millet entries had the lowest trial results last year?"
    )

    assert function_call is not None
    assert not isinstance(function_call, ClarificationResponse)
    assert function_call.name == "get_trial_results"
    assert function_call.parameters["crop"] == "pearl millet"
    assert function_call.parameters["temporal"] == "previous_year"
    assert function_call.parameters["ranking_direction"] == "ascending"


def test_planner_fallback_routes_high_confidence_domain_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._try_planner_fallback(
        "Recommend selection index strategy for wheat disease pattern improvement"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["crop"] == "wheat"


def test_hardened_detection_falls_through_when_no_pattern_or_domain_confidence():
    service = FunctionCallingService()

    assert service._detect_with_patterns_hardened("hello there") is None


def test_collect_all_candidates_and_clarification_response_for_ambiguous_request():
    service = FunctionCallingService()

    clarification = service._build_ambiguity_clarification(
        "Compare trait summary for IR64 and Swarna"
    )

    assert clarification is not None
    assert [option.function_name for option in clarification.options] == [
        "get_trait_summary",
        "compare_germplasm",
    ]
    assert "Which would you prefer?" in clarification.message


@pytest.mark.asyncio
async def test_functiongemma_detection_blocks_internal_helper_not_in_allowed_schema(monkeypatch):
    service = FunctionCallingService(api_key="test-key")

    async def mock_get_client():
        return _MockFunctionGemmaClient(
            '{"function": "get_statistics", "parameters": {}}'
        )

    monkeypatch.setattr(service, "_get_client", mock_get_client)

    function_call = await service._detect_with_functiongemma("Show database statistics")

    assert function_call is None


@pytest.mark.asyncio
async def test_functiongemma_detection_accepts_advertised_function(monkeypatch):
    service = FunctionCallingService(api_key="test-key")

    async def mock_get_client():
        return _MockFunctionGemmaClient(
            '{"function": "get_trial_results", "parameters": {"trial_id": "TRIAL-22"}}'
        )

    monkeypatch.setattr(service, "_get_client", mock_get_client)

    function_call = await service._detect_with_functiongemma(
        "Show trial summary for trial TRIAL-22"
    )

    assert function_call is not None
    assert function_call.name == "get_trial_results"
    assert function_call.parameters == {"trial_id": "TRIAL-22"}
