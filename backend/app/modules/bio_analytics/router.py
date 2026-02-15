from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from app.modules.bio_analytics.services.genomic_prediction import export_service
from app.modules.bio_analytics.services.gwas_analysis import gwas_service


router = APIRouter(tags=["Bio-Analytics"])

class TrainModelRequest(BaseModel):
    model_name: str
    trait_name: str
    markers: List[List[int]] # 0, 1, 2 matrix
    phenotypes: List[float]
    marker_names: List[str]
    germplasm_ids: List[str]
    heritability: Optional[float] = 0.5

@router.post("/train/rr-blup")
async def train_rrblup(
    request: TrainModelRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Train a Genomic Selection model using RR-BLUP.
    Returns model ID and accuracy stats.
    """
    if len(request.phenotypes) != len(request.markers):
        raise HTTPException(status_code=400, detail="Phenotype and Marker counts mismatch")
        
    result = await export_service.train_rrblup_model(
        db=db,
        user=user,
        model_name=request.model_name,
        trait_name=request.trait_name,
        markers=request.markers,
        phenotypes=request.phenotypes,
        marker_names=request.marker_names,
        germplasm_ids=request.germplasm_ids,
        heritability=request.heritability
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result



class TrainModelFromStorageRequest(BaseModel):
    model_name: str
    trait_name: str
    variant_set_id: int
    phenotype_data: Dict[str, float] # {sample_name: value}
    heritability: Optional[float] = 0.5

@router.post("/train/from-storage")
async def train_from_storage(
    request: TrainModelFromStorageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Train using server-side VCF/Zarr data.
    """
    try:
        result = await export_service.train_from_variant_set(
            db=db,
            user=user,
            variant_set_id=request.variant_set_id,
            model_name=request.model_name,
            trait_name=request.trait_name,
            phenotype_data=request.phenotype_data,
            heritability=request.heritability
        )
        
        if "error" in result:
             raise HTTPException(status_code=500, detail=result["error"])
             
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class MarkerInfo(BaseModel):
    name: str
    chromosome: str
    position: int

class RunGWASRequest(BaseModel):
    run_name: str
    trait_name: str
    method: str = "glm" # glm, mlm
    markers: List[MarkerInfo]
    genotypes: List[List[float]]
    phenotypes: List[float]
    kinship: Optional[List[List[float]]] = None

@router.post("/gwas/run")
async def run_gwas_analysis(
    request: RunGWASRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Run GWAS Analysis (GLM/MLM) and save results.
    """
    if len(request.phenotypes) != len(request.genotypes):
        raise HTTPException(status_code=400, detail="Phenotype and Genotype counts mismatch")

    # Convert MarkerInfo objects to dicts for service
    markers_dict = [m.model_dump() for m in request.markers]

    result = await gwas_service.run_gwas(
        db=db,
        user=user,
        run_name=request.run_name,
        trait_name=request.trait_name,
        method=request.method,
        markers=markers_dict,
        genotypes=request.genotypes,
        phenotypes=request.phenotypes,
        kinship=request.kinship
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

