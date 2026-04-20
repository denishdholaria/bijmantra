"""Evaluate the REEVU real-question benchmark against explicit runtime paths.

This runner uses the curated real-question benchmark fixture and scores each case
against the pass_criteria declared in the fixture. It supports two execution modes:

* local   — runs against the in-process FastAPI app via TestClient
* managed — runs against a configured remote REEVU base URL

The goal is to keep local and managed-path artifacts separate so regressions can be
tracked by runtime path rather than collapsed into one blended success rate.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from unittest.mock import AsyncMock, patch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.demo_dataset import DEMO_DATASET


FUNCTION_DOMAIN_MAP: dict[str, set[str]] = {
    "get_germplasm_details": {"breeding"},
    "get_trait_summary": {"breeding"},
    "compare_germplasm": {"breeding", "analytics"},
    "get_trial_results": {"trials", "analytics"},
    "get_marker_associations": {"genomics"},
    "calculate_breeding_value": {"genomics", "analytics"},
}

DEFAULT_LOCAL_EVAL_ORGANIZATION_ID = 1
LOCAL_EVAL_ORGANIZATION_ENV_VAR = "REEVU_LOCAL_EVAL_ORG_ID"
VALID_LOCAL_ORGANIZATION_SELECTION_MODES = frozenset({"default", "env", "cli"})
BLOCKING_LOCAL_READINESS_FLAGS = frozenset(
    {
        "germplasm.empty",
        "trials.empty",
        "observations.empty",
        "bio_gwas_runs.empty",
        "bio_qtls.empty",
        "bio_qtls.missing_or_inaccessible",
    }
)
DOMAIN_READINESS_SIGNAL_MAP: dict[str, dict[str, set[str]]] = {
    "analytics": {"blockers": {"observations.empty"}, "warnings": set()},
    "breeding": {
        "blockers": {"germplasm.empty"},
        "warnings": {"germplasm.sparse"},
    },
    "genomics": {
        "blockers": {
            "bio_gwas_runs.empty",
            "bio_qtls.empty",
            "bio_qtls.missing_or_inaccessible",
        },
        "warnings": set(),
    },
    "trials": {
        "blockers": {"trials.empty"},
        "warnings": {"trials.sparse"},
    },
}
FUNCTION_EXTRA_READINESS_SIGNAL_MAP: dict[str, dict[str, set[str]]] = {
    "get_germplasm_details": {
        "blockers": {"germplasm.empty"},
        "warnings": {"germplasm.sparse"},
    },
    "get_trait_summary": {
        "blockers": {"observations.empty"},
        "warnings": {"germplasm.sparse"},
    },
    "compare_germplasm": {
        "blockers": {"observations.empty"},
        "warnings": {"germplasm.sparse"},
    },
    "get_trial_results": {
        "blockers": {"trials.empty"},
        "warnings": {"trials.sparse"},
    },
    "get_marker_associations": {
        "blockers": {
            "bio_gwas_runs.empty",
            "bio_qtls.empty",
            "bio_qtls.missing_or_inaccessible",
        },
        "warnings": set(),
    },
    "calculate_breeding_value": {
        "blockers": {"observations.empty"},
        "warnings": set(),
    }
}
LOCAL_FAILURE_ATTRIBUTION_STATUSES = frozenset(
    {
        "executor_regression_or_contract_gap",
        "passed",
        "selected_local_org_readiness_blocker",
        "selected_local_org_readiness_warning",
    }
)
LOCAL_ORGANIZATION_SCOPES = frozenset({"demo_dataset", "non_demo", "unknown"})

LOCAL_READINESS_REMEDIATION_GUIDANCE = {
    "germplasm.empty": (
        "Provision authoritative germplasm for the selected organization via the authenticated "
        "import upload surface at /api/v2/import/upload with import_type=germplasm."
    ),
    "germplasm.sparse": (
        "Expand authoritative germplasm coverage for the selected organization via the authenticated "
        "import upload surface at /api/v2/import/upload with import_type=germplasm."
    ),
    "trials.empty": (
        "Provision authoritative trial rows for the selected organization via the authenticated "
        "import upload surface at /api/v2/import/upload with import_type=trial."
    ),
    "trials.sparse": (
        "Expand authoritative trial coverage for the selected organization via the authenticated "
        "import upload surface at /api/v2/import/upload with import_type=trial."
    ),
    "observations.empty": (
        "Provision authoritative observations for the selected organization via the authenticated "
        "import upload surface at /api/v2/import/upload with import_type=observation."
    ),
    "bio_gwas_runs.empty": (
        "Persist authoritative GWAS runs for the selected organization through the authenticated "
        "GWAS execution surface at /api/v2/bio-analytics/gwas/run using authoritative genotype "
        "and phenotype inputs."
    ),
}


def _local_organization_scope(*, organization_name: Any) -> str:
    if not isinstance(organization_name, str) or not organization_name.strip():
        return "unknown"
    if organization_name == DEMO_DATASET.organization_name:
        return "demo_dataset"
    return "non_demo"


def _parse_local_organization_id(raw_value: str | int | None) -> int:
    if raw_value is None:
        return DEFAULT_LOCAL_EVAL_ORGANIZATION_ID

    normalized = str(raw_value).strip()
    if not normalized:
        return DEFAULT_LOCAL_EVAL_ORGANIZATION_ID

    try:
        local_organization_id = int(normalized)
    except ValueError as exc:
        raise ValueError("local organization id must be an integer") from exc

    if local_organization_id <= 0:
        raise ValueError("local organization id must be a positive integer")

    return local_organization_id


def _default_local_organization_selection(local_organization_id: int) -> dict[str, Any]:
    return {
        "mode": "default",
        "requested_organization_id": local_organization_id,
        "effective_organization_id": local_organization_id,
    }


def _resolve_local_organization_selection(
    *,
    cli_value: str | int | None,
    env_value: str | int | None,
) -> dict[str, Any]:
    if cli_value is not None:
        local_organization_id = _parse_local_organization_id(cli_value)
        return {
            "mode": "cli",
            "requested_organization_id": local_organization_id,
            "effective_organization_id": local_organization_id,
        }

    if env_value is not None and str(env_value).strip():
        local_organization_id = _parse_local_organization_id(env_value)
        return {
            "mode": "env",
            "requested_organization_id": local_organization_id,
            "effective_organization_id": local_organization_id,
        }

    return _default_local_organization_selection(DEFAULT_LOCAL_EVAL_ORGANIZATION_ID)


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _extract_function_name(payload: dict[str, Any]) -> str | None:
    function_call = payload.get("function_call")
    if isinstance(function_call, dict):
        name = function_call.get("name")
        if isinstance(name, str) and name.strip():
            return name
    return None


def _extract_function_result(payload: dict[str, Any]) -> dict[str, Any]:
    function_result = payload.get("function_result")
    return function_result if isinstance(function_result, dict) else {}


def _extract_safe_failure_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    _, safe_failure = _extract_safe_failure_details(payload)
    return safe_failure


def _extract_safe_failure_details(payload: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    policy_validation = payload.get("policy_validation")
    if isinstance(policy_validation, dict):
        safe_failure = policy_validation.get("safe_failure")
        if isinstance(safe_failure, dict):
            return "policy_validation", dict(safe_failure)

    function_result = _extract_function_result(payload)
    safe_failure = function_result.get("safe_failure")
    if isinstance(safe_failure, dict):
        return "function_result", dict(safe_failure)

    return None, None


def _extract_evidence_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    envelope = payload.get("evidence_envelope")
    if isinstance(envelope, dict):
        return envelope

    function_result = _extract_function_result(payload)
    nested_envelope = function_result.get("evidence_envelope")
    return nested_envelope if isinstance(nested_envelope, dict) else {}


def _extract_retrieval_audit(payload: dict[str, Any]) -> dict[str, Any]:
    retrieval_audit = payload.get("retrieval_audit")
    if isinstance(retrieval_audit, dict):
        return retrieval_audit

    nested_retrieval_audit = _extract_function_result(payload).get("retrieval_audit")
    return nested_retrieval_audit if isinstance(nested_retrieval_audit, dict) else {}


def _extract_calculation_method_refs(payload: dict[str, Any]) -> list[str]:
    refs: list[str] = []

    function_result = _extract_function_result(payload)
    raw_refs = function_result.get("calculation_method_refs")
    if isinstance(raw_refs, list):
        refs.extend(ref for ref in raw_refs if isinstance(ref, str) and ref.strip())

    comparison_result = payload.get("comparison_result")
    if isinstance(comparison_result, dict):
        nested_refs = comparison_result.get("calculation_method_refs")
        if isinstance(nested_refs, list):
            refs.extend(ref for ref in nested_refs if isinstance(ref, str) and ref.strip())

    return refs


def _detect_domains(payload: dict[str, Any], actual_function: str | None) -> set[str]:
    plan_summary = payload.get("plan_execution_summary")
    if isinstance(plan_summary, dict):
        raw_domains = plan_summary.get("domains_involved")
        if isinstance(raw_domains, list):
            return {domain for domain in raw_domains if isinstance(domain, str) and domain.strip()}

    if actual_function is None:
        return set()

    return FUNCTION_DOMAIN_MAP.get(actual_function, set())


def _bool_has_values(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return any(bool(item) for item in value)
    return bool(value)


def _validate_auth_token(raw_token: str | None) -> str | None:
    if raw_token is None:
        return None

    token = raw_token.strip()
    if not token:
        return None
    if any(character.isspace() for character in token):
        raise ValueError("managed auth token must not contain whitespace")
    return token


def _question_family(case: dict[str, Any]) -> str:
    return f"{case['domain_group']}::{case['cross_domain_class']}"


def _relevant_local_readiness_signals(result: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    blockers: set[str] = set()
    warnings: set[str] = set()
    unmapped_expected_domains: set[str] = set()

    expected_function = result.get("expected_function")
    if isinstance(expected_function, str):
        extra_signals = FUNCTION_EXTRA_READINESS_SIGNAL_MAP.get(expected_function)
        if extra_signals is not None:
            blockers.update(extra_signals.get("blockers") or set())
            warnings.update(extra_signals.get("warnings") or set())
            return sorted(blockers), sorted(warnings), sorted(unmapped_expected_domains)

    for raw_domain in result.get("expected_domains") or []:
        if not isinstance(raw_domain, str) or not raw_domain.strip():
            continue

        signals = DOMAIN_READINESS_SIGNAL_MAP.get(raw_domain)
        if signals is None:
            unmapped_expected_domains.add(raw_domain)
            continue

        blockers.update(signals.get("blockers") or set())
        warnings.update(signals.get("warnings") or set())

    return sorted(blockers), sorted(warnings), sorted(unmapped_expected_domains)


def _build_local_failure_attribution(
    result: dict[str, Any],
    *,
    runtime_readiness: dict[str, Any],
) -> dict[str, Any]:
    relevant_blockers, relevant_warnings, unmapped_expected_domains = _relevant_local_readiness_signals(result)
    readiness_flags = [
        flag
        for flag in runtime_readiness.get("readiness_flags", [])
        if isinstance(flag, str) and flag.strip()
    ]
    selected_blockers = sorted(
        flag for flag in readiness_flags if flag in BLOCKING_LOCAL_READINESS_FLAGS and flag in relevant_blockers
    )
    selected_warnings = sorted(
        flag for flag in readiness_flags if flag not in BLOCKING_LOCAL_READINESS_FLAGS and flag in relevant_warnings
    )

    if result.get("passed"):
        status = "passed"
        reason = "The benchmark case passed on the selected local runtime."
    elif not result.get("safe_failure_observed"):
        status = "executor_regression_or_contract_gap"
        reason = (
            "The case failed without a structured safe-failure payload, so treat it as an executor or "
            "contract regression until proven otherwise."
        )
    else:
        safe_failure_payload = result.get("safe_failure_payload")
        safe_failure_error_category = (
            safe_failure_payload.get("error_category")
            if isinstance(safe_failure_payload, dict)
            else None
        )

        if selected_blockers and safe_failure_error_category in {
            "insufficient_compute_inputs",
            "insufficient_retrieval_scope",
        }:
            status = "selected_local_org_readiness_blocker"
            reason = (
                "The selected local organization is blocked on benchmark-relevant data surfaces for the "
                "expected REEVU domains in this case."
            )
        elif selected_warnings and safe_failure_error_category == "insufficient_retrieval_scope":
            status = "selected_local_org_readiness_warning"
            reason = (
                "The selected local organization is sparse on benchmark-relevant data surfaces for the "
                "expected REEVU domains in this case."
            )
        else:
            status = "executor_regression_or_contract_gap"
            reason = (
                "The selected local runtime does not expose matching readiness signals for this structured "
                "failure, so treat it as an executor or contract gap."
            )

    if unmapped_expected_domains:
        reason += " Unmapped expected domains: " + ", ".join(unmapped_expected_domains) + "."

    return {
        "status": status,
        "reason": reason,
        "relevant_blockers": selected_blockers,
        "relevant_warnings": selected_warnings,
        "unmapped_expected_domains": unmapped_expected_domains,
    }


def _annotate_local_failure_attributions(
    results: list[dict[str, Any]],
    *,
    runtime_readiness: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    annotated_results: list[dict[str, Any]] = []
    attribution_summary: dict[str, int] = {}

    for result in results:
        annotated_result = dict(result)
        failure_attribution = _build_local_failure_attribution(
            annotated_result,
            runtime_readiness=runtime_readiness,
        )
        status = failure_attribution["status"]
        if status not in LOCAL_FAILURE_ATTRIBUTION_STATUSES:
            raise ValueError(f"unexpected local failure attribution status: {status}")

        annotated_result["failure_attribution"] = failure_attribution
        attribution_summary[status] = attribution_summary.get(status, 0) + 1
        annotated_results.append(annotated_result)

    return annotated_results, {
        status: attribution_summary[status] for status in sorted(attribution_summary)
    }


def _summarize_grouped_results(
    results: list[dict[str, Any]],
    *,
    group_key: str,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for result in results:
        group_name = result[group_key]
        bucket = grouped.setdefault(
            group_name,
            {
                "total_cases": 0,
                "passed_cases": 0,
                "failed_cases": 0,
                "pass_rate": 0.0,
                "failed_benchmark_ids": [],
            },
        )
        bucket["total_cases"] += 1
        if result["passed"]:
            bucket["passed_cases"] += 1
        else:
            bucket["failed_cases"] += 1
            bucket["failed_benchmark_ids"].append(result["benchmark_id"])

    for group_name in sorted(grouped):
        bucket = grouped[group_name]
        total_cases = bucket["total_cases"]
        bucket["pass_rate"] = round((bucket["passed_cases"] / total_cases) if total_cases else 0.0, 4)
        bucket["failed_benchmark_ids"] = sorted(bucket["failed_benchmark_ids"])

    return {group_name: grouped[group_name] for group_name in sorted(grouped)}


def _evaluate_check(
    check_name: str,
    *,
    case: dict[str, Any],
    payload: dict[str, Any],
    actual_function: str | None,
    detected_domains: set[str],
    safe_failure_payload: dict[str, Any] | None,
    evidence_envelope: dict[str, Any],
    retrieval_audit: dict[str, Any],
    calculation_method_refs: list[str],
) -> bool:
    if check_name == "capability_grounded_answer":
        return actual_function == case["expected_function"]

    if check_name == "expected_domain_alignment":
        expected_domains = set(case.get("expected_domains", []))
        return expected_domains.issubset(detected_domains)

    if check_name == "do_not_guess_when_resolution_is_incomplete":
        if not case.get("safe_failure_expected", False):
            return True
        return bool(safe_failure_payload) and actual_function == case["expected_function"]

    if check_name == "evidence_envelope_required":
        return _bool_has_values(evidence_envelope)

    if check_name == "retrieval_audit_required":
        return _bool_has_values(retrieval_audit)

    if check_name == "failure_reason_context_required":
        if not safe_failure_payload:
            return False
        return _bool_has_values(safe_failure_payload.get("searched")) and _bool_has_values(
            safe_failure_payload.get("missing")
        )

    if check_name == "deterministic_method_refs_required":
        return bool(calculation_method_refs)

    if check_name == "deterministic_compute_evidence_required":
        calculation_steps = evidence_envelope.get("calculation_steps")
        return isinstance(calculation_steps, list) and len(calculation_steps) > 0

    if check_name == "structured_safe_failure_required":
        return isinstance(safe_failure_payload, dict) and bool(safe_failure_payload)

    if check_name == "failure_reason_must_be_explicit":
        if not safe_failure_payload:
            return False
        return bool(safe_failure_payload.get("error_category")) or _bool_has_values(
            safe_failure_payload.get("missing")
        )

    return False


def score_case(
    case: dict[str, Any],
    *,
    http_status: int,
    payload: dict[str, Any],
    runtime_path: str,
) -> dict[str, Any]:
    actual_function = _extract_function_name(payload)
    safe_failure_source, safe_failure_payload = _extract_safe_failure_details(payload)
    evidence_envelope = _extract_evidence_envelope(payload)
    retrieval_audit = _extract_retrieval_audit(payload)
    calculation_method_refs = _extract_calculation_method_refs(payload)
    detected_domains = _detect_domains(payload, actual_function)

    checks: dict[str, bool] = {}
    for category, criterion_names in case["pass_criteria"].items():
        for check_name in criterion_names:
            checks[f"{category}.{check_name}"] = _evaluate_check(
                check_name,
                case=case,
                payload=payload,
                actual_function=actual_function,
                detected_domains=detected_domains,
                safe_failure_payload=safe_failure_payload,
                evidence_envelope=evidence_envelope,
                retrieval_audit=retrieval_audit,
                calculation_method_refs=calculation_method_refs,
            )

    unexpected_safe_failure = bool(safe_failure_payload) and not case.get("safe_failure_expected", False)
    failed_checks = [name for name, ok in checks.items() if not ok]
    if unexpected_safe_failure:
        failed_checks.append("safe_failure.unexpected_safe_failure")

    passed = http_status < 400 and not unexpected_safe_failure and all(checks.values())

    return {
        "benchmark_id": case["benchmark_id"],
        "runtime_path": runtime_path,
        "domain_group": case["domain_group"],
        "cross_domain_class": case["cross_domain_class"],
        "question_family": _question_family(case),
        "http_status": http_status,
        "passed": passed,
        "expected_function": case["expected_function"],
        "actual_function": actual_function,
        "expected_domains": list(case.get("expected_domains", [])),
        "detected_domains": sorted(detected_domains),
        "safe_failure_expected": case.get("safe_failure_expected", False),
        "safe_failure_observed": bool(safe_failure_payload),
        "safe_failure_source": safe_failure_source,
        "safe_failure_payload": safe_failure_payload,
        "failed_checks": failed_checks,
        "checks": checks,
    }


@contextmanager
def _local_query_poster(
    *,
    local_organization_id: int,
) -> Iterator[Callable[[str], tuple[int, dict[str, Any]]]]:
    from starlette.testclient import TestClient

    from app.api.deps import get_current_user
    from app.main import app

    async def override_current_user() -> SimpleNamespace:
        return SimpleNamespace(
            id=1,
            organization_id=local_organization_id,
            email=f"real-question-eval+org{local_organization_id}@bijmantra.org",
            is_demo=False,
            is_superuser=False,
        )

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        with patch(
            "app.api.v2.chat.AIQuotaService.check_and_increment_usage",
            new=AsyncMock(return_value=None),
        ):
            with TestClient(app) as client:
                def post_local_query(query: str) -> tuple[int, dict[str, Any]]:
                    response = client.post(
                        "/api/v2/chat",
                        json={"message": query, "include_context": False},
                    )
                    payload = response.json()
                    return response.status_code, payload if isinstance(payload, dict) else {}

                yield post_local_query
    finally:
        app.dependency_overrides.clear()


def _post_managed_query(
    *,
    base_url: str,
    query: str,
    auth_token: str | None,
    timeout_seconds: float,
) -> tuple[int, dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/api/v2/chat"
    body = json.dumps({"message": query, "include_context": False}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    request = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw) if raw else {}
            return int(response.status), payload if isinstance(payload, dict) else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"error": raw or str(exc)}
        return int(exc.code), payload if isinstance(payload, dict) else {"error": str(exc)}
    except URLError as exc:
        return 599, {"error": str(exc.reason)}


def evaluate_cases(
    cases: list[dict[str, Any]],
    *,
    runtime_path: str,
    managed_base_url: str | None = None,
    managed_auth_token: str | None = None,
    local_organization_id: int = DEFAULT_LOCAL_EVAL_ORGANIZATION_ID,
    timeout_seconds: float = 30.0,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    if runtime_path == "local":
        with _local_query_poster(local_organization_id=local_organization_id) as post_local_query:
            for case in cases:
                http_status, payload = post_local_query(case["query"])
                results.append(
                    score_case(
                        case,
                        http_status=http_status,
                        payload=payload,
                        runtime_path=runtime_path,
                    )
                )
        return results

    if not managed_base_url:
        raise ValueError("managed_base_url is required when runtime_path='managed'")

    for case in cases:
        http_status, payload = _post_managed_query(
            base_url=managed_base_url,
            query=case["query"],
            auth_token=managed_auth_token,
            timeout_seconds=timeout_seconds,
        )

        results.append(
            score_case(
                case,
                http_status=http_status,
                payload=payload,
                runtime_path=runtime_path,
            )
        )

    return results


def build_summary(
    *,
    fixture_path: Path,
    runtime_path: str,
    results: list[dict[str, Any]],
    managed_base_url: str | None = None,
    local_organization_id: int = DEFAULT_LOCAL_EVAL_ORGANIZATION_ID,
    local_organization_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_status = "evaluated"
    runtime_readiness: dict[str, Any] | None = None
    readiness_blockers: list[str] = []
    readiness_warnings: list[str] = []
    if runtime_path == "local":
        runtime_readiness = _inspect_local_runtime_readiness(
            local_organization_id=local_organization_id,
        )
        runtime_status, readiness_blockers, readiness_warnings = _classify_local_runtime_readiness(
            runtime_readiness,
        )

    annotated_results = results
    failure_attribution_summary: dict[str, int] | None = None
    if runtime_readiness is not None:
        annotated_results, failure_attribution_summary = _annotate_local_failure_attributions(
            results,
            runtime_readiness=runtime_readiness,
        )

    total_cases = len(annotated_results)
    passed_cases = sum(1 for result in annotated_results if result["passed"])
    pass_rate = (passed_cases / total_cases) if total_cases else 0.0
    question_family_summary = {
        "by_domain_group": _summarize_grouped_results(annotated_results, group_key="domain_group"),
        "by_cross_domain_class": _summarize_grouped_results(annotated_results, group_key="cross_domain_class"),
        "by_question_family": _summarize_grouped_results(annotated_results, group_key="question_family"),
    }

    summary = {
        "generated_at": _iso_now(),
        "fixture_path": str(fixture_path),
        "runtime_path": runtime_path,
        "runtime_target": managed_base_url if runtime_path == "managed" else "in_process_app",
        "runtime_status": runtime_status,
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "pass_rate": round(pass_rate, 4),
        "failed_cases": total_cases - passed_cases,
        "question_family_summary": question_family_summary,
        "results": annotated_results,
    }
    if runtime_readiness is not None:
        summary["local_organization_id"] = local_organization_id
        summary["local_organization_selection"] = (
            local_organization_selection
            if isinstance(local_organization_selection, dict)
            else _default_local_organization_selection(local_organization_id)
        )
        summary["readiness_blockers"] = readiness_blockers
        summary["readiness_warnings"] = readiness_warnings
        summary["runtime_readiness"] = runtime_readiness
        summary["failure_attribution_summary"] = failure_attribution_summary or {}
    return summary


async def _inspect_local_runtime_readiness_async(
    *,
    session: Any,
    local_organization_id: int,
) -> dict[str, Any]:
    readiness = {
        "organization_id": local_organization_id,
        "surface_counts": {},
        "surface_examples": {},
        "surface_errors": {},
        "readiness_flags": [],
    }

    count_queries = {
        "germplasm": "SELECT COUNT(*) FROM germplasm WHERE organization_id = :org_id",
        "trials": "SELECT COUNT(*) FROM trials WHERE organization_id = :org_id",
        "observations": "SELECT COUNT(*) FROM observations WHERE organization_id = :org_id",
        "bio_gwas_runs": "SELECT COUNT(*) FROM bio_gwas_runs WHERE organization_id = :org_id",
        "bio_qtls": "SELECT COUNT(*) FROM bio_qtls WHERE organization_id = :org_id",
    }
    example_queries = {
        "germplasm": (
            "SELECT germplasm_name FROM germplasm WHERE organization_id = :org_id ORDER BY id LIMIT 5",
            "germplasm_name",
        ),
        "trials": (
            "SELECT trial_name FROM trials WHERE organization_id = :org_id ORDER BY id LIMIT 5",
            "trial_name",
        ),
    }

    for surface_name, sql in count_queries.items():
        try:
            result = await session.execute(
                text(sql),
                {"org_id": local_organization_id},
            )
        except Exception as exc:
            await session.rollback()
            readiness["surface_errors"][surface_name] = f"{type(exc).__name__}: {exc}"
            continue

        readiness["surface_counts"][surface_name] = int(result.scalar_one() or 0)

    for surface_name, (sql, column_name) in example_queries.items():
        try:
            result = await session.execute(
                text(sql),
                {"org_id": local_organization_id},
            )
        except Exception as exc:
            await session.rollback()
            readiness["surface_errors"][f"{surface_name}_examples"] = (
                f"{type(exc).__name__}: {exc}"
            )
            continue

        readiness["surface_examples"][surface_name] = [
            row._mapping[column_name]
            for row in result
            if row._mapping[column_name]
        ]

    flags = readiness["readiness_flags"]
    counts = readiness["surface_counts"]
    errors = readiness["surface_errors"]

    if "germplasm" not in errors and counts.get("germplasm", 0) == 0:
        flags.append("germplasm.empty")
    elif "germplasm" not in errors and counts.get("germplasm", 0) < 5:
        flags.append("germplasm.sparse")

    if "trials" not in errors and counts.get("trials", 0) == 0:
        flags.append("trials.empty")
    elif "trials" not in errors and counts.get("trials", 0) < 5:
        flags.append("trials.sparse")

    if "observations" not in errors and counts.get("observations", 0) == 0:
        flags.append("observations.empty")

    if "bio_gwas_runs" not in errors and counts.get("bio_gwas_runs", 0) == 0:
        flags.append("bio_gwas_runs.empty")

    if "bio_qtls" in errors:
        flags.append("bio_qtls.missing_or_inaccessible")
    elif counts.get("bio_qtls", 0) == 0:
        flags.append("bio_qtls.empty")

    return readiness


def _inspect_local_runtime_readiness(*, local_organization_id: int) -> dict[str, Any]:
    """Capture local tenant data readiness so benchmark failures are self-explanatory."""
    from app.core.config import settings

    async def _inspect() -> dict[str, Any]:
        engine = create_async_engine(
            settings.DATABASE_URL,
            future=True,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                return await _inspect_local_runtime_readiness_async(
                    session=session,
                    local_organization_id=local_organization_id,
                )
        finally:
            await engine.dispose()

    return asyncio.run(_inspect())


async def _list_active_local_organizations_async(*, session: Any) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            "SELECT id, name, is_active "
            "FROM organizations "
            "WHERE is_active = TRUE "
            "ORDER BY id"
        )
    )
    return [
        {
            "organization_id": int(row._mapping["id"]),
            "organization_name": row._mapping["name"],
            "is_active": bool(row._mapping["is_active"]),
            "listed_in_active_organizations": True,
        }
        for row in result
    ]


def _benchmark_relevant_surface_count(surface_counts: dict[str, Any]) -> int:
    total = 0
    for surface_name in ("germplasm", "trials", "observations", "bio_gwas_runs", "bio_qtls"):
        count = surface_counts.get(surface_name)
        if isinstance(count, int) and count > 0:
            total += count
    return total


def _build_local_readiness_policy_guidance(
    entries: list[dict[str, Any]],
    *,
    selected_local_organization_id: int,
) -> list[str]:
    selected_entry = next(
        (
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("organization_id") == selected_local_organization_id
        ),
        None,
    )
    if not isinstance(selected_entry, dict):
        return []
    if selected_entry.get("runtime_status") != "blocked":
        return []

    ready_entries = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("runtime_status") == "ready"
    ]
    if not ready_entries:
        return []

    ready_demo_entries = [
        entry
        for entry in ready_entries
        if entry.get("organization_scope") == "demo_dataset"
    ]
    ready_non_demo_entries = [
        entry
        for entry in ready_entries
        if entry.get("organization_scope") == "non_demo"
    ]
    if not ready_demo_entries or ready_non_demo_entries:
        return []
    if selected_entry.get("organization_scope") != "non_demo":
        return []

    ready_demo_labels = ", ".join(
        f"{entry.get('organization_id')} ({entry.get('organization_name') or DEMO_DATASET.organization_name})"
        for entry in ready_demo_entries
    )
    selected_local_label = (
        f"{selected_entry.get('organization_id')} ({selected_entry.get('organization_name') or 'unnamed'})"
    )
    return [
        "Benchmark-ready local coverage currently comes from demo-dataset tenant(s): "
        f"{ready_demo_labels}. The canonical demo dataset is isolated from production and staging; "
        f"do not mirror demo-seeded benchmark data into selected non-demo organization {selected_local_label}. "
        "Use the ready demo tenant for supplementary local executor verification or provision authoritative "
        "data for the selected organization."
    ]


def _remediation_guidance_for_readiness_flag(
    *,
    readiness_flag: Any,
    organization_scope: str,
) -> str | None:
    if not isinstance(readiness_flag, str) or not readiness_flag.strip():
        return None

    canned_guidance = LOCAL_READINESS_REMEDIATION_GUIDANCE.get(readiness_flag)
    if isinstance(canned_guidance, str) and canned_guidance:
        return canned_guidance

    if readiness_flag in {"bio_qtls.empty", "bio_qtls.missing_or_inaccessible"}:
        if organization_scope == "demo_dataset":
            return (
                "Provision deterministic BioQTL rows for the demo dataset through the canonical "
                "seeded analytics path before rerunning the local benchmark."
            )
        return (
            "Provision authoritative BioQTL rows for the selected organization via the authenticated "
            "import upload surface at /api/v2/import/upload with import_type=qtl."
        )

    return None


def _build_selected_local_organization_remediation(
    entries: list[dict[str, Any]],
    *,
    selected_local_organization_id: int,
) -> list[str]:
    selected_entry = next(
        (
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("organization_id") == selected_local_organization_id
        ),
        None,
    )
    if not isinstance(selected_entry, dict):
        return []

    organization_scope = str(selected_entry.get("organization_scope") or "unknown")
    ordered_flags = [
        *list(selected_entry.get("readiness_blockers") or []),
        *list(selected_entry.get("readiness_warnings") or []),
    ]

    seen_flags: set[str] = set()
    remediation: list[str] = []
    for readiness_flag in ordered_flags:
        if not isinstance(readiness_flag, str) or readiness_flag in seen_flags:
            continue
        seen_flags.add(readiness_flag)

        guidance = _remediation_guidance_for_readiness_flag(
            readiness_flag=readiness_flag,
            organization_scope=organization_scope,
        )
        if guidance:
            remediation.append(f"{readiness_flag}: {guidance}")

    return remediation


def _select_least_blocked_local_organization(
    entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    blocked_entries = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("runtime_status") != "ready"
    ]
    if not blocked_entries:
        return None

    selected_entry = min(
        blocked_entries,
        key=lambda entry: (
            len(entry.get("readiness_blockers") or []),
            len(entry.get("readiness_warnings") or []),
            -_benchmark_relevant_surface_count(
                entry.get("surface_counts") if isinstance(entry.get("surface_counts"), dict) else {}
            ),
            int(entry.get("organization_id") or 0),
        ),
    )
    surface_counts = (
        selected_entry.get("surface_counts") if isinstance(selected_entry.get("surface_counts"), dict) else {}
    )
    return {
        "organization_id": selected_entry.get("organization_id"),
        "organization_name": selected_entry.get("organization_name"),
        "organization_scope": selected_entry.get("organization_scope"),
        "selected": bool(selected_entry.get("selected")),
        "runtime_status": selected_entry.get("runtime_status"),
        "readiness_blockers": list(selected_entry.get("readiness_blockers") or []),
        "readiness_warnings": list(selected_entry.get("readiness_warnings") or []),
        "benchmark_relevant_surface_count": _benchmark_relevant_surface_count(surface_counts),
    }


def _build_local_readiness_census_payload(
    *,
    organizations: list[dict[str, Any]],
    readiness_by_organization_id: dict[int, dict[str, Any]],
    local_organization_selection: dict[str, Any],
) -> dict[str, Any]:
    selected_local_organization_id = int(local_organization_selection["effective_organization_id"])
    organization_index = {entry["organization_id"]: dict(entry) for entry in organizations}

    if selected_local_organization_id not in organization_index:
        organization_index[selected_local_organization_id] = {
            "organization_id": selected_local_organization_id,
            "organization_name": None,
            "is_active": False,
            "listed_in_active_organizations": False,
        }

    entries: list[dict[str, Any]] = []
    benchmark_ready_organization_ids: list[int] = []
    benchmark_ready_demo_organization_ids: list[int] = []
    benchmark_ready_non_demo_organization_ids: list[int] = []
    blocked_organization_ids: list[int] = []

    for organization_id in sorted(organization_index):
        readiness = readiness_by_organization_id[organization_id]
        runtime_status, readiness_blockers, readiness_warnings = _classify_local_runtime_readiness(
            readiness
        )
        organization_entry = organization_index[organization_id]
        organization_scope = _local_organization_scope(
            organization_name=organization_entry.get("organization_name")
        )
        if runtime_status == "ready":
            benchmark_ready_organization_ids.append(organization_id)
            if organization_scope == "demo_dataset":
                benchmark_ready_demo_organization_ids.append(organization_id)
            elif organization_scope == "non_demo":
                benchmark_ready_non_demo_organization_ids.append(organization_id)
        else:
            blocked_organization_ids.append(organization_id)

        entries.append(
            {
                **organization_entry,
                "organization_scope": organization_scope,
                "selected": organization_id == selected_local_organization_id,
                "runtime_status": runtime_status,
                "readiness_blockers": readiness_blockers,
                "readiness_warnings": readiness_warnings,
                "surface_counts": readiness.get("surface_counts", {}),
                "surface_errors": readiness.get("surface_errors", {}),
                "surface_examples": readiness.get("surface_examples", {}),
            }
        )

    least_blocked_local_organization = None
    if not benchmark_ready_organization_ids:
        least_blocked_local_organization = _select_least_blocked_local_organization(entries)
    policy_guidance = _build_local_readiness_policy_guidance(
        entries,
        selected_local_organization_id=selected_local_organization_id,
    )
    selected_local_organization_remediation = _build_selected_local_organization_remediation(
        entries,
        selected_local_organization_id=selected_local_organization_id,
    )

    return {
        "generated_at": _iso_now(),
        "runtime_path": "local",
        "local_organization_selection": local_organization_selection,
        "selected_local_organization_id": selected_local_organization_id,
        "organizations_scanned": len(entries),
        "benchmark_ready_organization_ids": benchmark_ready_organization_ids,
        "benchmark_ready_demo_organization_ids": benchmark_ready_demo_organization_ids,
        "benchmark_ready_non_demo_organization_ids": benchmark_ready_non_demo_organization_ids,
        "blocked_organization_ids": blocked_organization_ids,
        "least_blocked_local_organization": least_blocked_local_organization,
        "policy_guidance": policy_guidance,
        "selected_local_organization_remediation": selected_local_organization_remediation,
        "organizations": entries,
    }


def build_local_readiness_census(
    *,
    local_organization_selection: dict[str, Any],
) -> dict[str, Any]:
    from app.core.config import settings

    async def _build() -> dict[str, Any]:
        engine = create_async_engine(
            settings.DATABASE_URL,
            future=True,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory() as session:
                organizations = await _list_active_local_organizations_async(session=session)
                candidate_organization_ids = {
                    int(local_organization_selection["effective_organization_id"]),
                    *(organization["organization_id"] for organization in organizations),
                }
                readiness_by_organization_id = {
                    organization_id: await _inspect_local_runtime_readiness_async(
                        session=session,
                        local_organization_id=organization_id,
                    )
                    for organization_id in sorted(candidate_organization_ids)
                }
                return _build_local_readiness_census_payload(
                    organizations=organizations,
                    readiness_by_organization_id=readiness_by_organization_id,
                    local_organization_selection=local_organization_selection,
                )
        finally:
            await engine.dispose()

    return asyncio.run(_build())


def _classify_local_runtime_readiness(readiness: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    flags = list(readiness.get("readiness_flags", []))
    blockers = [flag for flag in flags if flag in BLOCKING_LOCAL_READINESS_FLAGS]
    warnings = [flag for flag in flags if flag not in BLOCKING_LOCAL_READINESS_FLAGS]
    status = "blocked" if blockers else "ready"
    return status, blockers, warnings


def _format_local_organization_console_label(organization: dict[str, Any]) -> str:
    organization_id = organization.get("organization_id") or "N/A"
    organization_name = organization.get("organization_name") or "unnamed"
    label = f"{organization_id} ({organization_name})"
    if organization.get("organization_scope") == "demo_dataset":
        return f"{label}, demo dataset"
    return label


def _collect_ready_candidate_labels(local_readiness_census: dict[str, Any]) -> list[str]:
    organizations = local_readiness_census.get("organizations")
    if not isinstance(organizations, list):
        return []
    return [
        _format_local_organization_console_label(organization)
        for organization in organizations
        if isinstance(organization, dict) and organization.get("runtime_status") == "ready"
    ]


def _build_local_readiness_console_lines(local_readiness_census: dict[str, Any]) -> list[str]:
    if not isinstance(local_readiness_census, dict):
        return []

    lines: list[str] = []
    ready_candidate_labels = _collect_ready_candidate_labels(local_readiness_census)
    if ready_candidate_labels:
        lines.append(
            "- benchmark-ready local organizations: " + ", ".join(ready_candidate_labels)
        )

    least_blocked_local_organization = local_readiness_census.get("least_blocked_local_organization")
    if isinstance(least_blocked_local_organization, dict):
        least_blocked_label = _format_local_organization_console_label(
            least_blocked_local_organization
        )
        least_blocked_blockers = ", ".join(
            str(item)
            for item in (least_blocked_local_organization.get("readiness_blockers") or [])
        )
        if least_blocked_blockers:
            least_blocked_label += f" — blockers: {least_blocked_blockers}"
        lines.append(f"- least-blocked local organization: {least_blocked_label}")

    for guidance in local_readiness_census.get("policy_guidance") or []:
        if isinstance(guidance, str) and guidance.strip():
            lines.append(f"- local selection guidance: {guidance}")

    for guidance in local_readiness_census.get("selected_local_organization_remediation") or []:
        if isinstance(guidance, str) and guidance.strip():
            lines.append(f"- recommended remediation: {guidance}")

    return lines


def _build_blocked_local_runtime_message(
    summary: dict[str, Any],
    *,
    local_readiness_census: dict[str, Any] | None = None,
) -> str:
    blockers = ", ".join(summary.get("readiness_blockers", [])) or "readiness blockers detected"
    organization_id = summary.get("local_organization_id")
    message = (
        "Benchmark blocked: "
        f"local runtime organization {organization_id} is not benchmark-ready ({blockers})."
    )

    if not isinstance(local_readiness_census, dict):
        return message

    ready_candidate_labels = _collect_ready_candidate_labels(local_readiness_census)
    if ready_candidate_labels:
        message += " Benchmark-ready local organizations discovered: " + ", ".join(
            ready_candidate_labels
        ) + "."
    else:
        least_blocked_local_organization = local_readiness_census.get(
            "least_blocked_local_organization"
        )
        if isinstance(least_blocked_local_organization, dict):
            least_blocked_id = least_blocked_local_organization.get("organization_id") or "N/A"
            least_blocked_name = least_blocked_local_organization.get("organization_name") or "unnamed"
            least_blocked_blockers = ", ".join(
                str(item)
                for item in (least_blocked_local_organization.get("readiness_blockers") or [])
            ) or "unspecified readiness blockers"
            message += (
                f" Least-blocked local organization is {least_blocked_id} "
                f"({least_blocked_name}): {least_blocked_blockers}."
            )

    policy_guidance = [
        guidance
        for guidance in (local_readiness_census.get("policy_guidance") or [])
        if isinstance(guidance, str) and guidance.strip()
    ]
    if policy_guidance:
        message += " " + " ".join(policy_guidance)

    remediation_guidance = [
        guidance
        for guidance in (
            local_readiness_census.get("selected_local_organization_remediation") or []
        )
        if isinstance(guidance, str) and guidance.strip()
    ]
    if remediation_guidance:
        message += " Recommended remediation: " + " ".join(remediation_guidance)

    return message


def _print_summary(summary: dict[str, Any]) -> None:
    print("REEVU Real-Question Benchmark Evaluation")
    print(f"- runtime path: {summary['runtime_path']}")
    print(f"- runtime target: {summary['runtime_target']}")
    print(f"- runtime status: {summary['runtime_status']}")
    print(f"- fixture path: {summary['fixture_path']}")
    if "local_organization_id" in summary:
        print(f"- local organization id: {summary['local_organization_id']}")
    local_organization_selection = summary.get("local_organization_selection")
    if isinstance(local_organization_selection, dict):
        print(
            "- local organization selection: "
            f"{local_organization_selection.get('mode')} "
            f"(requested={local_organization_selection.get('requested_organization_id')}, "
            f"effective={local_organization_selection.get('effective_organization_id')})"
        )
    print(
        "- pass rate: "
        f"{summary['passed_cases']}/{summary['total_cases']} "
        f"({summary['pass_rate']:.2%})"
    )
    print("- question family summary:")
    for family_name, family_summary in summary["question_family_summary"]["by_question_family"].items():
        print(
            f"  - {family_name}: "
            f"{family_summary['passed_cases']}/{family_summary['total_cases']} "
            f"({family_summary['pass_rate']:.2%})"
        )
    runtime_readiness = summary.get("runtime_readiness")
    if isinstance(runtime_readiness, dict):
        print("- local runtime readiness:")
        for surface_name, count in runtime_readiness.get("surface_counts", {}).items():
            print(f"  - {surface_name}: {count}")
        for surface_name, examples in runtime_readiness.get("surface_examples", {}).items():
            if isinstance(examples, list) and examples:
                print(f"  - {surface_name} examples: {', '.join(str(example) for example in examples)}")
        for surface_name, error in runtime_readiness.get("surface_errors", {}).items():
            print(f"  - {surface_name} error: {error}")
        flags = runtime_readiness.get("readiness_flags", [])
        if flags:
            print(f"  - readiness flags: {', '.join(flags)}")
    blockers = summary.get("readiness_blockers", [])
    if blockers:
        print(f"- readiness blockers: {', '.join(blockers)}")
    warnings = summary.get("readiness_warnings", [])
    if warnings:
        print(f"- readiness warnings: {', '.join(warnings)}")
    failure_attribution_summary = summary.get("failure_attribution_summary")
    if isinstance(failure_attribution_summary, dict) and failure_attribution_summary:
        print("- failure attribution summary:")
        for status, count in failure_attribution_summary.items():
            print(f"  - {status}: {count}")
    if summary["failed_cases"]:
        print("- failing benchmark ids:")
        for result in summary["results"]:
            if result["passed"]:
                continue
            failure_attribution = result.get("failure_attribution")
            failure_attribution_status = (
                failure_attribution.get("status")
                if isinstance(failure_attribution, dict)
                else None
            )
            suffix = f" [{failure_attribution_status}]" if isinstance(failure_attribution_status, str) else ""
            print(f"  - {result['benchmark_id']}: {', '.join(result['failed_checks'])}{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate REEVU real-question benchmark against local or managed runtime paths."
    )
    parser.add_argument(
        "--fixture",
        default="tests/fixtures/reevu/real_question_benchmark.json",
        help="Path to the real-question benchmark fixture",
    )
    parser.add_argument(
        "--runtime-path",
        choices=("local", "managed"),
        required=True,
        help="Runtime path to evaluate",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional path to write a JSON summary artifact",
    )
    parser.add_argument(
        "--managed-base-url",
        default="",
        help="Managed REEVU base URL (required when --runtime-path managed)",
    )
    parser.add_argument(
        "--managed-auth-token",
        default=os.getenv("REEVU_MANAGED_EVAL_TOKEN", ""),
        help="Optional bearer token for managed runtime evaluation",
    )
    parser.add_argument(
        "--local-organization-id",
        default=None,
        help="Organization id to impersonate for local in-process benchmark evaluation.",
    )
    parser.add_argument(
        "--local-readiness-census-output",
        default="",
        help="Optional path to write a local readiness census artifact for active organizations.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="HTTP timeout for managed runtime evaluation",
    )
    parser.add_argument(
        "--fail-on-failed-cases",
        action="store_true",
        help="Exit with code 1 when one or more benchmark cases fail.",
    )
    args = parser.parse_args(argv)

    fixture_path = Path(args.fixture)
    if not fixture_path.is_absolute():
        fixture_path = PROJECT_ROOT / fixture_path

    if args.runtime_path == "managed" and not args.managed_base_url:
        print("Error: --managed-base-url is required when --runtime-path managed")
        return 2

    if args.runtime_path != "local" and args.local_readiness_census_output:
        print("Error: --local-readiness-census-output can only be used with --runtime-path local")
        return 2

    cases = _load_fixture(fixture_path)
    try:
        managed_auth_token = _validate_auth_token(args.managed_auth_token)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2

    raw_env_local_organization_id = os.getenv(LOCAL_EVAL_ORGANIZATION_ENV_VAR)
    try:
        local_organization_selection = _resolve_local_organization_selection(
            cli_value=args.local_organization_id,
            env_value=raw_env_local_organization_id,
        )
        local_organization_id = int(local_organization_selection["effective_organization_id"])
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2

    results = evaluate_cases(
        cases,
        runtime_path=args.runtime_path,
        managed_base_url=args.managed_base_url or None,
        managed_auth_token=managed_auth_token,
        local_organization_id=local_organization_id,
        timeout_seconds=args.timeout_seconds,
    )
    summary = build_summary(
        fixture_path=fixture_path,
        runtime_path=args.runtime_path,
        results=results,
        managed_base_url=args.managed_base_url or None,
        local_organization_id=local_organization_id,
        local_organization_selection=local_organization_selection,
    )

    _print_summary(summary)

    if args.json_output:
        output_path = Path(args.json_output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"- wrote json summary: {output_path}")

    local_readiness_census: dict[str, Any] | None = None
    needs_local_readiness_census = (
        args.runtime_path == "local"
        and (
            bool(args.local_readiness_census_output)
            or (args.fail_on_failed_cases and summary["runtime_status"] == "blocked")
        )
    )
    if needs_local_readiness_census:
        local_readiness_census = build_local_readiness_census(
            local_organization_selection=local_organization_selection,
        )

    if args.local_readiness_census_output:
        census_output_path = Path(args.local_readiness_census_output)
        if not census_output_path.is_absolute():
            census_output_path = PROJECT_ROOT / census_output_path
        census_output_path.parent.mkdir(parents=True, exist_ok=True)
        if local_readiness_census is None:
            local_readiness_census = build_local_readiness_census(
                local_organization_selection=local_organization_selection,
            )
        census_output_path.write_text(
            json.dumps(local_readiness_census, indent=2),
            encoding="utf-8",
        )
        print(f"- wrote local readiness census: {census_output_path}")
        for line in _build_local_readiness_console_lines(local_readiness_census):
            print(line)

    if args.fail_on_failed_cases and summary["runtime_path"] == "local" and summary["runtime_status"] == "blocked":
        print(
            _build_blocked_local_runtime_message(
                summary,
                local_readiness_census=local_readiness_census,
            )
        )
        return 1

    if args.fail_on_failed_cases and summary["failed_cases"]:
        print(
            f"Benchmark failed: {summary['failed_cases']} case(s) did not meet the declared pass criteria."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
