"""
Phenotype Analysis API for Plant Breeding
Statistical analysis of phenotypic data

Endpoints:
- POST /api/v2/phenotype/stats - Descriptive statistics
- POST /api/v2/phenotype/heritability - Estimate heritability
- POST /api/v2/phenotype/correlation - Genetic correlation
- POST /api/v2/phenotype/selection-response - Expected selection gain
- POST /api/v2/phenotype/selection-index - Multi-trait selection index
- POST /api/v2/phenotype/anova - ANOVA for RCBD
"""

from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict

from app.services.phenotype_analysis import get_phenotype_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/phenotype", tags=["Phenotype Analysis"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class StatsRequest(BaseModel):
    """Request for descriptive statistics"""
    values: List[float] = Field(..., min_length=1, description="Phenotypic values")
    trait_name: str = Field("trait", description="Name of the trait")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "values": [4.5, 5.2, 4.8, 5.1, 4.9, 5.3, 4.7, 5.0],
            "trait_name": "yield"
        }
    })


class HeritabilityRequest(BaseModel):
    """Request for heritability estimation"""
    genotype_data: Dict[str, List[float]] = Field(
        ...,
        description="Dict of genotype_id -> list of replicate values"
    )
    trait_name: str = Field("trait", description="Name of the trait")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotype_data": {
                "G1": [4.5, 4.8, 4.6],
                "G2": [5.2, 5.0, 5.3],
                "G3": [4.1, 4.3, 4.0],
                "G4": [5.5, 5.4, 5.6]
            },
            "trait_name": "yield"
        }
    })


class CorrelationRequest(BaseModel):
    """Request for genetic correlation"""
    trait1_means: Dict[str, float] = Field(..., description="Genotype means for trait 1")
    trait2_means: Dict[str, float] = Field(..., description="Genotype means for trait 2")
    trait1_name: str = Field("trait1", description="Name of trait 1")
    trait2_name: str = Field("trait2", description="Name of trait 2")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "trait1_means": {"G1": 4.5, "G2": 5.2, "G3": 4.1, "G4": 5.5},
            "trait2_means": {"G1": 12.3, "G2": 14.1, "G3": 11.8, "G4": 15.2},
            "trait1_name": "yield",
            "trait2_name": "plant_height"
        }
    })


class SelectionResponseRequest(BaseModel):
    """Request for selection response calculation"""
    heritability: float = Field(..., ge=0, le=1, description="Heritability (0-1)")
    phenotypic_std: float = Field(..., gt=0, description="Phenotypic standard deviation")
    selection_proportion: float = Field(..., gt=0, lt=1, description="Proportion selected (e.g., 0.1 for top 10%)")
    trait_mean: float = Field(..., description="Current trait mean")
    trait_name: str = Field("trait", description="Name of the trait")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "heritability": 0.6,
            "phenotypic_std": 0.8,
            "selection_proportion": 0.1,
            "trait_mean": 5.0,
            "trait_name": "yield"
        }
    })


class SelectionIndexRequest(BaseModel):
    """Request for selection index calculation"""
    traits: List[str] = Field(..., description="List of trait names")
    phenotypic_values: Dict[str, List[float]] = Field(
        ...,
        description="Dict of genotype_id -> list of trait values (in same order as traits)"
    )
    economic_weights: List[float] = Field(..., description="Economic weight for each trait")
    heritabilities: List[float] = Field(..., description="Heritability for each trait")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "traits": ["yield", "protein", "disease_resistance"],
            "phenotypic_values": {
                "G1": [4.5, 12.0, 7.0],
                "G2": [5.2, 11.5, 8.0],
                "G3": [4.1, 13.0, 6.0],
                "G4": [5.5, 10.5, 9.0]
            },
            "economic_weights": [1.0, 0.5, 0.3],
            "heritabilities": [0.6, 0.7, 0.4]
        }
    })


class AnovaDataPoint(BaseModel):
    """Single data point for ANOVA"""
    genotype: str
    block: str
    value: float


class AnovaRequest(BaseModel):
    """Request for ANOVA"""
    data: List[AnovaDataPoint] = Field(..., description="List of observations")
    trait_name: str = Field("trait", description="Name of the trait")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "data": [
                {"genotype": "G1", "block": "B1", "value": 4.5},
                {"genotype": "G1", "block": "B2", "value": 4.8},
                {"genotype": "G2", "block": "B1", "value": 5.2},
                {"genotype": "G2", "block": "B2", "value": 5.0},
                {"genotype": "G3", "block": "B1", "value": 4.1},
                {"genotype": "G3", "block": "B2", "value": 4.3}
            ],
            "trait_name": "yield"
        }
    })


# ============================================
# ENDPOINTS
# ============================================

@router.post("/stats")
async def descriptive_statistics(request: StatsRequest):
    """Calculate descriptive statistics for phenotypic data.
    
    Computes standard statistical measures for a set of phenotypic observations:
    - Mean, standard deviation
    - Min, max, range
    - Coefficient of variation (CV%)
    
    Args:
        request: StatsRequest containing phenotypic values and trait name.
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether calculation succeeded
            - mean (float): Arithmetic mean
            - std (float): Standard deviation
            - min (float): Minimum value
            - max (float): Maximum value
            - cv (float): Coefficient of variation (%)
            - n (int): Sample size
    
    Raises:
        HTTPException: 500 if statistics calculation fails.
    """
    service = get_phenotype_service()

    try:
        stats = service.descriptive_stats(request.values, request.trait_name)
        return {
            "success": True,
            **stats.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Statistics calculation failed: {str(e)}")


@router.post("/heritability")
async def estimate_heritability(request: HeritabilityRequest):
    """Estimate broad-sense heritability from replicated data.
    
    H² = Vg / Vp = Vg / (Vg + Ve)
    
    Where:
        - Vg = Genetic variance (between genotypes)
        - Ve = Environmental variance (within genotypes)
        - Vp = Phenotypic variance (total)
    
    Requires multiple replicates per genotype.
    
    Interpretation:
        - H² > 0.6: High heritability (strong genetic control)
        - H² 0.3-0.6: Moderate heritability
        - H² < 0.3: Low heritability (strong environmental influence)
    
    Args:
        request: HeritabilityRequest containing genotype_data (dict of 
            genotype_id -> list of replicate values) and trait_name.
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether calculation succeeded
            - h2_broad (float): Broad-sense heritability estimate
            - vg (float): Genetic variance
            - ve (float): Environmental variance
            - interpretation (str): Human-readable interpretation
            - n_genotypes (int): Number of genotypes
            - n_replicates (int): Number of replicates per genotype
    
    Raises:
        HTTPException: 400 if genotypes have unequal replicates or < 2 replicates.
        HTTPException: 500 if heritability estimation fails.
    """
    service = get_phenotype_service()

    try:
        # Validate input
        n_reps = [len(v) for v in request.genotype_data.values()]
        if len(set(n_reps)) > 1:
            raise HTTPException(400, "All genotypes must have the same number of replicates")

        if n_reps[0] < 2:
            raise HTTPException(400, "Need at least 2 replicates per genotype")

        result = service.estimate_heritability(request.genotype_data, request.trait_name)

        # Add interpretation
        h2 = result.h2_broad
        if h2 > 0.6:
            interpretation = "High heritability - trait strongly controlled by genetics"
        elif h2 > 0.3:
            interpretation = "Moderate heritability - both genetics and environment important"
        else:
            interpretation = "Low heritability - trait strongly influenced by environment"

        return {
            "success": True,
            **result.to_dict(),
            "interpretation": interpretation,
            "n_genotypes": len(request.genotype_data),
            "n_replicates": n_reps[0],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Heritability estimation failed: {str(e)}")


@router.post("/correlation")
async def genetic_correlation(request: CorrelationRequest):
    """Calculate genetic correlation between two traits.
    
    rg = Cov(G1, G2) / sqrt(Vg1 × Vg2)
    
    Where:
        - Cov(G1, G2) = Genetic covariance between traits
        - Vg1, Vg2 = Genetic variances of each trait
    
    Interpretation:
        - rg > 0: Positive correlation (selecting for one increases the other)
        - rg < 0: Negative correlation (selecting for one decreases the other)
        - |rg| > 0.7: Strong correlation
        - |rg| 0.4-0.7: Moderate correlation
        - |rg| < 0.4: Weak correlation
    
    Args:
        request: CorrelationRequest containing trait1_means, trait2_means 
            (dicts of genotype_id -> mean value), and trait names.
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether calculation succeeded
            - trait_1 (str): Name of first trait
            - trait_2 (str): Name of second trait
            - correlation (float): Genetic correlation coefficient (-1 to 1)
            - p_value (float): Statistical significance
    
    Raises:
        HTTPException: 400 if correlation calculation returns an error.
        HTTPException: 500 if correlation calculation fails unexpectedly.
    """
    service = get_phenotype_service()

    try:
        result = service.genetic_correlation(request.trait1_means, request.trait2_means)

        if "error" in result:
            raise HTTPException(400, result["error"])

        return {
            "success": True,
            "trait_1": request.trait1_name,
            "trait_2": request.trait2_name,
            **result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Correlation calculation failed: {str(e)}")


@router.post("/selection-response")
async def selection_response(request: SelectionResponseRequest):
    """Calculate expected response to selection (Breeder's Equation).
    
    R = i × h² × σp
    
    Where:
        - R = Response to selection (genetic gain per generation)
        - i = Selection intensity (from selection proportion)
        - h² = Heritability (narrow-sense or broad-sense)
        - σp = Phenotypic standard deviation
    
    Common selection intensities:
        - Top 50%: i ≈ 0.80
        - Top 25%: i ≈ 1.27
        - Top 10%: i ≈ 1.76
        - Top 5%:  i ≈ 2.06
        - Top 1%:  i ≈ 2.67
    
    Example: Selecting top 10% (i ≈ 1.76) with h² = 0.6 and σp = 0.8
    gives R = 1.76 × 0.6 × 0.8 = 0.84 units gain per generation
    
    Args:
        request: SelectionResponseRequest containing heritability (0-1),
            phenotypic_std, selection_proportion (0-1), trait_mean, and trait_name.
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether calculation succeeded
            - response (float): Expected genetic gain per generation
            - percent_gain (float): Response as percentage of current mean
            - selection_proportion (float): Proportion of population selected
            - generations_to_10_percent_gain (float): Generations needed for 10% improvement
    
    Raises:
        HTTPException: 500 if selection response calculation fails.
    """
    service = get_phenotype_service()

    try:
        result = service.selection_response(
            heritability=request.heritability,
            phenotypic_std=request.phenotypic_std,
            selection_proportion=request.selection_proportion,
            trait_mean=request.trait_mean,
            trait_name=request.trait_name,
        )

        return {
            "success": True,
            **result.to_dict(),
            "selection_proportion": request.selection_proportion,
            "generations_to_10_percent_gain": round(10 / result.percent_gain, 1) if result.percent_gain > 0 else None,
        }
    except Exception as e:
        raise HTTPException(500, f"Selection response calculation failed: {str(e)}")


@router.post("/selection-index")
async def selection_index(request: SelectionIndexRequest):
    """Calculate Smith-Hazel selection index for multiple traits.
    
    I = Σ(bi × Pi)
    
    Where:
        - I = Selection index value
        - bi = Index weight for trait i (derived from economic weights and heritabilities)
        - Pi = Phenotypic value for trait i
    
    The Smith-Hazel index maximizes genetic gain across multiple traits
    by weighting each trait according to its economic importance and
    heritability.
    
    Higher index = better overall genotype considering all traits and their
    economic importance.
    
    Reference: Smith (1936), Hazel (1943)
    
    Args:
        request: SelectionIndexRequest containing:
            - traits: List of trait names
            - phenotypic_values: Dict of genotype_id -> list of trait values
            - economic_weights: Economic weight for each trait
            - heritabilities: Heritability for each trait
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether calculation succeeded
            - index_values (dict): Genotype_id -> index value
            - rankings (list): Genotypes ranked by index value
            - weights (list): Calculated index weights for each trait
    
    Raises:
        HTTPException: 400 if trait count doesn't match values or weights.
        HTTPException: 500 if selection index calculation fails.
    """
    service = get_phenotype_service()

    try:
        # Validate
        n_traits = len(request.traits)
        for geno, values in request.phenotypic_values.items():
            if len(values) != n_traits:
                raise HTTPException(400, f"Genotype {geno} has {len(values)} values, expected {n_traits}")

        result = service.selection_index(
            traits=request.traits,
            phenotypic_values=request.phenotypic_values,
            economic_weights=request.economic_weights,
            heritabilities=request.heritabilities,
        )

        if "error" in result:
            raise HTTPException(400, result["error"])

        return {
            "success": True,
            **result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Selection index calculation failed: {str(e)}")


@router.post("/anova")
async def anova_rcbd(request: AnovaRequest):
    """Perform ANOVA for Randomized Complete Block Design (RCBD).
    
    SS_total = SS_genotype + SS_block + SS_error
    
    Partitions total variance into:
        - Genotype effect (SS_genotype): Variation due to genetic differences
        - Block effect (SS_block): Variation due to environmental blocks
        - Error (SS_error): Residual/unexplained variation
    
    F-statistic for genotype effect:
        F = MS_genotype / MS_error
    
    Where MS = SS / df (Mean Square = Sum of Squares / degrees of freedom)
    
    Args:
        request: AnovaRequest containing:
            - data: List of AnovaDataPoint (genotype, block, value)
            - trait_name: Name of the trait being analyzed
    
    Returns:
        dict: A dictionary containing:
            - success (bool): Whether calculation succeeded
            - anova_table (dict): SS, df, MS, F, p-value for each source
            - genotype_means (dict): Mean value for each genotype
            - block_means (dict): Mean value for each block
            - grand_mean (float): Overall mean
            - cv (float): Coefficient of variation (%)
    
    Raises:
        HTTPException: 500 if ANOVA calculation fails.
    """
    service = get_phenotype_service()

    try:
        data = [d.model_dump() for d in request.data]
        result = service.anova_rcbd(data, request.trait_name)

        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"ANOVA calculation failed: {str(e)}")


@router.get("/methods")
async def list_methods():
    """List available phenotype analysis methods.
    
    Returns:
        dict: A dictionary containing a list of available analysis methods,
            each with id, name, and description.
    """
    return {
        "methods": [
            {
                "id": "stats",
                "name": "Descriptive Statistics",
                "description": "Mean, std, CV, range for phenotypic data",
            },
            {
                "id": "heritability",
                "name": "Heritability Estimation",
                "description": "Broad-sense heritability from replicated data",
            },
            {
                "id": "correlation",
                "name": "Genetic Correlation",
                "description": "Correlation between traits at genetic level",
            },
            {
                "id": "selection_response",
                "name": "Selection Response",
                "description": "Expected genetic gain from selection",
            },
            {
                "id": "selection_index",
                "name": "Selection Index",
                "description": "Multi-trait selection using economic weights",
            },
            {
                "id": "anova",
                "name": "ANOVA (RCBD)",
                "description": "Analysis of variance for randomized complete block design",
            },
        ]
    }
