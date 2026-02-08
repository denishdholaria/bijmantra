"""
Cross Prediction API
Predict progeny performance from parental crosses

Endpoints:
- POST /crosses/predict - Predict single cross
- POST /crosses/rank - Rank multiple crosses
- GET /crosses/selection-intensities - Get selection intensity values
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import numpy as np

from app.services.cross_prediction import cross_prediction_service, CrossPrediction
from app.api.deps import get_current_user

router = APIRouter(prefix="/crosses", tags=["Cross Prediction"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class SingleCrossRequest(BaseModel):
    """Request to predict a single cross"""
    parent1_id: str
    parent2_id: str
    parent1_gebv: float = Field(..., description="GEBV of parent 1")
    parent2_gebv: float = Field(..., description="GEBV of parent 2")
    parent1_genotypes: List[float] = Field(..., description="Genotypes of parent 1")
    parent2_genotypes: List[float] = Field(..., description="Genotypes of parent 2")
    marker_effects: Optional[List[float]] = Field(None, description="Marker effect estimates")
    selection_intensity: float = Field(2.06, description="Selection intensity (2.06 = top 5%)")
    threshold: Optional[float] = Field(None, description="Threshold for superior progeny")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "parent1_id": "GERM001",
            "parent2_id": "GERM002",
            "parent1_gebv": 2.5,
            "parent2_gebv": 3.1,
            "parent1_genotypes": [0, 1, 2, 1, 0, 2],
            "parent2_genotypes": [1, 1, 0, 2, 1, 1],
            "selection_intensity": 2.06
        }
    })


class CrossPredictionResponse(BaseModel):
    """Response for cross prediction"""
    parent1_id: str
    parent2_id: str
    predicted_mean: float
    predicted_variance: float
    predicted_sd: float
    usefulness: float
    superior_progeny_prob: float
    inbreeding_coefficient: float
    genetic_distance: float


class RankCrossesRequest(BaseModel):
    """Request to rank multiple crosses"""
    parents: List[Dict[str, Any]] = Field(..., description="List of parents with 'id' key")
    genotypes: List[List[float]] = Field(..., description="Genotype matrix (n_parents x n_markers)")
    gebvs: List[float] = Field(..., description="GEBV vector")
    marker_effects: Optional[List[float]] = Field(None, description="Marker effects")
    selection_intensity: float = Field(2.06, description="Selection intensity")
    threshold: Optional[float] = Field(None, description="Threshold for superior progeny")
    max_inbreeding: float = Field(0.25, description="Maximum allowed inbreeding")
    min_genetic_distance: float = Field(0.1, description="Minimum genetic distance")
    top_n: int = Field(20, ge=1, le=100, description="Number of top crosses")
    rank_by: str = Field("usefulness", description="Ranking criterion")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "parents": [
                {"id": "GERM001", "name": "Variety A"},
                {"id": "GERM002", "name": "Variety B"},
                {"id": "GERM003", "name": "Variety C"}
            ],
            "genotypes": [
                [0, 1, 2, 1],
                [1, 1, 0, 2],
                [2, 0, 1, 1]
            ],
            "gebvs": [2.5, 3.1, 2.8],
            "top_n": 10,
            "rank_by": "usefulness"
        }
    })


class RankedCross(BaseModel):
    """A ranked cross"""
    rank: int
    parent1_id: str
    parent2_id: str
    predicted_mean: float
    predicted_variance: float
    usefulness: float
    superior_progeny_prob: float
    inbreeding_coefficient: float
    genetic_distance: float


class RankCrossesResponse(BaseModel):
    """Response for ranked crosses"""
    crosses: List[RankedCross]
    total_evaluated: int
    selection_intensity: float
    threshold: float
    rank_by: str


class SelectionIntensity(BaseModel):
    """Selection intensity value"""
    percentage: float
    intensity: float
    description: str


# ============================================
# ENDPOINTS
# ============================================

@router.post("/predict", response_model=CrossPredictionResponse)
async def predict_single_cross(request: SingleCrossRequest):
    """Predict performance of a single cross between two parents.
    
    Predicted Mean (Mid-parent value):
        μ = (GEBV₁ + GEBV₂) / 2
    
    Predicted Variance (Mendelian sampling variance):
        σ² = Σ(aᵢ² × pᵢ × (1-pᵢ))
    
    Where:
        - aᵢ = Marker effect for locus i
        - pᵢ = Frequency of heterozygous loci
    
    Usefulness Criterion (Schnell & Utz, 1975):
        U = μ + i × σ
    
    Where i = selection intensity
    
    Args:
        request: SingleCrossRequest containing parent IDs, GEBVs, genotypes,
            optional marker effects, selection intensity, and threshold.
    
    Returns:
        CrossPredictionResponse: Contains predicted_mean, predicted_variance,
            predicted_sd, usefulness, superior_progeny_prob, 
            inbreeding_coefficient, and genetic_distance.
    
    Raises:
        HTTPException: 500 if prediction calculation fails.
    """
    try:
        prediction = cross_prediction_service.predict_single_cross(
            parent1_id=request.parent1_id,
            parent2_id=request.parent2_id,
            parent1_gebv=request.parent1_gebv,
            parent2_gebv=request.parent2_gebv,
            parent1_genotypes=np.array(request.parent1_genotypes),
            parent2_genotypes=np.array(request.parent2_genotypes),
            marker_effects=np.array(request.marker_effects) if request.marker_effects else None,
            selection_intensity=request.selection_intensity,
            threshold=request.threshold
        )
        
        return CrossPredictionResponse(
            parent1_id=prediction.parent1_id,
            parent2_id=prediction.parent2_id,
            predicted_mean=prediction.predicted_mean,
            predicted_variance=prediction.predicted_variance,
            predicted_sd=np.sqrt(prediction.predicted_variance) if prediction.predicted_variance > 0 else 0,
            usefulness=prediction.usefulness,
            superior_progeny_prob=prediction.superior_progeny_prob,
            inbreeding_coefficient=prediction.inbreeding_coefficient,
            genetic_distance=prediction.genetic_distance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rank", response_model=RankCrossesResponse)
async def rank_crosses(request: RankCrossesRequest):
    """Rank all possible crosses among a set of parents.
    
    Evaluates all n(n-1)/2 pairwise crosses and ranks them by selected criterion.
    
    Ranking Methods:
        - usefulness: U = μ + i × σ (balances mean and variance)
        - mean: μ = (GEBV₁ + GEBV₂) / 2 (predicted mean only)
        - variance: σ² = Σ(aᵢ² × pᵢ × (1-pᵢ)) (for maintaining diversity)
        - superior_prob: P(X > T) = 1 - Φ((T - μ) / σ) (probability exceeding threshold)
    
    Filters out crosses with:
        - Inbreeding coefficient > max_inbreeding
        - Genetic distance < min_genetic_distance
    
    Args:
        request: RankCrossesRequest containing:
            - parents: List of parent dicts with 'id' key
            - genotypes: Genotype matrix (n_parents × n_markers)
            - gebvs: GEBV vector for each parent
            - marker_effects: Optional marker effect estimates
            - selection_intensity: Selection intensity (default 2.06 = top 5%)
            - threshold: Optional threshold for superior progeny
            - max_inbreeding: Maximum allowed inbreeding (default 0.25)
            - min_genetic_distance: Minimum genetic distance (default 0.1)
            - top_n: Number of top crosses to return (default 20)
            - rank_by: Ranking criterion (default "usefulness")
    
    Returns:
        RankCrossesResponse: Contains ranked crosses list, total_evaluated,
            selection_intensity, threshold, and rank_by method.
    
    Raises:
        HTTPException: 400 if parent count doesn't match GEBVs or genotypes.
        HTTPException: 500 if ranking calculation fails.
    """
    try:
        if len(request.parents) != len(request.gebvs):
            raise HTTPException(
                status_code=400,
                detail="Number of parents must match number of GEBVs"
            )
        
        if len(request.parents) != len(request.genotypes):
            raise HTTPException(
                status_code=400,
                detail="Number of parents must match genotype rows"
            )
        
        ranking = cross_prediction_service.rank_crosses(
            parents=request.parents,
            genotypes=np.array(request.genotypes),
            gebvs=np.array(request.gebvs),
            marker_effects=np.array(request.marker_effects) if request.marker_effects else None,
            selection_intensity=request.selection_intensity,
            threshold=request.threshold,
            max_inbreeding=request.max_inbreeding,
            min_genetic_distance=request.min_genetic_distance,
            top_n=request.top_n,
            rank_by=request.rank_by
        )
        
        ranked_crosses = [
            RankedCross(
                rank=i + 1,
                parent1_id=c.parent1_id,
                parent2_id=c.parent2_id,
                predicted_mean=c.predicted_mean,
                predicted_variance=c.predicted_variance,
                usefulness=c.usefulness,
                superior_progeny_prob=c.superior_progeny_prob,
                inbreeding_coefficient=c.inbreeding_coefficient,
                genetic_distance=c.genetic_distance
            )
            for i, c in enumerate(ranking.crosses)
        ]
        
        # Calculate total possible crosses
        n = len(request.parents)
        total_possible = n * (n - 1) // 2
        
        return RankCrossesResponse(
            crosses=ranked_crosses,
            total_evaluated=total_possible,
            selection_intensity=ranking.selection_intensity,
            threshold=ranking.threshold,
            rank_by=ranking.method
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/selection-intensities", response_model=List[SelectionIntensity])
async def get_selection_intensities():
    """Get common selection intensity values for cross prediction.
    
    Selection intensity (i) is derived from the proportion of population selected
    and is used in the usefulness criterion:
    
        U = μ + i × σ
    
    Where:
        - U = Usefulness criterion
        - μ = Predicted mean of cross
        - i = Selection intensity
        - σ = Predicted standard deviation of cross
    
    Higher intensity = more aggressive selection = fewer individuals selected.
    
    Returns:
        List[SelectionIntensity]: List of common selection intensities with
            percentage, intensity value, and description.
    """
    return [
        SelectionIntensity(
            percentage=50.0,
            intensity=0.80,
            description="Top 50% - Low selection pressure"
        ),
        SelectionIntensity(
            percentage=25.0,
            intensity=1.27,
            description="Top 25% - Moderate selection"
        ),
        SelectionIntensity(
            percentage=10.0,
            intensity=1.76,
            description="Top 10% - High selection"
        ),
        SelectionIntensity(
            percentage=5.0,
            intensity=2.06,
            description="Top 5% - Very high selection (default)"
        ),
        SelectionIntensity(
            percentage=1.0,
            intensity=2.67,
            description="Top 1% - Extreme selection"
        ),
        SelectionIntensity(
            percentage=0.1,
            intensity=3.37,
            description="Top 0.1% - Ultra-extreme selection"
        ),
    ]


@router.get("/methods")
async def get_ranking_methods():
    """Get available ranking methods for cross prediction.
    
    Returns:
        dict: A dictionary containing a list of available ranking methods,
            each with id, name, description, formula, and optional reference.
    """
    return {
        "methods": [
            {
                "id": "usefulness",
                "name": "Usefulness Criterion",
                "description": "Mean + selection_intensity × SD. Balances mean and variance.",
                "formula": "U = μ + i × σ",
                "reference": "Schnell & Utz (1975)"
            },
            {
                "id": "mean",
                "name": "Predicted Mean",
                "description": "Rank by predicted mean only. Ignores variance.",
                "formula": "μ = (GEBV₁ + GEBV₂) / 2"
            },
            {
                "id": "variance",
                "name": "Predicted Variance",
                "description": "Rank by variance. Useful for maintaining diversity.",
                "formula": "σ² = Σ(aᵢ² × pᵢ × (1-pᵢ))"
            },
            {
                "id": "superior_prob",
                "name": "Superior Progeny Probability",
                "description": "Probability of progeny exceeding threshold.",
                "formula": "P(X > T) = 1 - Φ((T - μ) / σ)"
            }
        ]
    }
