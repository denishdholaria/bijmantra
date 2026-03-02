"""
Analytical Plane Service
Implements the Target Data Lake Architecture (Phase 2) using DuckDB, Polars, and PyArrow.
"""

from .engine import analytics_engine
from .etl_phenotype_extractor import phenotype_extractor
from .ssp_scenario_parser import SSPDataPoint, SSPParserResult, SSPScenario, parse_ssp_csv


__all__ = [
    "analytics_engine",
    "phenotype_extractor",
    "parse_ssp_csv",
    "SSPDataPoint",
    "SSPScenario",
    "SSPParserResult",
]
