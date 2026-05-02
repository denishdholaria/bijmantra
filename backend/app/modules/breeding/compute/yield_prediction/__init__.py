"""
Yield Prediction Compute Module.

This module contains compute-intensive yield prediction services
that should be executed via job queue for isolation from API workers.
"""

from app.modules.breeding.compute.yield_prediction.attribution import FactorAttribution
from app.modules.breeding.compute.yield_prediction.ensemble import EnsemblePredictor
from app.modules.breeding.compute.yield_prediction.ml import MLPredictor
from app.modules.breeding.compute.yield_prediction.process import ProcessBasedPredictor
from app.modules.breeding.compute.yield_prediction.statistical import StatisticalPredictor
from app.modules.breeding.compute.yield_prediction.yield_matrix_math import YieldMatrixMath

__all__ = [
    "FactorAttribution",
    "EnsemblePredictor",
    "MLPredictor",
    "ProcessBasedPredictor",
    "StatisticalPredictor",
    "YieldMatrixMath",
]
