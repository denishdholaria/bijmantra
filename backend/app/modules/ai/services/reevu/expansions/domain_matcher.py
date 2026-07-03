"""
Domain Matcher — Stage C (Expansions)

Identifies the functional domain of a user query based on token analysis.
Supports REEVU's multi-domain routing capabilities.
"""

from __future__ import annotations

from typing import TypedDict


class DomainScore(TypedDict):
    """Score breakdown for a specific domain."""
    score: int
    matches: list[str]


class DomainDetectionResult(TypedDict):
    """Result of domain detection analysis."""
    primary_domain: str
    confidence: float
    scores: dict[str, int]
    details: dict[str, DomainScore]


class DomainMatcher:
    """Matches normalized tokens against predefined knowledge domains."""

    # Domain Definitions
    # Keys should match REEVU canonical domains where possible.
    DOMAINS: dict[str, set[str]] = {
        "GENOMICS": {
            "genomics", "marker", "snp", "dna", "genotype", "gwas", "allele",
            "pedigree", "cross", "breeding", "population", "haplotype",
            "linkage", "disequilibrium", "qtl", "sequencing", "variant",
            "call", "rate", "kinship", "matrix", "grm", "blup", "ebv",
            "gebv", "prediction", "selection", "gain", "genetic",
        },
        "TRIALS": {
            "trial", "field", "plot", "experiment", "layout", "design",
            "block", "replication", "phenotype", "observation", "trait",
            "measurement", "yield", "harvest", "planting", "sowing",
            "location", "site", "environment", "check", "control",
            "randomization", "rcbd", "augmented", "split", "plot",
        },
        "WEATHER": {
            "weather", "climate", "temperature", "rain", "precipitation",
            "humidity", "wind", "forecast", "station", "historical",
            "accumulated", "gdd", "degree", "days", "solar", "radiation",
            "evapotranspiration", "drought", "flood", "frost", "heat",
            "stress", "meteorological",
        },
        "INVENTORY": {
            "inventory", "seed", "stock", "warehouse", "storage", "lot",
            "germplasm", "accession", "quantity", "available", "reserved",
            "location", "movement", "transaction", "shipping", "receipt",
            "discard", "viability", "germination", "test", "weight",
            "count", "bag", "packet",
        },
        "ANALYTICS": {
            "analytics", "report", "dashboard", "chart", "graph", "trend",
            "summary", "prediction", "model", "statistics", "mean",
            "variance", "deviation", "correlation", "regression", "pca",
            "cluster", "analysis", "insight", "visualization", "plot",
            "histogram", "scatter", "box",
        },
        "BREEDING": {
            "breeding", "program", "pipeline", "cycle", "generation",
            "advancement", "selection", "crossing", "nursery", "pollination",
            "harvest", "parent", "progeny", "line", "variety", "hybrid",
            "cultivar", "release", "commercial", "market", "segment",
        },
    }

    # Domains that share keywords (e.g., 'breeding' appears in GENOMICS and BREEDING)
    # This overlap is handled by scoring; the domain with MORE unique matches wins.
    # Alternatively, we could weight unique keywords higher?
    # For now, simple frequency count is robust enough for V1.

    def detect_domain(self, tokens: list[str]) -> DomainDetectionResult:
        """
        Identify the most likely domain for a given list of tokens.

        Returns a result object containing the primary domain, confidence score,
        and detailed breakdown.
        """
        scores: dict[str, int] = {d: 0 for d in self.DOMAINS}
        details: dict[str, DomainScore] = {
            d: {"score": 0, "matches": []} for d in self.DOMAINS
        }

        total_matches = 0

        for token in tokens:
            for domain, keywords in self.DOMAINS.items():
                if token in keywords:
                    scores[domain] += 1
                    details[domain]["score"] += 1
                    details[domain]["matches"].append(token)
                    total_matches += 1

        # Determine winner
        # Sort by score descending
        sorted_domains = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_domain, top_score = sorted_domains[0]

        # Calculate confidence
        # Simple metric: top_score / total_matches (if total > 0)
        # Or top_score / len(tokens) ?
        # top_score / total_matches represents "share of voice" among domains.
        confidence = 0.0
        if total_matches > 0:
            confidence = top_score / total_matches

        # If no matches, return UNKNOWN
        if top_score == 0:
            return {
                "primary_domain": "UNKNOWN",
                "confidence": 0.0,
                "scores": scores,
                "details": details,
            }

        return {
            "primary_domain": top_domain,
            "confidence": round(confidence, 2),
            "scores": scores,
            "details": details,
        }
