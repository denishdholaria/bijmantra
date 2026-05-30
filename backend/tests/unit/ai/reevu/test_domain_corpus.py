"""
Unit tests for REEVU domain corpus.

Validates:
- Each domain has at least 50 examples
- Each domain has at least 10 implicit examples (examples that do not contain
  the domain name or obvious domain keywords as a simple heuristic)
"""

from __future__ import annotations

import pytest

from app.modules.ai.services.reevu.domain_corpus import DOMAIN_CORPUS

# All 13 registered domains that must be present in the corpus.
REQUIRED_DOMAINS = [
    "trials",
    "breeding",
    "phenotyping",
    "genomics",
    "weather",
    "field",
    "soil",
    "pest_disease",
    "seed_ops",
    "sensors",
    "spatial",
    "protocols",
    "analytics",
]

# Minimum thresholds
MIN_TOTAL_EXAMPLES = 50
MIN_IMPLICIT_EXAMPLES = 10

# Obvious domain keywords per domain — an example containing any of these
# is considered "explicit" rather than "implicit".
# This is a simple heuristic: if the domain name or a core keyword appears
# verbatim in the example text, it is explicit.
DOMAIN_EXPLICIT_KEYWORDS: dict[str, list[str]] = {
    "trials": ["trial", "experiment", "nursery", "replication", "block", "treatment", "plot"],
    "breeding": ["breed", "germplasm", "pedigree", "cultivar", "variety", "varieties", "cross", "hybrid", "accession"],
    "phenotyping": ["phenotype", "phenotyping", "observation", "trait", "scoring", "measurement", "plant height", "grain yield", "days to flowering"],
    "genomics": ["genomic", "genome", "snp", "marker", "qtl", "gwas", "haplotype", "allele", "genotype", "genotyping", "sequencing", "dna", "molecular", "linkage"],
    "weather": ["weather", "climate", "rainfall", "temperature", "humidity", "frost", "precipitation", "gdd", "growing degree", "solar radiation", "wind", "forecast"],
    "field": ["field", "planting", "harvest", "crop calendar", "sowing", "rotation", "field layout", "field management", "field history"],
    "soil": ["soil", "nutrient", "ph", "organic matter", "nitrogen", "phosphorus", "potassium", "fertility", "npk", "soil type", "soil health"],
    "pest_disease": ["disease", "pest", "pathogen", "insect", "fungal", "bacterial", "rust", "blight", "wilt", "aphid", "borer", "mildew", "nematode", "scouting", "resistance"],
    "seed_ops": ["seed lot", "seedlot", "seed stock", "seed request", "seed quantity", "seed bank", "seed supply", "germplasm stock", "seed inventory", "seed"],
    "sensors": ["sensor", "iot", "telemetry", "data logger", "monitoring station", "weather station sensor", "device reading"],
    "spatial": ["spatial", "map", "gis", "radius", "proximity", "coordinates", "distance", "region", "nearby", "km", "miles"],
    "protocols": ["protocol", "speed breeding", "photoperiod", "growth chamber", "generation", "accelerated breeding"],
    "analytics": ["statistic", "analysis", "trend", "predict", "forecast", "model", "regression", "correlation", "compare", "rank", "performance", "calculate", "compute", "analyze", "analyse"],
}


def _is_implicit(example: str, domain: str) -> bool:
    """Return True if the example does not contain the domain name or obvious keywords."""
    text = example.lower()
    # Check domain name itself
    domain_name = domain.replace("_", " ")
    if domain_name in text or domain.replace("_", "") in text:
        return False
    # Check obvious keywords
    for keyword in DOMAIN_EXPLICIT_KEYWORDS.get(domain, []):
        if keyword.lower() in text:
            return False
    return True


class TestDomainCorpusStructure:
    """Tests for corpus structure and completeness."""

    def test_all_required_domains_present(self) -> None:
        """All 13 registered domains must be present in the corpus."""
        missing = [d for d in REQUIRED_DOMAINS if d not in DOMAIN_CORPUS]
        assert not missing, f"Missing domains: {missing}"

    def test_corpus_is_dict_of_string_lists(self) -> None:
        """DOMAIN_CORPUS must be a dict mapping str to list[str]."""
        assert isinstance(DOMAIN_CORPUS, dict)
        for domain, examples in DOMAIN_CORPUS.items():
            assert isinstance(domain, str), f"Domain key must be str, got {type(domain)}"
            assert isinstance(examples, list), f"Examples for '{domain}' must be a list"
            for i, ex in enumerate(examples):
                assert isinstance(ex, str), (
                    f"Example {i} in domain '{domain}' must be str, got {type(ex)}"
                )

    def test_no_empty_examples(self) -> None:
        """No example string should be empty or whitespace-only."""
        for domain, examples in DOMAIN_CORPUS.items():
            for i, ex in enumerate(examples):
                assert ex.strip(), f"Empty example at index {i} in domain '{domain}'"


class TestDomainExampleCounts:
    """Tests that each domain meets the minimum example count requirements."""

    @pytest.mark.parametrize("domain", REQUIRED_DOMAINS)
    def test_domain_has_minimum_total_examples(self, domain: str) -> None:
        """Each domain must have at least 50 examples."""
        examples = DOMAIN_CORPUS.get(domain, [])
        count = len(examples)
        assert count >= MIN_TOTAL_EXAMPLES, (
            f"Domain '{domain}' has {count} examples, need at least {MIN_TOTAL_EXAMPLES}"
        )

    @pytest.mark.parametrize("domain", REQUIRED_DOMAINS)
    def test_domain_has_minimum_implicit_examples(self, domain: str) -> None:
        """Each domain must have at least 10 implicit examples.

        An implicit example is one that does not contain the domain name
        or obvious domain keywords (simple heuristic).
        """
        examples = DOMAIN_CORPUS.get(domain, [])
        implicit = [ex for ex in examples if _is_implicit(ex, domain)]
        count = len(implicit)
        assert count >= MIN_IMPLICIT_EXAMPLES, (
            f"Domain '{domain}' has {count} implicit examples, need at least {MIN_IMPLICIT_EXAMPLES}. "
            f"Implicit examples found: {implicit}"
        )

    def test_all_domains_total_example_count(self) -> None:
        """Summary assertion: all required domains meet the 50-example threshold."""
        failures = []
        for domain in REQUIRED_DOMAINS:
            examples = DOMAIN_CORPUS.get(domain, [])
            if len(examples) < MIN_TOTAL_EXAMPLES:
                failures.append(f"{domain}: {len(examples)} examples")
        assert not failures, f"Domains below {MIN_TOTAL_EXAMPLES} examples: {failures}"

    def test_all_domains_implicit_example_count(self) -> None:
        """Summary assertion: all required domains meet the 10-implicit-example threshold."""
        failures = []
        for domain in REQUIRED_DOMAINS:
            examples = DOMAIN_CORPUS.get(domain, [])
            implicit = [ex for ex in examples if _is_implicit(ex, domain)]
            if len(implicit) < MIN_IMPLICIT_EXAMPLES:
                failures.append(f"{domain}: {len(implicit)} implicit examples")
        assert not failures, f"Domains below {MIN_IMPLICIT_EXAMPLES} implicit examples: {failures}"


class TestDomainExampleQuality:
    """Tests for example quality and diversity."""

    @pytest.mark.parametrize("domain", REQUIRED_DOMAINS)
    def test_no_duplicate_examples_per_domain(self, domain: str) -> None:
        """Each domain should not have duplicate examples."""
        examples = DOMAIN_CORPUS.get(domain, [])
        normalized = [ex.strip().lower() for ex in examples]
        duplicates = [ex for ex in normalized if normalized.count(ex) > 1]
        unique_duplicates = list(set(duplicates))
        assert not unique_duplicates, (
            f"Domain '{domain}' has duplicate examples: {unique_duplicates[:5]}"
        )

    def test_corpus_covers_all_required_domains_exactly(self) -> None:
        """Corpus must contain entries for all 13 required domains."""
        corpus_domains = set(DOMAIN_CORPUS.keys())
        required = set(REQUIRED_DOMAINS)
        missing = required - corpus_domains
        assert not missing, f"Required domains missing from corpus: {missing}"
