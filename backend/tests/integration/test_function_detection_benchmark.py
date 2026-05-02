import json
from pathlib import Path

import pytest

from app.modules.ai.services.function_calling_service import (
    ClarificationResponse,
    FunctionCallingService,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = BACKEND_ROOT / "tests" / "fixtures" / "reevu" / "function_detection_benchmark.json"
REAL_QUESTION_FIXTURE_PATH = (
    BACKEND_ROOT / "tests" / "fixtures" / "reevu" / "real_question_benchmark.json"
)


def _load_cases() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_function_detection_benchmark_fixture_covers_real_question_pack():
    cases = _load_cases()
    real_cases = json.loads(REAL_QUESTION_FIXTURE_PATH.read_text(encoding="utf-8"))
    real_case_ids = {case["benchmark_id"] for case in real_cases}

    assert len(cases) == 28
    assert {case["source_benchmark_id"] for case in cases} == real_case_ids
    assert sum(1 for case in cases if case["variant_type"] == "original") == 14
    assert sum(1 for case in cases if case["variant_type"] == "synonym_variation") == 14


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case["id"])
def test_function_detection_benchmark_routes_expected_function(case):
    service = FunctionCallingService()

    function_call = service._detect_with_patterns_hardened(case["query"])

    assert function_call is not None, case["query"]
    assert not isinstance(function_call, ClarificationResponse), case["query"]
    assert function_call.name == case["expected_function"]
