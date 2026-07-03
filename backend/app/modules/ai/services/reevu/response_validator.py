"""Evidence-first output validation for REEVU responses.

Stage B additions:
    - citation_mismatch: flags citation markers with no matching evidence
    - percentage_pattern: flags percentage claims with no backing calculation
"""

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidencePack:
    """Minimal structured evidence contract used by the validator."""

    evidence_refs: set[str] = field(default_factory=set)
    calculation_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ClaimItem:
    """A claim emitted by REEVU before final synthesis."""

    statement: str
    claim_type: str
    evidence_refs: tuple[str, ...] = tuple()
    calculation_ids: tuple[str, ...] = tuple()


@dataclass(frozen=True)
class ValidationResult:
    """Validation result for claim/evidence checks."""

    valid: bool
    errors: tuple[str, ...] = tuple()


# ── Stage B patterns ──────────────────────────────────────────────────
_NUMERIC_CITATION_GROUP_RE = re.compile(r"\[([0-9,;\s\-]+)\]")
_REF_TAG_RE = re.compile(r"\[\[ref:([^\]]+)\]\]")
_PERCENTAGE_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?%\s*\w+")
_NON_CLAIM_PERCENT_TERMS = {
    "confidence",
    "confident",
    "certainty",
    "certain",
    "sure",
    "ci",
    "interval",
    "probability",
    "likelihood",
    "chance",
}


def _normalize_ref(value: str) -> str:
    """Normalize evidence/citation ids for robust equality checks."""
    return value.strip().lower()


def is_non_claim_percentage(phrase: str) -> bool:
    """Return True when a percentage phrase expresses confidence, not a measured claim."""
    normalized = phrase.strip().lower()
    suffix = normalized.split("%", maxsplit=1)[1].strip() if "%" in normalized else ""
    if not suffix:
        return False
    leading_term = suffix.split()[0]
    return leading_term in _NON_CLAIM_PERCENT_TERMS


def is_year_like_numeric_ref(value: str) -> bool:
    """Treat bracketed years like [2024] as non-citation tokens."""
    if not value.isdigit():
        return False
    year = int(value)
    return 1900 <= year <= 2100


def extract_numeric_citation_ids(content: str) -> list[str]:
    """Extract numeric citation ids from bracketed groups.

    Supported forms:
    - ``[1]``
    - ``[1, 2]``
    - ``[1;2]``
    - ``[1-3]``
    - mixed groups like ``[1, 3-4; 6]``
    """
    extracted: list[str] = []
    seen: set[str] = set()

    for group in _NUMERIC_CITATION_GROUP_RE.findall(content):
        segments = [part.strip() for part in re.split(r"[,;]", group) if part.strip()]
        for segment in segments:
            if "-" in segment:
                bounds = [value.strip() for value in segment.split("-", maxsplit=1)]
                if len(bounds) != 2 or not bounds[0].isdigit() or not bounds[1].isdigit():
                    continue
                start_id = int(bounds[0])
                end_id = int(bounds[1])
                lower = min(start_id, end_id)
                upper = max(start_id, end_id)
                if upper - lower > 50:
                    continue
                for cited_num in range(lower, upper + 1):
                    cited_id = str(cited_num)
                    if is_year_like_numeric_ref(cited_id) or cited_id in seen:
                        continue
                    seen.add(cited_id)
                    extracted.append(cited_id)
                continue

            if not segment.isdigit():
                continue
            cited_id = segment
            if is_year_like_numeric_ref(cited_id) or cited_id in seen:
                continue
            seen.add(cited_id)
            extracted.append(cited_id)

    return extracted


class ResponseValidator:
    """Reject claims that cannot be traced to evidence or computations."""

    def validate_claims(self, claims: list[ClaimItem], evidence_pack: EvidencePack) -> ValidationResult:
        errors: list[str] = []
        normalized_evidence = {_normalize_ref(ref) for ref in evidence_pack.evidence_refs}

        for index, claim in enumerate(claims):
            if claim.claim_type == "reference":
                if not claim.evidence_refs:
                    errors.append(f"claim[{index}] reference claim is missing evidence refs")
                    continue

                missing_refs = [
                    ref for ref in claim.evidence_refs if _normalize_ref(ref) not in normalized_evidence
                ]
                if missing_refs:
                    errors.append(f"claim[{index}] has unmatched evidence refs: {', '.join(missing_refs)}")

            if claim.claim_type == "quantitative":
                missing_calculations = [
                    calc_id for calc_id in claim.calculation_ids if calc_id not in evidence_pack.calculation_ids
                ]
                if missing_calculations:
                    errors.append(
                        f"claim[{index}] has unmatched calculation ids: {', '.join(missing_calculations)}"
                    )

        return ValidationResult(valid=not errors, errors=tuple(errors))

    # ── Stage B: content-level anti-hallucination ─────────────────────

    def check_citation_mismatch(self, content: str, evidence_pack: EvidencePack) -> list[str]:
        """Flag citation markers with no matching evidence_ref.

        Supports numeric citations (``[1]``) and explicit ref tags (``[[ref:doc-1]]``).
        """
        flags: list[str] = []
        normalized_evidence = {_normalize_ref(ref) for ref in evidence_pack.evidence_refs}

        for cited_id in extract_numeric_citation_ids(content):
            normalized_cited_id = _normalize_ref(cited_id)
            if normalized_cited_id not in normalized_evidence:
                flags.append(f"citation_mismatch:[{normalized_cited_id}]")

        for match in _REF_TAG_RE.finditer(content):
            cited_ref = _normalize_ref(match.group(1))
            if cited_ref and cited_ref not in normalized_evidence:
                flags.append(f"citation_mismatch:[[ref:{cited_ref}]]")

        # Preserve stable ordering while removing duplicates.
        if not flags:
            return []
        deduped: list[str] = []
        seen: set[str] = set()
        for flag in flags:
            if flag not in seen:
                deduped.append(flag)
                seen.add(flag)
        return deduped

    def check_percentage_without_calc(self, content: str, evidence_pack: EvidencePack) -> list[str]:
        """Flag percentage claims (e.g. '95% yield') with no backing calculation."""
        if evidence_pack.calculation_ids:
            return []
        matches = _PERCENTAGE_RE.findall(content)
        if matches:
            deduped: list[str] = []
            seen: set[str] = set()
            for match in matches:
                cleaned = match.strip().lower()
                if is_non_claim_percentage(cleaned):
                    continue
                if cleaned not in seen:
                    deduped.append(f"percentage_without_calc:{cleaned}")
                    seen.add(cleaned)
                if len(deduped) >= 3:
                    break
            return deduped
        return []
