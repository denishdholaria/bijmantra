"""
REEVU Provenance Validator — Stage B

Quality checks on the evidence envelope:
  • freshness   – flag stale refs
  • resolvable  – flag refs missing required identifiers
  • required    – flag refs with missing minimum fields
  • aggregate   – collect all flags into envelope.policy_flags
"""

from __future__ import annotations

from datetime import datetime, timezone
import math

from app.schemas.reevu_envelope import EvidenceRef, ReevuEnvelope

# ── tunables ──────────────────────────────────────────────────────────
DEFAULT_MAX_AGE_SECONDS: float = 86_400  # 24 hours
MAX_FUTURE_SKEW_SECONDS: float = 60  # tolerate minor clock drift
MAX_FRESHNESS_DRIFT_SECONDS: float = 60  # tolerate small duplicate-reporting variance


def validate_freshness(
    ref: EvidenceRef,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
) -> str | None:
    """Return a flag string if *ref* is stale, else None."""
    if ref.freshness_seconds is not None and not math.isfinite(ref.freshness_seconds):
        return f"invalid_freshness:{ref.entity_id}"

    if ref.freshness_seconds is not None and ref.freshness_seconds < 0:
        return f"invalid_freshness:{ref.entity_id}"

    if ref.freshness_seconds is not None and ref.freshness_seconds > max_age_seconds:
        return f"stale_evidence:{ref.entity_id}"

    if ref.freshness_seconds is None and ref.retrieved_at:
        retrieved_at = ref.retrieved_at.strip()
        try:
            parsed = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        except ValueError:
            return f"invalid_retrieved_at:{ref.entity_id}"

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        age_seconds = (datetime.now(timezone.utc) - parsed).total_seconds()
        if age_seconds < -MAX_FUTURE_SKEW_SECONDS:
            return f"future_evidence_timestamp:{ref.entity_id}"
        if age_seconds > max_age_seconds:
            return f"stale_evidence:{ref.entity_id}"
    return None


def validate_resolvable(ref: EvidenceRef) -> str | None:
    """Return a flag string if *ref* cannot be resolved."""
    if not ref.entity_id or not ref.entity_id.strip():
        return "unresolvable_ref:empty_entity_id"

    source_type = (ref.source_type or "").strip().lower()
    normalized_entity_id = ref.entity_id.strip().lower()
    if source_type == "function" and not normalized_entity_id.startswith("fn:"):
        return f"unresolvable_ref:function_entity_id_format:{normalized_entity_id}"

    return None


def validate_required_fields(ref: EvidenceRef) -> str | None:
    """Return a flag string if *ref* is missing minimum required fields."""
    if not ref.source_type or not ref.source_type.strip():
        return f"missing_source_type:{ref.entity_id}"

    source_type = ref.source_type.strip().lower()
    if source_type == "function" and not ref.query_or_method.strip():
        return f"missing_query_or_method:{ref.entity_id}"

    return None


def validate_all(
    envelope: ReevuEnvelope,
    *,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
) -> list[str]:
    """Run every provenance check and return aggregated policy flags.

    Flags are de-duplicated and sorted for deterministic output.
    """
    flags: set[str] = set()
    seen_entity_ids: set[str] = set()
    source_type_by_entity: dict[str, str] = {}
    query_method_by_key: dict[tuple[str, str], str] = {}
    retrieved_at_by_key: dict[tuple[str, str], datetime] = {}
    freshness_by_key: dict[tuple[str, str], float] = {}

    for ref in envelope.evidence_refs:
        normalized_entity_id = (ref.entity_id or "").strip().lower()
        normalized_source_type = (ref.source_type or "").strip().lower()
        normalized_query_method = (ref.query_or_method or "").strip().lower()
        normalized_retrieved_at = (ref.retrieved_at or "").strip()
        if normalized_entity_id:
            prior_source_type = source_type_by_entity.get(normalized_entity_id)
            if prior_source_type is None:
                source_type_by_entity[normalized_entity_id] = normalized_source_type
            elif prior_source_type and normalized_source_type and prior_source_type != normalized_source_type:
                flags.add(f"conflicting_source_type:{normalized_entity_id}")

            if normalized_source_type and normalized_query_method:
                key = (normalized_entity_id, normalized_source_type)
                prior_query_method = query_method_by_key.get(key)
                if prior_query_method is None:
                    query_method_by_key[key] = normalized_query_method
                elif prior_query_method != normalized_query_method:
                    flags.add(
                        f"conflicting_query_method:{normalized_entity_id}:{normalized_source_type}"
                    )

            if normalized_source_type and normalized_retrieved_at:
                try:
                    parsed_retrieved_at = datetime.fromisoformat(
                        normalized_retrieved_at.replace("Z", "+00:00")
                    )
                    if parsed_retrieved_at.tzinfo is None:
                        parsed_retrieved_at = parsed_retrieved_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    parsed_retrieved_at = None

                if parsed_retrieved_at is not None:
                    key = (normalized_entity_id, normalized_source_type)
                    prior_retrieved_at = retrieved_at_by_key.get(key)
                    if prior_retrieved_at is None:
                        retrieved_at_by_key[key] = parsed_retrieved_at
                    else:
                        drift_seconds = abs((prior_retrieved_at - parsed_retrieved_at).total_seconds())
                        if drift_seconds > MAX_FUTURE_SKEW_SECONDS:
                            flags.add(
                                f"conflicting_retrieved_at:{normalized_entity_id}:{normalized_source_type}"
                            )

            if (
                normalized_source_type
                and ref.freshness_seconds is not None
                and math.isfinite(ref.freshness_seconds)
                and ref.freshness_seconds >= 0
            ):
                key = (normalized_entity_id, normalized_source_type)
                prior_freshness = freshness_by_key.get(key)
                if prior_freshness is None:
                    freshness_by_key[key] = ref.freshness_seconds
                else:
                    drift_seconds = abs(prior_freshness - ref.freshness_seconds)
                    if drift_seconds > MAX_FRESHNESS_DRIFT_SECONDS:
                        flags.add(
                            f"conflicting_freshness_seconds:{normalized_entity_id}:{normalized_source_type}"
                        )

            if normalized_entity_id in seen_entity_ids:
                flags.add(f"duplicate_evidence_ref:{normalized_entity_id}")
            else:
                seen_entity_ids.add(normalized_entity_id)

        for check in (
            lambda r: validate_freshness(r, max_age_seconds),
            validate_resolvable,
            validate_required_fields,
        ):
            flag = check(ref)
            if flag:
                flags.add(flag)

    # No evidence at all is itself a flag-worthy condition.
    if not envelope.evidence_refs and envelope.claims:
        flags.add("no_evidence_for_claims")

    return sorted(flags)
