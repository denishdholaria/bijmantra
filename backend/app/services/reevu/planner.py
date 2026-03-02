"""
REEVU Multi-Domain Planner — Stage C

Decomposes compound user queries into explicit multi-step execution plans
with domain tags, dependency ordering, and deterministic routing markers.
"""

from __future__ import annotations

import re
from os import getenv
from uuid import uuid4

from app.schemas.reevu_plan import PlanStep, ReevuExecutionPlan

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
}

# Domain dependency ordering (lower index = earlier in plan).
DOMAIN_ORDER: dict[str, int] = {
    "weather": 0,
    "trials": 1,
    "genomics": 2,
    "breeding": 3,
    "analytics": 4,
}

# Function name prefixes that indicate deterministic computation.
DETERMINISTIC_PREFIXES: tuple[str, ...] = (
    "calculate_", "analyze_", "predict_", "compute_", "estimate_",
)


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
            if kw in message_lower:
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
        "recommend": ["analytics"],
        "recommendation": ["analytics"],
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
        "genomics": "Retrieve genomic and molecular marker information",
        "breeding": "Fetch breeding program, germplasm, and trait data",
        "analytics": "Run analytical computations and statistical comparisons",
    }
    return descriptions.get(domain, f"Execute {domain} data retrieval")



def _expected_outputs(domain: str) -> list[str]:
    """Default expected output types per domain."""
    outputs = {
        "weather": ["weather_records", "gdd_values"],
        "trials": ["trial_records", "plot_data"],
        "genomics": ["marker_data", "genomic_profiles"],
        "breeding": ["germplasm_list", "trait_summaries"],
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
        return sorted(set(domains), key=lambda d: DOMAIN_ORDER.get(d, 99))

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

        is_compound = len(domains) > 1
        steps: list[PlanStep] = []
        prev_step_id: str | None = None

        for idx, domain in enumerate(domains):
            step_id = f"step-{idx + 1}"
            is_deterministic = bool(
                domain == "analytics"
                or (function_call_name is not None and function_call_name.startswith(DETERMINISTIC_PREFIXES))
            )

            prerequisites: list[str] = []
            if self.dag_enabled and prev_step_id is not None:
                prerequisites = [prev_step_id]

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
            prev_step_id = step_id

        return ReevuExecutionPlan(
            plan_id=f"plan-{uuid4().hex[:8]}",
            original_query=message,
            is_compound=is_compound,
            steps=steps,
            domains_involved=domains,
            metadata={"fallback_reasons": fallback_reasons},
        )
