"""
G×E Interaction Analysis API
Genotype-by-Environment interaction analysis endpoints

Endpoints:
- POST /api/v2/gxe/ammi - AMMI analysis
- POST /api/v2/gxe/gge - GGE biplot analysis
- POST /api/v2/gxe/finlay-wilkinson - Finlay-Wilkinson regression
- POST /api/v2/gxe/mega-environments - Identify mega-environments
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, ConfigDict
import numpy as np

from app.core.database import get_db
from app.services.gxe_analysis import (
    get_gxe_service,
    GxEMethod,
    GGEScaling,
)

from app.api.deps import get_current_active_user

router = APIRouter(
    prefix="/gxe", 
    tags=["G×E Analysis"],
    dependencies=[Depends(get_current_active_user)]
)


# ============================================
# SCHEMAS
# ============================================

class GxEDataInput(BaseModel):
    """Input data for G×E analysis"""
    yield_matrix: List[List[float]] = Field(..., description="Yield data (genotypes × environments)")
    genotype_names: List[str] = Field(..., description="Names of genotypes")
    environment_names: List[str] = Field(..., description="Names of environments")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "yield_matrix": [
                [4.5, 5.2, 3.8, 4.9],
                [5.1, 4.8, 4.2, 5.5],
                [3.9, 4.5, 3.5, 4.2],
            ],
            "genotype_names": ["G1", "G2", "G3"],
            "environment_names": ["E1", "E2", "E3", "E4"],
        }
    })

class GxEFromDbRequest(BaseModel):
    """Request to analyze data directly from DB"""
    study_db_ids: List[str] = Field(..., description="List of Study DB IDs (Environments)")
    trait_db_id: str = Field(..., description="Trait DB ID (Yield)")
    method: GxEMethod = Field(GxEMethod.AMMI, description="Analysis method")
    n_components: int = Field(2, ge=1, le=10, description="Number of components (AMMI/GGE)")
    scaling: GGEScaling = Field(GGEScaling.SYMMETRIC, description="Scaling method (GGE only)")


class AMMIRequest(GxEDataInput):
    """Request for AMMI analysis"""
    n_components: int = Field(2, ge=1, le=10, description="Number of IPCA components")


class GGERequest(GxEDataInput):
    """Request for GGE biplot analysis"""
    n_components: int = Field(2, ge=1, le=10, description="Number of PC components")
    scaling: int = Field(0, ge=0, le=2, description="Scaling: 0=symmetric, 1=genotype, 2=environment")


class MegaEnvRequest(BaseModel):
    """Request for mega-environment identification"""
    environment_scores: List[List[float]]
    environment_names: List[str]
    n_clusters: int = Field(3, ge=2, le=10)


# ============================================
# ENDPOINTS
# ============================================

@router.post("/analyze-from-db")
async def analyze_from_db(
    request: GxEFromDbRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform GxE analysis using data fetched directly from the database
    """
    service = get_gxe_service()
    
    # 1. Get Matrix
    data = await service.get_observation_matrix(
        db=db, 
        study_db_ids=request.study_db_ids, 
        trait_db_id=request.trait_db_id
    )
    
    if "error" in data:
        raise HTTPException(404, detail=data["error"])
        
    yield_matrix = np.array(data["yield_matrix"])
    genotype_names = data["genotype_names"]
    environment_names = data["environment_names"]
    
    # 2. Run Analysis
    try:
        if request.method == GxEMethod.AMMI:
            result = service.ammi_analysis(
                yield_matrix=yield_matrix,
                genotype_names=genotype_names,
                environment_names=environment_names,
                n_components=request.n_components
            )
            return {
                "method": "AMMI",
                "n_genotypes": len(genotype_names),
                "n_environments": len(environment_names),
                **result.to_dict()
            }
            
        elif request.method == GxEMethod.GGE:
            result = service.gge_biplot(
                yield_matrix=yield_matrix,
                genotype_names=genotype_names,
                environment_names=environment_names,
                n_components=request.n_components,
                scaling=request.scaling
            )
            winners = service.identify_winning_genotypes(result)
            return {
                "method": "GGE",
                "n_genotypes": len(genotype_names),
                **result.to_dict(),
                "winning_genotypes": winners
            }
            
        elif request.method == GxEMethod.FINLAY_WILKINSON:
            result = service.finlay_wilkinson(
                yield_matrix=yield_matrix,
                genotype_names=genotype_names,
                environment_names=environment_names
            )
            return {
                "method": "Finlay-Wilkinson",
                **result.to_dict()
            }
            
    except Exception as e:
        raise HTTPException(500, detail=f"Analysis failed: {str(e)}")


@router.post("/ammi")
async def ammi_analysis(request: AMMIRequest):
    """
    AMMI (Additive Main effects and Multiplicative Interaction) Analysis
    
    Decomposes yield variation into:
    - Grand mean (μ)
    - Genotype main effects (G_i)
    - Environment main effects (E_j)
    - G×E interaction (via SVD → IPCA scores)
    
    Returns genotype and environment scores for biplot visualization.
    """
    service = get_gxe_service()
    
    try:
        yield_matrix = np.array(request.yield_matrix)
        
        if yield_matrix.shape[0] != len(request.genotype_names):
            raise HTTPException(400, "Number of rows must match genotype_names length")
        if yield_matrix.shape[1] != len(request.environment_names):
            raise HTTPException(400, "Number of columns must match environment_names length")
        
        result = service.ammi_analysis(
            yield_matrix=yield_matrix,
            genotype_names=request.genotype_names,
            environment_names=request.environment_names,
            n_components=request.n_components,
        )
        
        return {
            "method": "AMMI",
            "n_genotypes": len(request.genotype_names),
            "n_environments": len(request.environment_names),
            "n_components": request.n_components,
            **result.to_dict(),
        }
        
    except Exception as e:
        raise HTTPException(500, f"AMMI analysis failed: {str(e)}")


@router.post("/gge")
async def gge_biplot(request: GGERequest):
    """
    GGE (Genotype + Genotype-by-Environment) Biplot Analysis
    
    Environment-centered analysis that combines G + GE effects.
    Useful for:
    - Identifying winning genotypes per environment
    - Mega-environment delineation
    - Genotype stability assessment
    
    Scaling options:
    - 0: Symmetric (default) - balanced view
    - 1: Genotype-focused - compare genotypes
    - 2: Environment-focused - compare environments
    """
    service = get_gxe_service()
    
    try:
        yield_matrix = np.array(request.yield_matrix)
        scaling = GGEScaling(request.scaling)
        
        result = service.gge_biplot(
            yield_matrix=yield_matrix,
            genotype_names=request.genotype_names,
            environment_names=request.environment_names,
            n_components=request.n_components,
            scaling=scaling,
        )
        
        # Also get winning genotypes
        winners = service.identify_winning_genotypes(result)
        
        return {
            "method": "GGE",
            "n_genotypes": len(request.genotype_names),
            "n_environments": len(request.environment_names),
            "n_components": request.n_components,
            **result.to_dict(),
            "winning_genotypes": winners,
        }
        
    except Exception as e:
        raise HTTPException(500, f"GGE analysis failed: {str(e)}")


@router.post("/finlay-wilkinson")
async def finlay_wilkinson(request: GxEDataInput):
    """
    Finlay-Wilkinson Regression Analysis
    
    Regresses genotype yield against environment index.
    
    Interpretation of slope (β):
    - β ≈ 1: Average stability
    - β < 1: Below-average response (stable, adapted to poor environments)
    - β > 1: Above-average response (responsive to good environments)
    
    Combined with mean yield:
    - High mean + β ≈ 1: Ideal genotype (high yield, stable)
    - High mean + β > 1: Good for favorable environments
    - Low mean + β < 1: Adapted to stress environments
    """
    service = get_gxe_service()
    
    try:
        yield_matrix = np.array(request.yield_matrix)
        
        result = service.finlay_wilkinson(
            yield_matrix=yield_matrix,
            genotype_names=request.genotype_names,
            environment_names=request.environment_names,
        )
        
        return {
            "method": "Finlay-Wilkinson",
            "n_genotypes": len(request.genotype_names),
            "n_environments": len(request.environment_names),
            **result.to_dict(),
        }
        
    except Exception as e:
        raise HTTPException(500, f"Finlay-Wilkinson analysis failed: {str(e)}")


@router.post("/mega-environments")
async def identify_mega_environments(request: GGERequest):
    """
    Identify Mega-Environments from GGE Analysis
    
    Clusters environments based on their GGE scores.
    Environments in the same mega-environment have similar
    genotype rankings and can share variety recommendations.
    """
    service = get_gxe_service()
    
    try:
        yield_matrix = np.array(request.yield_matrix)
        scaling = GGEScaling(request.scaling)
        
        # First run GGE
        gge_result = service.gge_biplot(
            yield_matrix=yield_matrix,
            genotype_names=request.genotype_names,
            environment_names=request.environment_names,
            n_components=request.n_components,
            scaling=scaling,
        )
        
        # Then identify mega-environments
        mega_envs = service.identify_mega_environments(
            gge_result,
            n_clusters=min(3, len(request.environment_names) - 1)
        )
        
        return {
            "method": "Mega-Environment Analysis",
            **mega_envs,
            "gge_variance_explained": gge_result.variance_explained.tolist(),
        }
        
    except Exception as e:
        raise HTTPException(500, f"Mega-environment analysis failed: {str(e)}")


@router.get("/methods")
async def list_methods():
    """List available G×E analysis methods"""
    return {
        "methods": [
            {
                "id": "ammi",
                "name": "AMMI",
                "full_name": "Additive Main effects and Multiplicative Interaction",
                "description": "Separates main effects from interaction, uses SVD for IPCA",
                "use_case": "Understanding G×E structure, biplot visualization",
            },
            {
                "id": "gge",
                "name": "GGE Biplot",
                "full_name": "Genotype + Genotype-by-Environment",
                "description": "Environment-centered, combines G + GE for variety evaluation",
                "use_case": "Which-won-where analysis, mega-environment delineation",
            },
            {
                "id": "finlay_wilkinson",
                "name": "Finlay-Wilkinson",
                "full_name": "Finlay-Wilkinson Regression",
                "description": "Regresses yield on environment index for stability",
                "use_case": "Genotype stability classification, adaptation patterns",
            },
        ]
    }
