"""
Evidence pack assembly, claim extraction, and REEVU envelope construction.

Extracted from message_service.py — pure functions, no HTTP, no DB.
"""

from __future__ import annotations

import re
from typing import Any

from app.modules.ai.services.memory import SearchResult
from app.modules.ai.services.reevu import (
    ClaimItem,
    EvidencePack,
    ResponseValidator,
    ValidationResult,
    extract_numeric_citation_ids,
    is_non_claim_percentage,
    is_year_like_numeric_ref,
)
from app.modules.ai.services.reevu_provenance_validator import validate_all as validate_provenance
from app.schemas.reevu_envelope import (
    CalculationStep,
    ClaimTrace,
    EvidenceRef,
    ReevuEnvelope,
    UncertaintyInfo,
)

# Compiled regex patterns
_CLAIM_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_REF_TAG_CAPTURE_RE = re.compile(r"\[\[ref:([^\]]+)\]\]")
_CALC_TAG_CAPTURE_RE = re.compile(r"\[\[calc:([^\]]+)\]\]")
_INLINE_TRACE_TAG_RE = re.compile(r"\[\[(?:ref|calc):[^\]]+\]\]")
_PERCENTAGE_PHRASE_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?%\s*\w+")


def build_evidence_pack(
    context_docs: list[SearchResult] | None,
    function_call_name: str | None = None,
    function_result: dict[str, Any] | None = None,
) -> EvidencePack:
    """Assemble an evidence pack from retrieved context and tool execution artifacts."""
    evidence_refs: set[str] = set()
    calculation_ids: set[str] = set()

    for doc in context_docs or []:
        if doc.doc_id:
            evidence_refs.add(str(doc.doc_id))
        if doc.source_id:
            evidence_refs.add(str(doc.source_id))

    if function_result:
        for key in ("evidence_refs", "source_ids", "doc_ids"):
            values = function_result.get(key)
            if isinstance(values, list):
                evidence_refs.update(str(v) for v in values if v is not None)

        calc_values = function_result.get("calculation_ids")
        if isinstance(calc_values, list):
            calculation_ids.update(str(v) for v in calc_values if v is not None)

        method_refs = function_result.get("calculation_method_refs")
        if isinstance(method_refs, list):
            calculation_ids.update(str(v) for v in method_refs if v is not None)

        nested_envelope = function_result.get("evidence_envelope")
        if isinstance(nested_envelope, dict):
            nested_refs = nested_envelope.get("evidence_refs")
            if isinstance(nested_refs, list):
                for ref in nested_refs:
                    if isinstance(ref, dict):
                        entity_id = ref.get("entity_id")
                        if entity_id is not None:
                            evidence_refs.add(str(entity_id))
                    elif ref is not None:
                        evidence_refs.add(str(ref))

            nested_steps = nested_envelope.get("calculation_steps")
            if isinstance(nested_steps, list):
                for step in nested_steps:
                    if isinstance(step, dict):
                        step_id = step.get("step_id")
                        if step_id is not None:
                            calculation_ids.add(str(step_id))

        payload = function_result.get("data")
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    if item.get("doc_id") is not None:
                        evidence_refs.add(str(item["doc_id"]))
                    if item.get("source_id") is not None:
                        evidence_refs.add(str(item["source_id"]))
                    if item.get("id") is not None:
                        evidence_refs.add(str(item["id"]))

    if function_call_name and function_call_name.startswith(("calculate_", "analyze_", "predict_")):
        calculation_ids.add(f"fn:{function_call_name}")

    return EvidencePack(evidence_refs=evidence_refs, calculation_ids=calculation_ids)


def extract_claims_for_validation(content: str, evidence_pack: EvidencePack) -> list[ClaimItem]:
    """Extract minimal claim structure for deterministic policy validation."""
    claims: list[ClaimItem] = []
    seen_claim_keys: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()

    def _append_claim(claim: ClaimItem) -> None:
        normalized_statement = claim.statement.strip().lower()
        normalized_refs = tuple(ref.strip().lower() for ref in claim.evidence_refs)
        normalized_calcs = tuple(calc.strip() for calc in claim.calculation_ids)
        key = (claim.claim_type, normalized_statement, normalized_refs, normalized_calcs)
        if key in seen_claim_keys:
            return
        seen_claim_keys.add(key)
        claims.append(claim)

    sentences = [
        segment.strip()
        for segment in _CLAIM_SENTENCE_SPLIT_RE.split(content)
        if segment and segment.strip()
    ]
    if not sentences:
        sentences = [content]

    for sentence in sentences:
        sentence_calc_ids = tuple(
            calc.strip()
            for calc in _CALC_TAG_CAPTURE_RE.findall(sentence)
            if calc.strip()
        )

        for ref in _REF_TAG_CAPTURE_RE.findall(sentence):
            _append_claim(
                ClaimItem(
                    statement=f"reference:{ref}",
                    claim_type="reference",
                    evidence_refs=(ref.strip(),),
                )
            )

        for cited_id in extract_numeric_citation_ids(sentence):
            _append_claim(
                ClaimItem(
                    statement=f"reference:[{cited_id}]",
                    claim_type="reference",
                    evidence_refs=(cited_id,),
                )
            )

        for calc in sentence_calc_ids:
            _append_claim(
                ClaimItem(
                    statement=f"quantitative:{calc}",
                    claim_type="quantitative",
                    calculation_ids=(calc,),
                )
            )

        for percentage_phrase in _PERCENTAGE_PHRASE_RE.findall(sentence):
            if is_non_claim_percentage(percentage_phrase):
                continue
            calculation_ids = (
                sentence_calc_ids
                if sentence_calc_ids
                else tuple(sorted(evidence_pack.calculation_ids))
            )
            if not calculation_ids:
                calculation_ids = ("missing_calculation",)

            _append_claim(
                ClaimItem(
                    statement=f"quantitative:{percentage_phrase.strip()}",
                    claim_type="quantitative",
                    calculation_ids=calculation_ids,
                )
            )

    non_claim_percentage_tokens: set[str] = set()
    for phrase in _PERCENTAGE_PHRASE_RE.findall(content):
        if is_non_claim_percentage(phrase):
            token = phrase.split("%", maxsplit=1)[0].strip()
            if token:
                non_claim_percentage_tokens.add(f"{token}%")
                non_claim_percentage_tokens.add(token)

    raw_numeric_tokens = re.findall(r"\b\d+(?:\.\d+)?%?\b", content)
    numeric_tokens: list[str] = []
    for token in raw_numeric_tokens:
        if token in non_claim_percentage_tokens:
            continue
        normalized = token[:-1] if token.endswith("%") else token
        if normalized.isdigit() and is_year_like_numeric_ref(normalized):
            continue
        numeric_tokens.append(token)

    has_quantitative_density = len(numeric_tokens) >= 3
    if has_quantitative_density and not evidence_pack.calculation_ids and not evidence_pack.evidence_refs:
        _append_claim(
            ClaimItem(
                statement="quantitative-claim-without-evidence",
                claim_type="quantitative",
                calculation_ids=("missing_calculation",),
            )
        )

    return claims


def extract_claim_traces(content: str, evidence_pack: EvidencePack) -> list[ClaimTrace]:
    """Classify response sentences as retrieval-backed, calculation-backed, or model synthesis."""
    sentences = [
        segment.strip()
        for segment in _CLAIM_SENTENCE_SPLIT_RE.split(content)
        if segment and segment.strip()
    ]
    if not sentences and content.strip():
        sentences = [content.strip()]

    claim_traces: list[ClaimTrace] = []
    seen_keys: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()

    for sentence in sentences:
        explicit_refs = tuple(
            ref.strip() for ref in _REF_TAG_CAPTURE_RE.findall(sentence) if ref.strip()
        )
        cited_ids = tuple(extract_numeric_citation_ids(sentence))
        evidence_refs = tuple(dict.fromkeys((*explicit_refs, *cited_ids)))

        explicit_calc_ids = tuple(
            calc.strip() for calc in _CALC_TAG_CAPTURE_RE.findall(sentence) if calc.strip()
        )

        calculation_ids = explicit_calc_ids
        if not calculation_ids:
            percentage_phrases = [
                phrase
                for phrase in _PERCENTAGE_PHRASE_RE.findall(sentence)
                if not is_non_claim_percentage(phrase)
            ]
            if percentage_phrases and evidence_pack.calculation_ids:
                calculation_ids = tuple(sorted(evidence_pack.calculation_ids))

        if calculation_ids:
            support_type = "calculation_backed"
        elif evidence_refs:
            support_type = "retrieval_backed"
        else:
            support_type = "model_synthesis"

        display_statement = _INLINE_TRACE_TAG_RE.sub("", sentence)
        display_statement = re.sub(r"\s+", " ", display_statement).strip()
        display_statement = re.sub(r"\s+([.,;:!?])", r"\1", display_statement)
        if not display_statement:
            continue

        key = (
            support_type,
            display_statement.lower(),
            tuple(ref.lower() for ref in evidence_refs),
            tuple(calc.lower() for calc in calculation_ids),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)

        claim_traces.append(
            ClaimTrace(
                statement=display_statement,
                support_type=support_type,
                evidence_refs=list(evidence_refs),
                calculation_ids=list(calculation_ids),
            )
        )

    return claim_traces


def validate_response_content(
    content: str,
    context_docs: list[SearchResult] | None,
    function_call_name: str | None = None,
    function_result: dict[str, Any] | None = None,
) -> tuple[ValidationResult, EvidencePack]:
    """Run REEVU response validation against assembled evidence pack."""
    evidence_pack = build_evidence_pack(context_docs, function_call_name, function_result)
    claims = extract_claims_for_validation(content, evidence_pack)
    validator = ResponseValidator()
    validation = validator.validate_claims(claims=claims, evidence_pack=evidence_pack)

    content_flags = validator.check_citation_mismatch(content, evidence_pack)
    content_flags.extend(validator.check_percentage_without_calc(content, evidence_pack))

    if content_flags:
        merged_errors = list(validation.errors)
        for flag in content_flags:
            if flag not in merged_errors:
                merged_errors.append(flag)
        validation = ValidationResult(valid=False, errors=tuple(merged_errors))

    return validation, evidence_pack


def build_reevu_envelope(
    content: str,
    evidence_pack: EvidencePack,
    validation: ValidationResult,
    context_docs: list[SearchResult] | None = None,
    function_call_name: str | None = None,
) -> dict[str, Any]:
    """Construct the Stage-B evidence envelope from validation artefacts."""
    evidence_refs = [
        EvidenceRef(
            source_type="rag",
            entity_id=str(ref),
            query_or_method="vector_search",
        )
        for ref in evidence_pack.evidence_refs
    ]
    calculation_steps = [
        CalculationStep(step_id=str(calc_id))
        for calc_id in evidence_pack.calculation_ids
    ]
    claims = extract_claims_for_validation(content, evidence_pack)
    claim_traces = extract_claim_traces(content, evidence_pack)
    claim_strings = [c.statement for c in claims]
    normalized_errors = [error.strip().lower() for error in validation.errors]
    evidence_related_error_markers = (
        "evidence",
        "citation",
        "claim[",
        "percentage_without_calc",
        "missing_calculation",
    )

    policy_flags = list(validation.errors)
    missing_evidence_signals: list[str] = []

    if not evidence_pack.evidence_refs and (
        claim_strings
        or any(
            marker in error
            for error in normalized_errors
            for marker in evidence_related_error_markers
        )
    ):
        missing_evidence_signals.append("missing_evidence")

    if (
        any(claim.claim_type == "quantitative" for claim in claims)
        and not evidence_pack.calculation_ids
    ):
        missing_evidence_signals.append("missing_calculation_provenance")

    for signal in missing_evidence_signals:
        if signal not in policy_flags:
            policy_flags.append(signal)

    confidence = 1.0 if validation.valid else max(0.0, 1.0 - 0.2 * len(validation.errors))
    missing_data: list[str] = []
    if not evidence_pack.evidence_refs:
        missing_data.append("no_rag_context")
    if not evidence_pack.calculation_ids and function_call_name:
        missing_data.append("no_calculation_ids")

    envelope = ReevuEnvelope(
        claims=claim_strings,
        claim_traces=claim_traces,
        evidence_refs=evidence_refs,
        calculation_steps=calculation_steps,
        uncertainty=UncertaintyInfo(confidence=confidence, missing_data=missing_data),
        missing_evidence_signals=missing_evidence_signals,
        policy_flags=policy_flags,
    )

    provenance_flags = validate_provenance(envelope)
    if provenance_flags:
        envelope = envelope.model_copy(
            update={"policy_flags": envelope.policy_flags + provenance_flags}
        )

    envelope_payload = envelope.model_dump()
    envelope_payload["calculations"] = envelope_payload.get("calculation_steps", [])
    return envelope_payload
