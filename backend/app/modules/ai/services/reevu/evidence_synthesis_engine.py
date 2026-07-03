"""
Evidence Synthesis Engine

Synthesizes evidence from all REEVU domain steps into a unified picture:
agreements, contradictions, gaps, and an overall confidence score.

This runs as a post-processing step after StepExecutor.execute_plan() completes
and before the LLM explanation prompt is built. Instead of dumping raw domain
records into the LLM, the synthesis engine produces a structured SynthesisResult
that the LLM can reason over honestly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.modules.ai.services.reevu.step_executor import ExecutionOutcome, StepResult


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class EvidenceAgreement:
    """Two or more domain steps agree on the same entity's performance."""
    domains: list[str]          # e.g. ["analytics", "genomics"]
    entity_id: str              # germplasm ID or trial ID
    entity_name: str
    claim: str                  # e.g. "IR64 has highest yield and high GEBV"
    confidence: float           # 0.0–1.0


@dataclass
class EvidenceContradiction:
    """Two domain steps produce conflicting signals for the same entity."""
    domain_a: str
    domain_b: str
    entity_id: str
    entity_name: str
    claim_a: str                # e.g. "IR64 ranks #1 for yield"
    claim_b: str                # e.g. "IR64 is susceptible to blast"
    severity: Literal["warning", "critical"]


@dataclass
class EvidenceGap:
    """A domain step failed or returned no data."""
    domain: str
    entity_id: str | None
    description: str            # human-readable description
    impact: Literal["low", "medium", "high"]
    suggestion: str             # how to fill the gap


@dataclass
class SynthesisResult:
    """Unified evidence picture from all domain steps."""
    primary_conclusion: str | None
    confidence: float
    supporting_evidence: list[EvidenceAgreement] = field(default_factory=list)
    contradictions: list[EvidenceContradiction] = field(default_factory=list)
    gaps: list[EvidenceGap] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)


# ── Engine ────────────────────────────────────────────────────────────────────

# Resistance types that indicate susceptibility (not resistance)
_SUSCEPTIBLE_TYPES: frozenset[str] = frozenset({
    "susceptible", "highly_susceptible", "hs", "s", "ms",
    "moderately_susceptible",
})

# Gap descriptions and suggestions per domain
_GAP_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "soil":        ("No soil analysis data for trial locations",
                    "Add soil test records for trial locations to explain yield variability"),
    "weather":     ("No weather data available for the query period",
                    "Ensure weather service is configured and trial locations have coordinates"),
    "genomics":    ("No genomic data available for the queried germplasm",
                    "Run GWAS or GEBV analysis for these entries"),
    "pest_disease":("No pest/disease scouting data available",
                    "Add scouting records or disease resistance screening data"),
    "seed_ops":    ("No seed inventory data available",
                    "Update seedlot records for the queried germplasm"),
    "phenotyping": ("No phenotypic observations available",
                    "Add observation records for the queried traits and germplasm"),
    "trials":      ("No trial data found for the query",
                    "Verify trial names, locations, and seasons match the query"),
    "field":       ("No field location data available",
                    "Add field location records with coordinates"),
    "sensors":     ("No IoT sensor data available",
                    "Check sensor device connectivity and data ingestion"),
    "climate":     ("No climate projection data available",
                    "Ensure climate service is configured"),
    "commercial":  ("No commercial/market data available",
                    "Add variety release and market demand records"),
    "harvest":     ("No harvest records available",
                    "Add harvest data for the queried trials and seasons"),
    "nursery":     ("No nursery operations data available",
                    "Add nursery records for the queried crop and location"),
    "vision":      ("No image analysis results available",
                    "Provide an image URL or base64 image for vision analysis"),
    "analytics":   ("No analytics results available",
                    "Ensure phenotypic observations exist for the queried traits"),
}


class EvidenceSynthesisEngine:
    """Synthesize evidence from all domain steps into a unified picture.

    Usage:
        engine = EvidenceSynthesisEngine()
        result = engine.synthesize(outcome, original_query, params)
    """

    def synthesize(
        self,
        outcome: ExecutionOutcome,
        original_query: str,
        params: dict[str, Any],
    ) -> SynthesisResult:
        """Synthesize evidence from all domain steps.

        Args:
            outcome: The ExecutionOutcome from StepExecutor.execute_plan().
            original_query: The user's original query string.
            params: The original function call params dict.

        Returns:
            SynthesisResult with agreements, contradictions, gaps, and confidence.
        """
        agreements = self._find_agreements(outcome)
        contradictions = self._find_contradictions(outcome)
        gaps = self._find_gaps(outcome, params)
        confidence = self._compute_confidence(outcome, agreements, contradictions, gaps)
        primary_conclusion = self._derive_primary_conclusion(outcome, agreements)
        caveats = self._build_caveats(contradictions, gaps)

        return SynthesisResult(
            primary_conclusion=primary_conclusion,
            confidence=confidence,
            supporting_evidence=agreements,
            contradictions=contradictions,
            gaps=gaps,
            caveats=caveats,
        )

    # ── Agreement Detection ───────────────────────────────────────────────────

    def _find_agreements(self, outcome: ExecutionOutcome) -> list[EvidenceAgreement]:
        """Find entities that appear in 2+ domain steps with consistent signals.

        Currently detects:
        - analytics top-rank + genomics high GEBV for same germplasm
        - analytics top-rank + trials top-performer for same germplasm
        """
        agreements: list[EvidenceAgreement] = []

        # Build per-domain entity maps
        analytics_top = self._extract_analytics_top(outcome)
        genomics_high = self._extract_genomics_high(outcome)
        trials_top = self._extract_trials_top(outcome)

        # analytics + genomics agreement
        for gid, info in analytics_top.items():
            if gid in genomics_high:
                agreements.append(EvidenceAgreement(
                    domains=["analytics", "genomics"],
                    entity_id=gid,
                    entity_name=info.get("name", gid),
                    claim=(
                        f"{info.get('name', gid)} ranks #{info.get('rank', '?')} for yield "
                        f"and has high genomic estimated breeding value "
                        f"(GEBV={genomics_high[gid].get('gebv', '?'):.2f})"
                        if isinstance(genomics_high[gid].get("gebv"), (int, float))
                        else f"{info.get('name', gid)} is top-ranked in both analytics and genomics"
                    ),
                    confidence=min(
                        0.9,
                        0.7 + 0.1 * (2 - info.get("rank", 2)),
                    ),
                ))

        # analytics + trials agreement
        for gid, info in analytics_top.items():
            if gid in trials_top:
                agreements.append(EvidenceAgreement(
                    domains=["analytics", "trials"],
                    entity_id=gid,
                    entity_name=info.get("name", gid),
                    claim=(
                        f"{info.get('name', gid)} is top-ranked in both analytics "
                        f"and trial performance"
                    ),
                    confidence=0.80,
                ))

        return agreements

    # ── Contradiction Detection ───────────────────────────────────────────────

    def _find_contradictions(self, outcome: ExecutionOutcome) -> list[EvidenceContradiction]:
        """Find entities with conflicting signals across domain steps."""
        contradictions: list[EvidenceContradiction] = []

        analytics_top = self._extract_analytics_top(outcome)
        susceptible_germplasm = self._extract_susceptible_germplasm(outcome)
        seed_available = self._extract_seed_available_germplasm(outcome)
        seed_ops_present = any(r.domain == "seed_ops" for r in outcome.step_results)

        # Rule 1: top analytics rank + disease susceptibility
        for gid, info in analytics_top.items():
            if gid in susceptible_germplasm:
                disease = susceptible_germplasm[gid].get("disease_name", "disease")
                contradictions.append(EvidenceContradiction(
                    domain_a="analytics",
                    domain_b="pest_disease",
                    entity_id=gid,
                    entity_name=info.get("name", gid),
                    claim_a=f"{info.get('name', gid)} ranks #{info.get('rank', '?')} for yield",
                    claim_b=f"{info.get('name', gid)} is susceptible to {disease}",
                    severity="warning",
                ))

        # Rule 2: top analytics rank + no seed available
        if seed_ops_present and analytics_top:
            top_gid = min(analytics_top, key=lambda g: analytics_top[g].get("rank", 99))
            top_info = analytics_top[top_gid]
            if top_gid not in seed_available:
                contradictions.append(EvidenceContradiction(
                    domain_a="analytics",
                    domain_b="seed_ops",
                    entity_id=top_gid,
                    entity_name=top_info.get("name", top_gid),
                    claim_a=f"{top_info.get('name', top_gid)} is the top performer",
                    claim_b=f"No seed stock available for {top_info.get('name', top_gid)}",
                    severity="warning",
                ))

        return contradictions

    # ── Gap Detection ─────────────────────────────────────────────────────────

    def _find_gaps(
        self, outcome: ExecutionOutcome, params: dict[str, Any]
    ) -> list[EvidenceGap]:
        """Detect gaps from failed or empty domain steps."""
        gaps: list[EvidenceGap] = []

        for step_result in outcome.step_results:
            domain = step_result.domain
            desc, suggestion = _GAP_DESCRIPTIONS.get(
                domain,
                (f"No data available from {domain} domain",
                 f"Check {domain} service configuration and data availability"),
            )

            if step_result.status == "failed":
                impact: Literal["low", "medium", "high"] = (
                    "high"
                    if step_result.error_category == "missing_service"
                    else "medium"
                )
                gaps.append(EvidenceGap(
                    domain=domain,
                    entity_id=None,
                    description=f"{desc} (service unavailable)"
                    if step_result.error_category == "missing_service"
                    else f"{desc}: {step_result.error_message or 'unknown error'}",
                    impact=impact,
                    suggestion=suggestion,
                ))

            elif step_result.status == "success" and self._step_has_no_data(step_result):
                gaps.append(EvidenceGap(
                    domain=domain,
                    entity_id=None,
                    description=desc,
                    impact="medium",
                    suggestion=suggestion,
                ))

        return gaps

    # ── Confidence Aggregation ────────────────────────────────────────────────

    def _compute_confidence(
        self,
        outcome: ExecutionOutcome,
        agreements: list[EvidenceAgreement],
        contradictions: list[EvidenceContradiction],
        gaps: list[EvidenceGap],
    ) -> float:
        """Compute overall confidence score, clamped to [0.1, 1.0].

        Formula:
          base = 0.8
          - 0.1 per contradiction
          - 0.05 per high-impact gap
          + 0.05 per agreement
          × (steps_completed / total_steps)
        """
        base = 0.8
        base -= 0.1 * len(contradictions)
        base -= 0.05 * sum(1 for g in gaps if g.impact == "high")
        base += 0.05 * len(agreements)

        total_steps = max(len(outcome.step_results), 1)
        completion_ratio = outcome.steps_completed / total_steps
        base *= completion_ratio

        return max(0.1, min(1.0, base))

    # ── Primary Conclusion ────────────────────────────────────────────────────

    def _derive_primary_conclusion(
        self,
        outcome: ExecutionOutcome,
        agreements: list[EvidenceAgreement],
    ) -> str | None:
        """Derive the primary conclusion from the top-ranked entity.

        Prefers the analytics step's top-ranked germplasm. Falls back to the
        most-mentioned entity across all steps. Returns None when no data exists.
        """
        # Try analytics step first
        analytics_top = self._extract_analytics_top(outcome)
        if analytics_top:
            top_gid = min(analytics_top, key=lambda g: analytics_top[g].get("rank", 99))
            top_info = analytics_top[top_gid]
            name = top_info.get("name", top_gid)
            rank = top_info.get("rank", 1)
            mean = top_info.get("mean_value")
            conclusion = f"{name} is the top performer (rank #{rank})"
            if mean is not None:
                try:
                    conclusion += f" with mean value {float(mean):.2f}"
                except (TypeError, ValueError):
                    pass
            # Enrich with agreement if available
            top_agreements = [a for a in agreements if a.entity_id == top_gid]
            if top_agreements:
                domains = sorted({d for a in top_agreements for d in a.domains})
                conclusion += f", confirmed by {' and '.join(domains)}"
            return conclusion

        # Fall back to most-mentioned entity across all successful steps
        entity_counts: dict[str, int] = {}
        entity_names: dict[str, str] = {}
        for step_result in outcome.step_results:
            if step_result.status != "success":
                continue
            for eid in (step_result.entity_ids or []):
                if eid:
                    entity_counts[eid] = entity_counts.get(eid, 0) + 1

        if entity_counts:
            top_eid = max(entity_counts, key=lambda e: entity_counts[e])
            return f"Entity {top_eid} appears in {entity_counts[top_eid]} domain steps"

        return None

    # ── Caveats ───────────────────────────────────────────────────────────────

    def _build_caveats(
        self,
        contradictions: list[EvidenceContradiction],
        gaps: list[EvidenceGap],
    ) -> list[str]:
        """Convert contradictions and high-impact gaps to human-readable caveats."""
        caveats: list[str] = []

        for c in contradictions:
            caveats.append(
                f"Caution: {c.claim_a}, but {c.claim_b} "
                f"({c.severity} — {c.domain_a} vs {c.domain_b})"
            )

        for g in gaps:
            if g.impact == "high":
                caveats.append(
                    f"Data gap: {g.description}. {g.suggestion}"
                )

        return caveats

    # ── Private Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _extract_analytics_top(outcome: ExecutionOutcome) -> dict[str, dict[str, Any]]:
        """Extract top-ranked germplasm from the analytics step."""
        result: dict[str, dict[str, Any]] = {}
        for step in outcome.step_results:
            if step.domain != "analytics" or step.status != "success":
                continue
            ranking = step.records.get("ranking", {})
            if not isinstance(ranking, dict):
                continue
            for entry in ranking.get("ranked_germplasm", []):
                if not isinstance(entry, dict):
                    continue
                gid = str(entry.get("germplasm_id", "")).strip()
                if gid:
                    result[gid] = entry
        return result

    @staticmethod
    def _extract_genomics_high(outcome: ExecutionOutcome) -> dict[str, dict[str, Any]]:
        """Extract germplasm with high GEBV (top 50%) from the genomics step."""
        all_entries: list[dict[str, Any]] = []
        for step in outcome.step_results:
            if step.domain != "genomics" or step.status != "success":
                continue
            gebv_result = step.records.get("gebv_result", {})
            if isinstance(gebv_result, dict):
                all_entries.extend(gebv_result.get("entries", []))

        if not all_entries:
            return {}

        gebv_values = [
            float(e["gebv"])
            for e in all_entries
            if isinstance(e, dict) and e.get("gebv") is not None
        ]
        if not gebv_values:
            return {}

        median_gebv = sorted(gebv_values)[len(gebv_values) // 2]
        return {
            str(e["germplasm_id"]): e
            for e in all_entries
            if isinstance(e, dict)
            and e.get("germplasm_id")
            and float(e.get("gebv", 0)) >= median_gebv
        }

    @staticmethod
    def _extract_trials_top(outcome: ExecutionOutcome) -> dict[str, dict[str, Any]]:
        """Extract top-performing germplasm from the trials step entity_ids."""
        result: dict[str, dict[str, Any]] = {}
        for step in outcome.step_results:
            if step.domain != "trials" or step.status != "success":
                continue
            for eid in (step.entity_ids or []):
                if eid:
                    result[str(eid)] = {"germplasm_id": eid}
        return result

    @staticmethod
    def _extract_susceptible_germplasm(outcome: ExecutionOutcome) -> dict[str, dict[str, Any]]:
        """Extract germplasm with susceptible resistance type from pest_disease step."""
        result: dict[str, dict[str, Any]] = {}
        for step in outcome.step_results:
            if step.domain != "pest_disease" or step.status != "success":
                continue
            for profile in step.records.get("resistance_profiles", []):
                if not isinstance(profile, dict):
                    continue
                rtype = str(profile.get("resistance_type", "")).lower()
                gid = str(profile.get("germplasm_id", "")).strip()
                if gid and rtype in _SUSCEPTIBLE_TYPES:
                    result[gid] = profile
        return result

    @staticmethod
    def _extract_seed_available_germplasm(outcome: ExecutionOutcome) -> set[str]:
        """Extract germplasm IDs that have seed in stock from seed_ops step."""
        available: set[str] = set()
        for step in outcome.step_results:
            if step.domain != "seed_ops" or step.status != "success":
                continue
            for seedlot in step.records.get("seedlots", []):
                if not isinstance(seedlot, dict):
                    continue
                qty = seedlot.get("quantity") or seedlot.get("quantity_grams") or 0
                try:
                    qty_val = float(qty)
                except (TypeError, ValueError):
                    qty_val = 0.0
                if qty_val > 0:
                    gid = str(seedlot.get("germplasm_id", "")).strip()
                    if gid:
                        available.add(gid)
        return available

    @staticmethod
    def _step_has_no_data(step_result: StepResult) -> bool:
        """Return True when a successful step has no meaningful records."""
        if not step_result.records:
            return True
        # Check if all record values are empty lists/dicts
        for value in step_result.records.values():
            if isinstance(value, list) and value:
                return False
            if isinstance(value, dict) and value:
                return False
        return True
