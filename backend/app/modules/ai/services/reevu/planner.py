"""
REEVU Multi-Domain Planner — Stage C

Decomposes compound user queries into explicit multi-step execution plans
with domain tags, dependency ordering, and deterministic routing markers.
"""

from __future__ import annotations

import logging
import re
from os import getenv
from typing import TYPE_CHECKING
from uuid import uuid4

from app.schemas.reevu_plan import PlanStep, ReevuExecutionPlan

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.modules.ai.services.reevu.domain_embedding_service import DomainEmbeddingService

logger = logging.getLogger(__name__)

# ── domain keyword registry ──────────────────────────────────────────
# Maps keywords/phrases to canonical domain tags.
# Order is important: more specific patterns checked first.
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "genomics": [
        "genomic", "genome", "snp", "marker", "qtl", "gwas", "haplotype",
        "allele", "genotype", "genotyping", "sequencing", "dna", "molecular",
        "linkage", "polymorphism",
    ],
    "weather": [
        "weather", "climate", "rainfall", "temperature", "humidity",
        "frost", "drought", "precipitation", "gdd", "growing degree",
        "solar radiation", "wind",
    ],
    "trials": [
        "trial", "experiment", "field test", "plot", "nursery",
        "replication", "block", "treatment", "location",
    ],
    "field": [
        "field", "plot", "location", "planting", "harvest date",
        "crop calendar", "season", "field layout", "rotation",
        "field management", "field history", "planted", "sowing",
    ],
    "phenotyping": [
        "observation", "phenotype", "trait data", "field data", "scoring",
        "measurement", "phenotypic", "observation variable", "phenotyping",
        "plant height", "grain yield", "days to flowering",
    ],
    "protocols": [
        "protocol", "protocols", "speed breeding", "photoperiod", "growth chamber",
        "generation", "generations per year", "accelerated breeding",
    ],
    "analytics": [
        "statistic", "analysis", "trend", "predict", "forecast",
        "model", "regression", "correlation", "compare", "rank",
        "performance", "yield gap", "stability",
    ],
    "breeding": [
        "breed", "cross", "hybrid", "variety", "cultivar", "germplasm",
        "parent", "selection", "pedigree", "trait", "phenotype",
        "resistance", "tolerance", "seed", "crop",
    ],
    "seed_ops": [
        "seed lot", "seed stock", "inventory", "seed request", "availability",
        "seed quantity", "storage", "viability", "accession inventory",
        "seed bank", "seed supply", "germplasm stock",
    ],
    "soil": [
        "soil", "nutrient", "pH", "organic matter", "nitrogen", "phosphorus",
        "potassium", "soil type", "soil health", "fertility", "soil analysis",
        "soil test", "NPK", "soil profile", "soil texture", "soil moisture",
    ],
    "pest_disease": [
        "disease", "pest", "pathogen", "insect", "fungal",
        "bacterial", "rust", "blight", "wilt", "aphid", "borer",
        "susceptible", "susceptibility", "scouting",
        "mildew", "nematode", "pest pressure", "disease pressure",
        "disease resistance", "pest scouting",
    ],
    "sensors": [
        "sensor", "IoT", "telemetry", "soil moisture sensor", "data logger",
        "sensor reading", "device reading", "environmental data",
        "monitoring station", "weather station sensor",
    ],
    "spatial": [
        "map", "spatial", "nearby", "within", "radius", "proximity",
        "GIS", "region", "km", "miles", "area", "near", "closest",
        "distance", "coordinates", "location map",
    ],
    "climate": [
        "climate change", "SSP", "future climate", "climate risk",
        "climate projection", "global warming", "adaptation", "2050",
        "temperature rise", "rainfall change", "climate scenario",
    ],
    "commercial": [
        "variety release", "market demand", "licensing", "royalty",
        "commercial", "market", "price", "revenue", "released variety",
        "variety registration", "seed market",
    ],
    "harvest": [
        "harvest", "yield data", "quality grade", "post-harvest",
        "storage loss", "moisture content", "harvested", "crop yield",
        "harvest record", "threshing", "milling",
    ],
    "nursery": [
        "nursery", "seedling", "transplant", "irrigation schedule",
        "fertilizer schedule", "crop management", "growth stage",
        "planting schedule", "nursery management",
    ],
    "vision": [
        "identify disease", "plant image", "leaf photo", "visual scan",
        "image analysis", "photo", "camera", "scan leaf",
        "disease identification", "plant counting",
    ],
}

# Domain dependency ordering (lower index = earlier in plan).
DOMAIN_ORDER: dict[str, int] = {
    "weather": 0,
    "trials": 1,
    "field": 2,
    "sensors": 3,
    "phenotyping": 4,
    "genomics": 5,
    "breeding": 6,
    "seed_ops": 7,
    "soil": 8,
    "pest_disease": 9,
    "protocols": 10,
    "climate": 11,
    "commercial": 12,
    "harvest": 13,
    "nursery": 14,
    "vision": 15,
    "analytics": 16,
    "spatial": 17,
}

EXPLICIT_WEATHER_TERMS: tuple[str, ...] = (
    "weather",
    "climate",
    "rainfall",
    "temperature",
    "humidity",
    "frost",
    "precipitation",
    "gdd",
    "growing degree",
    "solar radiation",
    "wind",
    "forecast",
)

BREEDING_STRESS_TRAIT_PHRASES: tuple[str, ...] = (
    "drought tolerance",
    "drought resistance",
    "drought resistant",
)

BREEDING_ENTITY_TERMS: tuple[str, ...] = (
    "breed",
    "breeding",
    "cross",
    "hybrid",
    "variety",
    "varieties",
    "cultivar",
    "cultivars",
    "germplasm",
    "accession",
    "line",
    "lines",
    "parent",
    "pedigree",
)

PHENOTYPING_OBSERVATION_TERMS: tuple[str, ...] = (
    "observation",
    "observations",
    "phenotype",
    "phenotypic",
    "phenotyping",
    "trait data",
    "field data",
    "scoring",
    "measurement",
    "observation variable",
    "plant height",
    "grain yield",
    "days to flowering",
)

FIELD_OPS_TERMS: tuple[str, ...] = (
    "field",
    "plot",
    "location",
    "planting",
    "harvest date",
    "crop calendar",
    "season",
    "field layout",
    "rotation",
    "field management",
    "field history",
    "planted",
    "sowing",
)

TRIAL_EXPLICIT_TERMS: tuple[str, ...] = (
    "trial",
    "trials",
    "experiment",
    "experiments",
    "field test",
    "nursery",
    "replication",
    "block",
    "treatment",
)

SEED_OPS_TERMS: tuple[str, ...] = (
    "seed lot",
    "seedlot",
    "seed stock",
    "inventory",
    "seed request",
    "seed quantity",
    "storage",
    "viability",
    "seed bank",
    "seed supply",
    "germplasm stock",
)

# Function name prefixes that indicate deterministic computation.
DETERMINISTIC_PREFIXES: tuple[str, ...] = (
    "calculate_", "analyze_", "predict_", "compute_", "estimate_",
)


def _dependency_hints(domains: list[str]) -> dict[str, set[str]]:
    available = set(domains)
    hints: dict[str, set[str]] = {domain: set() for domain in domains}

    if "weather" in available and "trials" in available:
        hints["weather"].add("trials")
    if "field" in available and "trials" in available:
        hints["field"].add("trials")
    if "weather" in available and "field" in available:
        hints["weather"].add("field")
    if "breeding" in available and "trials" in available:
        hints["breeding"].add("trials")
    if "phenotyping" in available and "trials" in available:
        hints["phenotyping"].add("trials")
    if "genomics" in available and "breeding" in available:
        hints["genomics"].add("breeding")
    if "seed_ops" in available and "breeding" in available:
        hints["seed_ops"].add("breeding")
    if "soil" in available and "field" in available:
        hints["soil"].add("field")
    if "sensors" in available and "field" in available:
        hints["sensors"].add("field")
    if "climate" in available and "field" in available:
        hints["climate"].add("field")
    if "commercial" in available and "breeding" in available:
        hints["commercial"].add("breeding")
    if "harvest" in available and "trials" in available:
        hints["harvest"].add("trials")
    if "harvest" in available and "field" in available:
        hints["harvest"].add("field")
    if "nursery" in available and "field" in available:
        hints["nursery"].add("field")
    if "pest_disease" in available and "breeding" in available:
        hints["pest_disease"].add("breeding")
    if "pest_disease" in available and "trials" in available:
        hints["pest_disease"].add("trials")
    if "protocols" in available and "breeding" in available:
        hints["protocols"].add("breeding")
    if "analytics" in available:
        hints["analytics"].update(domain for domain in domains if domain != "analytics")

    return hints


def _normalize_tokens(text: str) -> list[str]:
    """Lightweight token normalization and stemming."""
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = text.split()
    stemmed = []
    for w in words:
        if w.endswith('ing') and len(w) > 4:
            stemmed.append(w[:-3])
        elif w.endswith('ies') and len(w) > 4:
            stemmed.append(w[:-3] + 'y')
        elif w.endswith('s') and len(w) > 3 and not w.endswith('ss'):
            stemmed.append(w[:-1])
        elif w.endswith('ed') and len(w) > 4:
            stemmed.append(w[:-2])
        else:
            stemmed.append(w)
    return stemmed

def _nlp_detect_domains(message: str) -> dict[str, float]:
    """NLP-assisted domain detection with scoring."""
    message_lower = message.lower()
    tokens = _normalize_tokens(message)
    token_set = set(tokens)
    
    scores: dict[str, float] = {d: 0.0 for d in DOMAIN_ORDER.keys()}
    
    # 1. Base keyword matching with lemmatization
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if (
                (" " in kw and kw in message_lower)
                or (" " not in kw and re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", message_lower))
            ):
                scores[domain] += 1.0
            else:
                kw_tokens = _normalize_tokens(kw)
                if len(kw_tokens) == 1 and kw_tokens[0] in token_set:
                    scores[domain] += 0.8
                elif len(kw_tokens) > 1 and all(k in token_set for k in kw_tokens):
                    scores[domain] += 0.8

    # 2. Implicit / Phrase-level cues
    implicit_cues = {
        "sowing window": ["weather", "analytics"],
        "soil moisture": ["weather"],
        "genomic selection": ["analytics"],
        "gblup": ["analytics"],
        "gebv": ["analytics"],
        "recommend": ["analytics"],
        "recommendation": ["analytics"],
        "top performer": ["analytics"],
        "top performers": ["analytics"],
        "best performer": ["analytics"],
        "best performers": ["analytics"],
        "performed best": ["analytics"],
        "compute": ["analytics"],
        "calculate": ["analytics"],
        "assess": ["analytics"],
        "cross validation": ["analytics"],
        "accuracy": ["analytics"],
        "protein": ["breeding"],
        "entries": ["breeding"],
        "sorghum": ["breeding"],
        "pearl millet": ["breeding"],
        "chickpea": ["breeding"],
        "cotton": ["breeding"],
        "rice": ["breeding"],
        "wheat": ["breeding"],
        "maize": ["breeding"],
        "soybean": ["breeding"],
        "disease pattern": ["analytics"],
        "selection index": ["analytics"],
    }
    
    # Remove hyphens for implicit phrase matching
    msg_clean = message_lower.replace("-", " ")
    for phrase, domains in implicit_cues.items():
        if phrase in msg_clean:
            for d in domains:
                scores[d] += 1.5

    # 3. Contextual Negative Cues (Disambiguation)
    if "solar radiation trend" in message_lower:
        scores["analytics"] -= 2.0
    if "snps" in message_lower or "snp markers" in message_lower:
        if "disease resistance" in message_lower and "germplasm" in message_lower:
            # For purely genomics questions that mention resistance/germplasm as context
            scores["breeding"] -= 2.0

    # Drought-tolerance trait questions should stay on breeding/trial surfaces unless
    # the user also asks explicitly for weather or climate context.
    if any(phrase in message_lower for phrase in BREEDING_STRESS_TRAIT_PHRASES) and not any(
        term in message_lower for term in EXPLICIT_WEATHER_TERMS
    ):
        scores["weather"] = max(0.0, scores["weather"] - 1.0)

    # Observation-first phenotype questions should not route to breeding only
    # because they contain generic words such as "trait" or "phenotype".
    if scores.get("phenotyping", 0.0) > 0 and any(
        term in message_lower for term in PHENOTYPING_OBSERVATION_TERMS
    ) and not any(term in message_lower for term in BREEDING_ENTITY_TERMS):
        scores["breeding"] = max(0.0, scores["breeding"] - 1.0)

    if scores.get("field", 0.0) > 0 and any(
        term in message_lower for term in FIELD_OPS_TERMS
    ) and not any(term in message_lower for term in TRIAL_EXPLICIT_TERMS):
        scores["trials"] = max(0.0, scores["trials"] - 1.0)

    if scores.get("field", 0.0) > 0 and any(
        term in message_lower for term in FIELD_OPS_TERMS
    ) and not any(term in message_lower for term in BREEDING_ENTITY_TERMS):
        scores["breeding"] = max(0.0, scores["breeding"] - 2.0)

    if scores.get("phenotyping", 0.0) > 0 and any(
        term in message_lower for term in PHENOTYPING_OBSERVATION_TERMS
    ) and not any(
        term in message_lower
        for term in (
            "plot",
            "location",
            "planting",
            "harvest date",
            "crop calendar",
            "field layout",
            "rotation",
            "field management",
            "field history",
            "planted",
            "sowing",
        )
    ):
        scores["field"] = max(0.0, scores["field"] - 1.0)

    if scores.get("seed_ops", 0.0) > 0 and any(
        term in message_lower for term in SEED_OPS_TERMS
    ) and not any(term in message_lower for term in BREEDING_ENTITY_TERMS):
        scores["breeding"] = max(0.0, scores["breeding"] - 1.0)

    return scores

def _detect_domains(message: str) -> list[str]:
    """Return sorted list of domains detected in the user message."""
    scores = _nlp_detect_domains(message)
    detected = {domain for domain, score in scores.items() if score >= 0.8}
    return sorted(detected, key=lambda d: DOMAIN_ORDER.get(d, 99))



def _step_description(domain: str) -> str:
    """Generate a brief description for a plan step given a domain."""
    descriptions = {
        "weather": "Retrieve weather and climate data relevant to the query",
        "trials": "Query trial/experiment data for matching conditions",
        "field": "Retrieve field location, layout, and crop calendar data",
        "phenotyping": "Retrieve phenotypic observations and trait distribution data",
        "genomics": "Retrieve genomic and molecular marker information",
        "breeding": "Fetch breeding program, germplasm, and trait data",
        "seed_ops": "Retrieve seed inventory, availability, and seedlot records",
        "soil": "Retrieve soil analysis records, nutrient levels, and soil health indicators",
        "pest_disease": "Retrieve disease resistance profiles and pest/disease scouting records",
        "sensors": "Retrieve IoT sensor readings, telemetry summaries, and device status",
        "spatial": "Retrieve spatially proximate locations, trials, or entities within a radius",
        "climate": "Retrieve climate projections, crop suitability scores, and adaptation recommendations",
        "commercial": "Retrieve variety release status, market demand, and commercial licensing data",
        "harvest": "Retrieve harvest records, yield summaries, and quality grading results",
        "nursery": "Retrieve nursery operations, seedling inventory, and crop management events",
        "vision": "Analyse plant images for disease identification, counting, or morphology",
        "protocols": "Retrieve breeding protocol or speed-breeding configuration data",
        "analytics": "Run analytical computations and statistical comparisons",
    }
    return descriptions.get(domain, f"Execute {domain} data retrieval")



def _expected_outputs(domain: str) -> list[str]:
    """Default expected output types per domain."""
    outputs = {
        "weather": ["weather_records", "gdd_values"],
        "trials": ["trial_records", "plot_data"],
        "field": ["location_records", "field_layouts", "crop_calendar_events", "season_data"],
        "phenotyping": ["observation_records", "trait_summaries", "observation_statistics"],
        "genomics": ["marker_data", "genomic_profiles"],
        "breeding": ["germplasm_list", "trait_summaries"],
        "seed_ops": ["seedlot_records", "inventory_levels", "request_status"],
        "soil": ["soil_analysis_records", "nutrient_summaries", "soil_health_indicators"],
        "pest_disease": ["resistance_profiles", "scouting_records", "stress_observations"],
        "sensors": ["sensor_readings", "telemetry_summaries", "device_status"],
        "spatial": ["spatial_results", "proximity_records", "region_summaries"],
        "climate": ["climate_projections", "crop_suitability", "adaptation_recommendations"],
        "commercial": ["variety_releases", "market_demand", "cost_analysis"],
        "harvest": ["harvest_records", "yield_summary", "quality_grades"],
        "nursery": ["nursery_operations", "transplanting_schedules", "crop_management_events"],
        "vision": ["classification_result", "confidence_score", "management_recommendation"],
        "protocols": ["protocol_records", "protocol_conditions"],
        "analytics": ["comparison_table", "ranked_recommendations"],
    }
    return outputs.get(domain, [f"{domain}_results"])


def _env_flag(name: str, default: bool) -> bool:
    """Read a boolean feature flag from environment variables."""
    raw_value = getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


class ReevuPlanner:
    """Decomposes compound queries into multi-domain execution plans."""

    NLP_CONFIDENCE_THRESHOLD: float = 0.6

    def __init__(
        self,
        *,
        nlp_enabled: bool | None = None,
        dag_enabled: bool | None = None,
        embedding_service: "DomainEmbeddingService | None" = None,
    ) -> None:
        self.nlp_enabled = (
            _env_flag("REEVU_PLANNER_NLP_ENABLED", True)
            if nlp_enabled is None
            else nlp_enabled
        )
        self.dag_enabled = (
            _env_flag("REEVU_PLANNER_DAG_ENABLED", True)
            if dag_enabled is None
            else dag_enabled
        )
        self._embedding_service = embedding_service

    def _detect_domains_nlp(self, message: str) -> tuple[list[str], float]:
        """Advanced domain detection path; currently deterministic and patchable in tests."""
        if not self.nlp_enabled:
            return [], 0.0
        domains = _detect_domains(message)
        confidence = 1.0 if domains else 0.0
        return domains, confidence

    def _detect_domains_keywords(self, message: str) -> list[str]:
        """Keyword fallback domain detection path."""
        if not self.nlp_enabled:
            return []
        return _detect_domains(message)

    def _build_domain_order_dag(self, domains: list[str]) -> list[str]:
        """Build ordered domain execution path from dependency DAG."""
        unique_domains = sorted(set(domains), key=lambda d: DOMAIN_ORDER.get(d, 99))
        dependency_map = _dependency_hints(unique_domains)
        in_degree = {
            domain: len(dependency_map.get(domain, set()))
            for domain in unique_domains
        }
        dependents: dict[str, list[str]] = {domain: [] for domain in unique_domains}

        for domain, prerequisites in dependency_map.items():
            for prerequisite in prerequisites:
                if prerequisite in dependents:
                    dependents[prerequisite].append(domain)

        ready = sorted(
            [domain for domain, degree in in_degree.items() if degree == 0],
            key=lambda domain: DOMAIN_ORDER.get(domain, 99),
        )
        ordered: list[str] = []

        while ready:
            domain = ready.pop(0)
            ordered.append(domain)

            for dependent in dependents.get(domain, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    ready.append(dependent)
                    ready.sort(key=lambda candidate: DOMAIN_ORDER.get(candidate, 99))

        if len(ordered) != len(unique_domains):
            return unique_domains

        return ordered

    def build_plan(
        self,
        message: str,
        *,
        function_call_name: str | None = None,
    ) -> ReevuExecutionPlan:
        """Build an execution plan for the given user message.

        Returns a single-step plan if only one domain is detected,
        or a multi-step plan with dependencies for compound queries.
        """
        fallback_reasons: list[str] = []

        try:
            domains, confidence = self._detect_domains_nlp(message)
            if confidence < self.NLP_CONFIDENCE_THRESHOLD:
                fallback_reasons.append("low_confidence_threshold")
                domains = self._detect_domains_keywords(message)
        except Exception:
            fallback_reasons.append("nlp_exception")
            domains = self._detect_domains_keywords(message)

        valid_domains = [domain for domain in domains if domain in DOMAIN_ORDER]
        if len(valid_domains) != len(domains):
            fallback_reasons.append("ambiguous_domain_filtered")
        domains = valid_domains

        if not domains:
            # Default to breeding domain if nothing detected.
            domains = ["breeding"]
            fallback_reasons.append("default_breeding_fallback")

        try:
            domains = self._build_domain_order_dag(domains)
        except Exception:
            fallback_reasons.append("dag_builder_error")
            domains = sorted(set(domains), key=lambda d: DOMAIN_ORDER.get(d, 99))

        dependency_map = _dependency_hints(domains)
        is_compound = len(domains) > 1
        steps: list[PlanStep] = []
        step_ids_by_domain: dict[str, str] = {}

        for idx, domain in enumerate(domains):
            step_id = f"step-{idx + 1}"
            is_deterministic = bool(
                domain == "analytics"
                or (function_call_name is not None and function_call_name.startswith(DETERMINISTIC_PREFIXES))
            )

            prerequisites: list[str] = []
            if self.dag_enabled:
                prerequisites = [
                    step_ids_by_domain[prerequisite_domain]
                    for prerequisite_domain in domains
                    if prerequisite_domain in dependency_map.get(domain, set())
                    and prerequisite_domain in step_ids_by_domain
                ]

            steps.append(
                PlanStep(
                    step_id=step_id,
                    domain=domain,
                    description=_step_description(domain),
                    prerequisites=prerequisites,
                    expected_outputs=_expected_outputs(domain),
                    completed=False,
                    deterministic=is_deterministic,
                )
            )
            step_ids_by_domain[domain] = step_id

        return ReevuExecutionPlan(
            plan_id=f"plan-{uuid4().hex[:8]}",
            original_query=message,
            is_compound=is_compound,
            steps=steps,
            domains_involved=domains,
            metadata={"fallback_reasons": fallback_reasons},
        )

    async def build_plan_async(
        self,
        message: str,
        db: "AsyncSession | None" = None,
        *,
        function_call_name: str | None = None,
    ) -> ReevuExecutionPlan:
        """Async version of build_plan that optionally uses embedding detection.

        Runs keyword detection first, then — if an embedding service and a db
        session are both available — runs embedding detection and fuses scores
        using ``max(keyword_score, embedding_score)`` per domain.

        If the embedding call fails for any reason, a warning is logged and
        keyword-only scores are used (safe fallback).

        Args:
            message:            The user's query string.
            db:                 An open async SQLAlchemy session (optional).
            function_call_name: Optional function name for deterministic routing.

        Returns:
            A :class:`ReevuExecutionPlan` built from the fused domain scores.
        """
        fallback_reasons: list[str] = []

        # ── Step 1: keyword detection ─────────────────────────────────────────
        fused_scores: dict[str, float] = _nlp_detect_domains(message)

        # ── Step 2: optional embedding detection + score fusion ───────────────
        if self._embedding_service is not None and db is not None:
            try:
                embedding_scores = await self._embedding_service.detect_domains(message, db)
                for domain, emb_score in embedding_scores.items():
                    fused_scores[domain] = max(fused_scores.get(domain, 0.0), emb_score)
            except Exception:
                logger.warning(
                    "ReevuPlanner.build_plan_async: embedding detection failed — "
                    "falling back to keyword-only scores"
                )
                fallback_reasons.append("embedding_detection_failed")

        # ── Step 3: threshold filter (same as build_plan: score >= 0.8) ───────
        detected = {d for d, s in fused_scores.items() if s >= 0.8}
        domains = sorted(detected, key=lambda d: DOMAIN_ORDER.get(d, 99))

        # ── Step 4: validate and default ─────────────────────────────────────
        valid_domains = [domain for domain in domains if domain in DOMAIN_ORDER]
        if len(valid_domains) != len(domains):
            fallback_reasons.append("ambiguous_domain_filtered")
        domains = valid_domains

        if not domains:
            domains = ["breeding"]
            fallback_reasons.append("default_breeding_fallback")

        # ── Step 5: DAG ordering ──────────────────────────────────────────────
        try:
            domains = self._build_domain_order_dag(domains)
        except Exception:
            fallback_reasons.append("dag_builder_error")
            domains = sorted(set(domains), key=lambda d: DOMAIN_ORDER.get(d, 99))

        # ── Step 6: build plan steps (identical logic to build_plan) ──────────
        dependency_map = _dependency_hints(domains)
        is_compound = len(domains) > 1
        steps: list[PlanStep] = []
        step_ids_by_domain: dict[str, str] = {}

        for idx, domain in enumerate(domains):
            step_id = f"step-{idx + 1}"
            is_deterministic = bool(
                domain == "analytics"
                or (
                    function_call_name is not None
                    and function_call_name.startswith(DETERMINISTIC_PREFIXES)
                )
            )

            prerequisites: list[str] = []
            if self.dag_enabled:
                prerequisites = [
                    step_ids_by_domain[prerequisite_domain]
                    for prerequisite_domain in domains
                    if prerequisite_domain in dependency_map.get(domain, set())
                    and prerequisite_domain in step_ids_by_domain
                ]

            steps.append(
                PlanStep(
                    step_id=step_id,
                    domain=domain,
                    description=_step_description(domain),
                    prerequisites=prerequisites,
                    expected_outputs=_expected_outputs(domain),
                    completed=False,
                    deterministic=is_deterministic,
                )
            )
            step_ids_by_domain[domain] = step_id

        return ReevuExecutionPlan(
            plan_id=f"plan-{uuid4().hex[:8]}",
            original_query=message,
            is_compound=is_compound,
            steps=steps,
            domains_involved=domains,
            metadata={"fallback_reasons": fallback_reasons},
        )
