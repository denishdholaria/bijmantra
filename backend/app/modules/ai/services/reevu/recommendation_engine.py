"""
Recommendation Engine

Given a recommendation query ("which varieties should I advance?"), produces a
ranked list of germplasm entries backed by evidence from every available domain.

Each entry carries:
- composite_score: weighted combination of trait_performance, genomic_prediction,
  disease_resistance, and seed_availability
- classification: "advance" / "drop" / "retest" based on configurable thresholds
- evidence_chain: per-factor breakdown with raw values and source domain
- caveats: contradictions from SynthesisResult that affect this entry

Runs after EvidenceSynthesisEngine when the query intent is "recommend" or "advance".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.modules.ai.services.reevu.evidence_synthesis_engine import (
    SynthesisResult,
    EvidenceContradiction,
)
from app.modules.ai.services.reevu.step_executor import ExecutionOutcome, EvidenceRef


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class EvidenceFactor:
    """A single factor contributing to a germplasm's composite score."""
    factor_name: str        # e.g. "trait_performance"
    value: float            # normalized 0–1
    raw_value: str          # e.g. "4.2 t/ha"
    source_domain: str      # e.g. "analytics"
    evidence_refs: list[str]
    weight: float


@dataclass
class RecommendationEntry:
    """A single ranked germplasm recommendation."""
    rank: int
    germplasm_id: str
    germplasm_name: str
    composite_score: float
    classification: Literal["advance", "drop", "retest"]
    evidence_chain: list[EvidenceFactor] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)


@dataclass
class RecommendationResult:
    """Full recommendation output for a query."""
    ranked_entries: list[RecommendationEntry]
    classification: dict[str, list[str]]    # advance/drop/retest → germplasm names
    weights_used: dict[str, float]
    factors_available: list[str]
    factors_missing: list[str]
    evidence_refs: list[EvidenceRef] = field(default_factory=list)


# ── Resistance type → score mapping ──────────────────────────────────────────

_RESISTANCE_SCORES: dict[str, float] = {
    "complete": 1.0,
    "dominant": 0.9,
    "partial": 0.7,
    "quantitative": 0.6,
    "recessive": 0.5,
    "moderately_susceptible": 0.3,
    "ms": 0.3,
    "susceptible": 0.1,
    "s": 0.1,
    "highly_susceptible": 0.0,
    "hs": 0.0,
}

# Recommendation intent keywords
_RECOMMENDATION_PHRASES: tuple[str, ...] = (
    "advance", "recommend", "select", "which varieties", "should i",
    "should we", "drop", "retest", "best germplasm", "top entries",
    "which entries", "which lines",
)

# Weight boost keywords
_WEIGHT_BOOSTS: dict[str, str] = {
    "disease resistance": "disease_resistance",
    "disease": "disease_resistance",
    "resistance": "disease_resistance",
    "yield": "trait_performance",
    "trait": "trait_performance",
    "performance": "trait_performance",
    "genomic": "genomic_prediction",
    "gebv": "genomic_prediction",
    "seed": "seed_availability",
    "availability": "seed_availability",
    "stock": "seed_availability",
}


class RecommendationEngine:
    """Rank germplasm entries by weighted multi-factor evidence.

    Usage:
        engine = RecommendationEngine()
        result = engine.recommend(outcome, synthesis, query)
    """

    DEFAULT_WEIGHTS: dict[str, float] = {
        "trait_performance": 0.4,
        "genomic_prediction": 0.3,
        "disease_resistance": 0.2,
        "seed_availability": 0.1,
    }

    ADVANCE_THRESHOLD: float = 0.7
    DROP_THRESHOLD: float = 0.3

    # ── Public API ────────────────────────────────────────────────────────────

    def recommend(
        self,
        outcome: ExecutionOutcome,
        synthesis: SynthesisResult,
        query: str,
        user_weights: dict[str, float] | None = None,
    ) -> RecommendationResult:
        """Produce a ranked recommendation from all available domain evidence.

        Args:
            outcome: ExecutionOutcome from StepExecutor.execute_plan().
            synthesis: SynthesisResult from EvidenceSynthesisEngine.synthesize().
            query: The user's original query string.
            user_weights: Optional explicit weight overrides.

        Returns:
            RecommendationResult with ranked entries, classification, and evidence.
        """
        # 1. Extract all available factors
        trait_factors = self._extract_trait_performance(outcome)
        genomic_factors = self._extract_genomic_prediction(outcome)
        disease_factors = self._extract_disease_resistance(outcome)
        seed_factors = self._extract_seed_availability(outcome)

        factor_map: dict[str, dict[str, float] | None] = {
            "trait_performance": trait_factors,
            "genomic_prediction": genomic_factors,
            "disease_resistance": disease_factors,
            "seed_availability": seed_factors,
        }

        factors_available = [k for k, v in factor_map.items() if v is not None]
        factors_missing = [k for k, v in factor_map.items() if v is None]

        # 2. Collect all germplasm IDs across all successful steps
        all_germplasm: dict[str, str] = {}  # id → name
        for step in outcome.step_results:
            if step.status != "success":
                continue
            for eid in (step.entity_ids or []):
                if eid and eid not in all_germplasm:
                    all_germplasm[eid] = self._resolve_name(eid, outcome)

        if not all_germplasm:
            return RecommendationResult(
                ranked_entries=[],
                classification={"advance": [], "drop": [], "retest": []},
                weights_used={},
                factors_available=[],
                factors_missing=list(self.DEFAULT_WEIGHTS.keys()),
            )

        # 3. Parse and normalize weights
        raw_weights = user_weights or self._parse_user_weights(query)
        weights = self._normalize_weights(raw_weights, factors_available)

        # 4. Build contradiction lookup for caveats
        contradictions_by_entity: dict[str, list[EvidenceContradiction]] = {}
        for c in synthesis.contradictions:
            contradictions_by_entity.setdefault(c.entity_id, []).append(c)

        # 5. Score and classify each germplasm
        entries: list[RecommendationEntry] = []
        for gid, gname in all_germplasm.items():
            per_factor: dict[str, float] = {}
            evidence_chain: list[EvidenceFactor] = []

            for fname in factors_available:
                fdata = factor_map[fname]
                if fdata is None or gid not in fdata:
                    continue
                val = fdata[gid]
                w = weights.get(fname, 0.0)
                per_factor[fname] = val
                evidence_chain.append(EvidenceFactor(
                    factor_name=fname,
                    value=val,
                    raw_value=self._format_raw_value(fname, val, gid, outcome),
                    source_domain=self._factor_domain(fname),
                    evidence_refs=[f"{self._factor_domain(fname)}:germplasm:{gid}"],
                    weight=w,
                ))

            if not per_factor:
                continue

            score = self._compute_composite_score(per_factor, weights)
            classification = self._classify(score)

            # Attach caveats from synthesis contradictions
            caveats = [
                f"{c.claim_a}, but {c.claim_b}"
                for c in contradictions_by_entity.get(gid, [])
            ]

            entries.append(RecommendationEntry(
                rank=0,  # assigned after sorting
                germplasm_id=gid,
                germplasm_name=gname,
                composite_score=score,
                classification=classification,
                evidence_chain=evidence_chain,
                caveats=caveats,
            ))

        # 6. Sort descending by composite_score and assign ranks
        entries.sort(key=lambda e: e.composite_score, reverse=True)
        for i, entry in enumerate(entries):
            entry.rank = i + 1

        # 7. Build classification dict
        classification_dict: dict[str, list[str]] = {"advance": [], "drop": [], "retest": []}
        for entry in entries:
            classification_dict[entry.classification].append(entry.germplasm_name)

        return RecommendationResult(
            ranked_entries=entries,
            classification=classification_dict,
            weights_used=weights,
            factors_available=factors_available,
            factors_missing=factors_missing,
        )

    def _is_recommendation_query(self, query: str) -> bool:
        """Return True when the query expresses recommendation/advancement intent."""
        q = query.lower()
        return any(phrase in q for phrase in _RECOMMENDATION_PHRASES)

    # ── Factor Extraction ─────────────────────────────────────────────────────

    def _extract_trait_performance(
        self, outcome: ExecutionOutcome
    ) -> dict[str, float] | None:
        """Extract per-germplasm mean values from analytics step, normalized 0–1."""
        raw: dict[str, float] = {}
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
                val = entry.get("mean_value")
                if gid and val is not None:
                    try:
                        raw[gid] = float(val)
                    except (TypeError, ValueError):
                        pass

        return self._normalize_dict(raw) if raw else None

    def _extract_genomic_prediction(
        self, outcome: ExecutionOutcome
    ) -> dict[str, float] | None:
        """Extract GEBV per germplasm from genomics step, normalized 0–1."""
        raw: dict[str, float] = {}
        for step in outcome.step_results:
            if step.domain != "genomics" or step.status != "success":
                continue
            gebv_result = step.records.get("gebv_result", {})
            if not isinstance(gebv_result, dict):
                continue
            for entry in gebv_result.get("entries", []):
                if not isinstance(entry, dict):
                    continue
                gid = str(entry.get("germplasm_id", "")).strip()
                val = entry.get("gebv")
                if gid and val is not None:
                    try:
                        raw[gid] = float(val)
                    except (TypeError, ValueError):
                        pass

        return self._normalize_dict(raw) if raw else None

    def _extract_disease_resistance(
        self, outcome: ExecutionOutcome
    ) -> dict[str, float] | None:
        """Extract resistance scores from pest_disease step, normalized 0–1.

        Maps resistance_type strings to a 0–1 scale where 1.0 = fully resistant
        and 0.0 = highly susceptible.
        """
        raw: dict[str, float] = {}
        for step in outcome.step_results:
            if step.domain != "pest_disease" or step.status != "success":
                continue
            for profile in step.records.get("resistance_profiles", []):
                if not isinstance(profile, dict):
                    continue
                gid = str(profile.get("germplasm_id", "")).strip()
                rtype = str(profile.get("resistance_type", "")).lower()
                if gid and rtype:
                    score = _RESISTANCE_SCORES.get(rtype, 0.5)
                    # Keep the worst score if multiple profiles for same germplasm
                    if gid not in raw or score < raw[gid]:
                        raw[gid] = score

        return raw if raw else None

    def _extract_seed_availability(
        self, outcome: ExecutionOutcome
    ) -> dict[str, float] | None:
        """Extract binary seed availability from seed_ops step (1.0 = in stock)."""
        result: dict[str, float] = {}
        found_seed_ops = False
        for step in outcome.step_results:
            if step.domain != "seed_ops" or step.status != "success":
                continue
            found_seed_ops = True
            for seedlot in step.records.get("seedlots", []):
                if not isinstance(seedlot, dict):
                    continue
                gid = str(seedlot.get("germplasm_id", "")).strip()
                qty = seedlot.get("quantity") or seedlot.get("quantity_grams") or 0
                try:
                    qty_val = float(qty)
                except (TypeError, ValueError):
                    qty_val = 0.0
                if gid:
                    # 1.0 if any seedlot has stock; 0.0 if all are empty
                    if qty_val > 0:
                        result[gid] = 1.0
                    elif gid not in result:
                        result[gid] = 0.0

        return result if found_seed_ops else None

    # ── Weight Management ─────────────────────────────────────────────────────

    def _parse_user_weights(self, query: str) -> dict[str, float]:
        """Extract weight adjustments from the user query.

        Doubles the weight of any factor mentioned with a priority keyword.
        Returns DEFAULT_WEIGHTS unchanged when no priority keywords are found.
        """
        q = query.lower()
        priority_keywords = (
            "prioritize", "most important", "focus on", "care about",
            "weight", "emphasize", "critical", "key factor",
        )
        has_priority = any(kw in q for kw in priority_keywords)
        if not has_priority:
            return dict(self.DEFAULT_WEIGHTS)

        weights = dict(self.DEFAULT_WEIGHTS)
        for phrase, factor in _WEIGHT_BOOSTS.items():
            if phrase in q:
                weights[factor] = weights.get(factor, 0.0) * 2.0
                break  # apply only the first match

        return weights

    def _normalize_weights(
        self, weights: dict[str, float], available_factors: list[str]
    ) -> dict[str, float]:
        """Exclude missing factors and renormalize remaining weights to sum 1.0."""
        filtered = {k: v for k, v in weights.items() if k in available_factors}
        total = sum(filtered.values())
        if total <= 0:
            # Fallback: equal weights
            n = len(available_factors)
            return {k: 1.0 / n for k in available_factors} if n > 0 else {}
        return {k: v / total for k, v in filtered.items()}

    # ── Scoring and Classification ────────────────────────────────────────────

    def _compute_composite_score(
        self, factors: dict[str, float], weights: dict[str, float]
    ) -> float:
        """Weighted sum of available factor values."""
        return sum(
            factors[k] * weights.get(k, 0.0)
            for k in factors
            if k in weights
        )

    def _classify(self, score: float) -> Literal["advance", "drop", "retest"]:
        """Classify a composite score into advance / drop / retest."""
        if score >= self.ADVANCE_THRESHOLD:
            return "advance"
        if score < self.DROP_THRESHOLD:
            return "drop"
        return "retest"

    # ── Private Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _normalize_dict(raw: dict[str, float]) -> dict[str, float]:
        """Min-max normalize a dict of floats to [0, 1].

        When all values are equal (zero range), returns 1.0 for all entries.
        """
        if not raw:
            return {}
        min_val = min(raw.values())
        max_val = max(raw.values())
        rng = max_val - min_val
        if rng == 0:
            return {k: 1.0 for k in raw}
        return {k: (v - min_val) / rng for k, v in raw.items()}

    @staticmethod
    def _factor_domain(factor_name: str) -> str:
        return {
            "trait_performance": "analytics",
            "genomic_prediction": "genomics",
            "disease_resistance": "pest_disease",
            "seed_availability": "seed_ops",
        }.get(factor_name, factor_name)

    @staticmethod
    def _format_raw_value(
        factor_name: str, normalized_value: float, gid: str, outcome: ExecutionOutcome
    ) -> str:
        """Format a human-readable raw value string for the evidence chain."""
        if factor_name == "trait_performance":
            for step in outcome.step_results:
                if step.domain != "analytics" or step.status != "success":
                    continue
                for entry in step.records.get("ranking", {}).get("ranked_germplasm", []):
                    if str(entry.get("germplasm_id", "")) == gid:
                        mv = entry.get("mean_value")
                        if mv is not None:
                            return f"{float(mv):.2f} (mean)"
        if factor_name == "genomic_prediction":
            for step in outcome.step_results:
                if step.domain != "genomics" or step.status != "success":
                    continue
                for entry in step.records.get("gebv_result", {}).get("entries", []):
                    if str(entry.get("germplasm_id", "")) == gid:
                        gebv = entry.get("gebv")
                        if gebv is not None:
                            return f"GEBV={float(gebv):.3f}"
        if factor_name == "disease_resistance":
            return f"resistance_score={normalized_value:.2f}"
        if factor_name == "seed_availability":
            return "in stock" if normalized_value >= 1.0 else "out of stock"
        return f"{normalized_value:.3f}"

    @staticmethod
    def _resolve_name(gid: str, outcome: ExecutionOutcome) -> str:
        """Try to find a human-readable name for a germplasm ID from step records."""
        for step in outcome.step_results:
            if step.status != "success":
                continue
            # Check analytics rankings
            for entry in step.records.get("ranking", {}).get("ranked_germplasm", []):
                if str(entry.get("germplasm_id", "")) == gid:
                    name = entry.get("name") or entry.get("germplasm_name")
                    if name:
                        return str(name)
            # Check germplasm records
            for g in step.records.get("germplasm", []):
                if isinstance(g, dict) and str(g.get("id", "")) == gid:
                    name = g.get("germplasm_name") or g.get("name")
                    if name:
                        return str(name)
        return gid  # fall back to ID
