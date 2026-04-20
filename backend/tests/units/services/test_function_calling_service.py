import pytest

from app.modules.ai.services.function_calling_service import FunctionCallingService


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


def test_pattern_detection_routes_compound_trial_phenotype_environment_requests_to_cross_domain_query():
    service = FunctionCallingService()

    function_call = service._detect_with_patterns(
        "Show phenotype observations from trials at Ludhiana under current weather"
    )

    assert function_call is not None
    assert function_call.name == "cross_domain_query"
    assert function_call.parameters["location"] == "Ludhiana"


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
