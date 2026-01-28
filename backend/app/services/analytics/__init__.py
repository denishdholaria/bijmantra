"""
Analytical Plane Service
Implements the Target Data Lake Architecture (Phase 2) using DuckDB, Polars, and PyArrow.
"""
from .engine import analytics_engine

__all__ = ["analytics_engine"]
