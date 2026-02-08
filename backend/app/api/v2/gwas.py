"""
GWAS (Genome-Wide Association Study) API
Marker-trait association analysis endpoints

Endpoints:
- POST /api/v2/gwas/glm - GLM single-marker regression
- POST /api/v2/gwas/mlm - Mixed Linear Model with kinship
- POST /api/v2/gwas/kinship - Calculate kinship matrix
- POST /api/v2/gwas/pca - Population structure PCA
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ConfigDict
import numpy as np

from app.services.gwas import get_gwas_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/gwas", tags=["GWAS"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class MarkerInfo(BaseModel):
    """Information about a genetic marker"""
    name: str
    chromosome: str
    position: int


class GWASRequest(BaseModel):
    """Request for GWAS analysis"""
    genotypes: List[List[float]] = Field(..., description="Genotype matrix (samples × markers), coded 0/1/2")
    phenotypes: List[float] = Field(..., description="Trait values for each sample")
    markers: List[MarkerInfo] = Field(..., description="Marker information")
    covariates: Optional[List[List[float]]] = Field(None, description="Optional covariate matrix")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": [[0, 1, 2], [1, 1, 0], [2, 0, 1]],
            "phenotypes": [5.2, 4.8, 5.5],
            "markers": [
                {"name": "SNP1", "chromosome": "1", "position": 1000},
                {"name": "SNP2", "chromosome": "1", "position": 2000},
                {"name": "SNP3", "chromosome": "2", "position": 1500},
            ],
        }
    })


class MLMRequest(GWASRequest):
    """Request for MLM GWAS with kinship"""
    kinship: Optional[List[List[float]]] = Field(None, description="Kinship matrix (optional, will be calculated)")


class KinshipRequest(BaseModel):
    """Request for kinship calculation"""
    genotypes: List[List[float]]
    method: str = Field("vanraden", description="Method: vanraden or ibs")


class PCARequest(BaseModel):
    """Request for PCA"""
    genotypes: List[List[float]]
    n_components: int = Field(10, ge=1, le=50)


# ============================================
# ENDPOINTS
# ============================================

@router.post("/glm")
async def glm_gwas(request: GWASRequest):
    """
    GLM (General Linear Model) GWAS
    
    Single-marker regression without population structure correction.
    Fast but may have inflated p-values if population structure exists.
    
    Use for:
    - Quick preliminary analysis
    - Populations with minimal structure
    - When kinship is not available
    """
    service = get_gwas_service()
    
    try:
        genotypes = np.array(request.genotypes)
        phenotypes = np.array(request.phenotypes)
        
        if genotypes.shape[0] != len(phenotypes):
            raise HTTPException(400, "Number of samples must match between genotypes and phenotypes")
        if genotypes.shape[1] != len(request.markers):
            raise HTTPException(400, "Number of markers must match marker info")
        
        covariates = np.array(request.covariates) if request.covariates else None
        
        result = service.glm_gwas(
            genotypes=genotypes,
            phenotypes=phenotypes,
            marker_names=[m.name for m in request.markers],
            chromosomes=[m.chromosome for m in request.markers],
            positions=[m.position for m in request.markers],
            covariates=covariates,
        )
        
        return result.to_dict()
        
    except Exception as e:
        raise HTTPException(500, f"GLM GWAS failed: {str(e)}")


@router.post("/mlm")
async def mlm_gwas(request: MLMRequest):
    """
    MLM (Mixed Linear Model) GWAS
    
    Accounts for population structure using kinship matrix.
    More accurate p-values for structured populations.
    
    Model: y = Xβ + Zα + u + ε
    where u ~ N(0, Kσ²_g)
    
    Use for:
    - Populations with structure (breeding populations, diverse panels)
    - When accurate p-values are critical
    - Publication-quality results
    """
    service = get_gwas_service()
    
    try:
        genotypes = np.array(request.genotypes)
        phenotypes = np.array(request.phenotypes)
        
        if genotypes.shape[0] != len(phenotypes):
            raise HTTPException(400, "Number of samples must match")
        
        # Calculate kinship if not provided
        if request.kinship:
            kinship = np.array(request.kinship)
        else:
            kinship = service.calculate_kinship(genotypes)
        
        covariates = np.array(request.covariates) if request.covariates else None
        
        result = service.mlm_gwas(
            genotypes=genotypes,
            phenotypes=phenotypes,
            kinship=kinship,
            marker_names=[m.name for m in request.markers],
            chromosomes=[m.chromosome for m in request.markers],
            positions=[m.position for m in request.markers],
            covariates=covariates,
        )
        
        return result.to_dict()
        
    except Exception as e:
        raise HTTPException(500, f"MLM GWAS failed: {str(e)}")


@router.post("/kinship")
async def calculate_kinship(request: KinshipRequest):
    """
    Calculate Genomic Relationship Matrix (Kinship)
    
    Methods:
    - vanraden: VanRaden (2008) method, recommended for GWAS
    - ibs: Identity by State, simpler but less accurate
    
    Returns kinship matrix for use in MLM GWAS.
    """
    service = get_gwas_service()
    
    try:
        genotypes = np.array(request.genotypes)
        kinship = service.calculate_kinship(genotypes, method=request.method)
        
        return {
            "method": request.method,
            "n_samples": kinship.shape[0],
            "kinship": kinship.tolist(),
            "mean_relatedness": float(np.mean(kinship[np.triu_indices_from(kinship, k=1)])),
            "diagonal_mean": float(np.mean(np.diag(kinship))),
        }
        
    except Exception as e:
        raise HTTPException(500, f"Kinship calculation failed: {str(e)}")


@router.post("/pca")
async def population_pca(request: PCARequest):
    """
    Principal Component Analysis for Population Structure
    
    Calculates PCs from genotype data for:
    - Visualizing population structure
    - Use as covariates in GWAS
    - Quality control (outlier detection)
    """
    service = get_gwas_service()
    
    try:
        genotypes = np.array(request.genotypes)
        scores, var_explained = service.calculate_pca(genotypes, request.n_components)
        
        return {
            "n_samples": scores.shape[0],
            "n_components": scores.shape[1],
            "scores": scores.tolist(),
            "variance_explained": var_explained.tolist(),
            "cumulative_variance": np.cumsum(var_explained).tolist(),
        }
        
    except Exception as e:
        raise HTTPException(500, f"PCA failed: {str(e)}")


@router.get("/methods")
async def list_methods():
    """List available GWAS methods"""
    return {
        "methods": [
            {
                "id": "glm",
                "name": "GLM",
                "full_name": "General Linear Model",
                "description": "Single-marker regression, fast but no structure correction",
                "use_case": "Quick analysis, minimal population structure",
            },
            {
                "id": "mlm",
                "name": "MLM",
                "full_name": "Mixed Linear Model",
                "description": "Kinship-corrected analysis using EMMA approach",
                "use_case": "Structured populations, accurate p-values",
            },
        ],
        "significance": {
            "bonferroni": "0.05 / n_markers",
            "suggestive": "1 / n_markers",
            "description": "Bonferroni correction for multiple testing",
        },
    }



# ============================================
# LD ANALYSIS ENDPOINTS
# ============================================

class LDRequest(BaseModel):
    """Request for LD analysis"""
    genotypes: List[List[float]] = Field(..., description="Genotype matrix (samples × markers)")
    markers: List[MarkerInfo] = Field(..., description="Marker information")
    max_distance: int = Field(50000, description="Maximum distance in bp")
    r2_threshold: float = Field(0.0, ge=0, le=1, description="Minimum r² to include")


class LDPruningRequest(BaseModel):
    """Request for LD pruning"""
    genotypes: List[List[float]]
    markers: List[MarkerInfo]
    r2_threshold: float = Field(0.5, ge=0, le=1)
    window_size: int = Field(50000, description="Window size in bp")


@router.post("/ld")
async def calculate_ld(request: LDRequest):
    """
    Calculate Linkage Disequilibrium (LD)
    
    Computes pairwise LD statistics (r², D') between markers.
    Returns LD decay curve and chromosome-wise statistics.
    
    Use for:
    - Understanding LD structure in population
    - Determining marker density requirements
    - Identifying haplotype blocks
    """
    service = get_gwas_service()
    
    try:
        genotypes = np.array(request.genotypes)
        
        if genotypes.shape[1] != len(request.markers):
            raise HTTPException(400, "Number of markers must match marker info")
        
        result = service.calculate_ld(
            genotypes=genotypes,
            marker_names=[m.name for m in request.markers],
            chromosomes=[m.chromosome for m in request.markers],
            positions=[m.position for m in request.markers],
            max_distance=request.max_distance,
            r2_threshold=request.r2_threshold,
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"LD calculation failed: {str(e)}")


@router.post("/ld/pruning")
async def ld_pruning(request: LDPruningRequest):
    """
    LD-based marker pruning
    
    Removes markers in high LD to create independent marker set.
    Useful for:
    - GWAS (reduce multiple testing)
    - Population structure analysis
    - Diversity analysis
    """
    service = get_gwas_service()
    
    try:
        genotypes = np.array(request.genotypes)
        
        result = service.ld_pruning(
            genotypes=genotypes,
            marker_names=[m.name for m in request.markers],
            chromosomes=[m.chromosome for m in request.markers],
            positions=[m.position for m in request.markers],
            r2_threshold=request.r2_threshold,
            window_size=request.window_size,
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(500, f"LD pruning failed: {str(e)}")
