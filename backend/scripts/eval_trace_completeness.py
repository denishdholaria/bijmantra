"""Trace-completeness evaluator for REEVU stream stage telemetry.

Runs a prompt fixture against `/api/v2/chat/stream` using deterministic mocks and
reports request-level stage-trace completeness against the Stage A KPI floor.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.api.deps import get_current_user


REQUIRED_STAGE_ORDER = [
    "intent_scope",
    "plan_generation",
    "answer_synthesis",
    "policy_validation",
    "response_emission",
]
REQUIRED_EVENT_FIELDS = {"request_id", "stage", "status", "ts"}


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_stage_events(response_text: str) -> list[dict[str, Any]]:
    stage_events: list[dict[str, Any]] = []
    for line in response_text.splitlines():
        if not line.startswith("data: ") or '"type": "stage"' not in line:
            continue
        try:
            stage_events.append(json.loads(line[6:]))
        except json.JSONDecodeError:
            continue
    return stage_events


def _evaluate_case(case: dict[str, Any], client: TestClient) -> dict[str, Any]:
    response = client.post(
        "/api/v2/chat/stream",
        json={"message": case["message"], "include_context": False},
    )

    stage_events = _parse_stage_events(response.text)
    seen_stages: list[str] = []
    for event in stage_events:
        stage = event.get("stage")
        if stage and stage not in seen_stages:
            seen_stages.append(stage)

    missing_stages = [stage for stage in REQUIRED_STAGE_ORDER if stage not in seen_stages]

    field_violations: list[str] = []
    for idx, event in enumerate(stage_events):
        missing_fields = sorted(REQUIRED_EVENT_FIELDS - set(event.keys()))
        if missing_fields:
            field_violations.append(f"event[{idx}] missing {','.join(missing_fields)}")
        if event.get("status") == "completed" and "latency_ms" not in event:
            field_violations.append(f"event[{idx}] missing latency_ms on completed stage")

    order_violations: list[str] = []
    if not missing_stages:
        indices = {stage: seen_stages.index(stage) for stage in REQUIRED_STAGE_ORDER}
        for left, right in zip(REQUIRED_STAGE_ORDER, REQUIRED_STAGE_ORDER[1:]):
            if indices[left] >= indices[right]:
                order_violations.append(f"{left} appears after {right}")

    complete = not missing_stages and not field_violations and not order_violations

    return {
        "id": case["id"],
        "message": case["message"],
        "http_status": response.status_code,
        "complete": complete,
        "missing_stages": missing_stages,
        "field_violations": field_violations,
        "order_violations": order_violations,
    }


def _build_summary(case_results: list[dict[str, Any]], floor: float) -> dict[str, Any]:
    total = len(case_results)
    complete_count = sum(1 for result in case_results if result["complete"])
    completeness_rate = (complete_count / total) if total else 0.0

    failures = [result for result in case_results if not result["complete"]]

    return {
        "total_cases": total,
        "complete_cases": complete_count,
        "trace_completeness_rate": round(completeness_rate, 4),
        "kpi_floor": floor,
        "meets_floor": completeness_rate >= floor,
        "required_stage_order": REQUIRED_STAGE_ORDER,
        "required_event_fields": sorted(REQUIRED_EVENT_FIELDS),
        "failures": failures,
    }


def _print_summary(summary: dict[str, Any]) -> None:
    print("REEVU Trace Completeness Eval")
    print(f"- total cases: {summary['total_cases']}")
    print(
        "- complete traces: "
        f"{summary['complete_cases']}/{summary['total_cases']} "
        f"({summary['trace_completeness_rate']:.2%})"
    )
    print(f"- KPI floor: {summary['kpi_floor']:.2%}")
    print(f"- meets floor: {summary['meets_floor']}")
    if summary["failures"]:
        print("- failing cases:")
        for failure in summary["failures"]:
            print(f"  - {failure['id']}: missing={failure['missing_stages']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate REEVU stream trace completeness.")
    parser.add_argument(
        "--fixture",
        default="tests/fixtures/reevu/trace_completeness_prompts.json",
        help="Path to fixture JSON file",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional path to write JSON summary",
    )
    parser.add_argument(
        "--floor",
        type=float,
        default=0.99,
        help="Trace-completeness KPI floor",
    )
    args = parser.parse_args()

    fixture_path = Path(args.fixture)
    cases = _load_fixture(fixture_path)

    async def override_current_user() -> SimpleNamespace:
        return SimpleNamespace(id=1, organization_id=1, email="trace-eval@bijmantra.org", is_demo=False)

    app.dependency_overrides[get_current_user] = override_current_user

    try:
        # Keep eval deterministic: patch non-telemetry side effects (quota, memory writes,
        # function routing/execution) so metrics reflect stage-trace contract only.
        with TestClient(app) as client, patch("app.api.v2.chat.get_llm_service") as mock_llm_service, patch(
            "app.api.v2.chat.get_breeding_service"
        ) as mock_breeding_service, patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.api.v2.chat.FunctionCallingService.detect_function_call",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.api.v2.chat.VeenaService.get_or_create_user_context",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.api.v2.chat.VeenaService.update_interaction_stats",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.api.v2.chat.VeenaService.save_episodic_memory",
            new=AsyncMock(return_value=None),
        ):
            llm_service = SimpleNamespace()

            async def mock_status() -> dict[str, Any]:
                return {
                    "active_provider": "template",
                    "active_model": "template-v1",
                    "providers": {"template": {"available": True}},
                }

            async def mock_stream_chat(*args: Any, **kwargs: Any):
                yield "REEVU"
                yield " trace"
                yield " response"

            llm_service.get_status = mock_status
            llm_service.stream_chat = mock_stream_chat
            mock_llm_service.return_value = llm_service

            breeding_service = SimpleNamespace()

            async def mock_search(*args: Any, **kwargs: Any) -> list[Any]:
                return []

            breeding_service.search_breeding_knowledge = mock_search
            mock_breeding_service.return_value = breeding_service

            results = [_evaluate_case(case, client) for case in cases]
    finally:
        app.dependency_overrides.clear()

    summary = _build_summary(results, floor=args.floor)
    _print_summary(summary)

    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"- wrote json summary: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
