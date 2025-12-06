"""
Abiotic Stress Tolerance API
Track drought, heat, salinity, and other abiotic stress tolerance
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.abiotic_stress import abiotic_stress_service

router = APIRouter(prefix="/abiotic", tags=["Abiotic Stress"])


class GeneCreate(BaseModel):
    name: str
    stress_id: str
    mechanism: str
    crop: str
    chromosome: Optional[str] = None
    markers: Optional[List[str]] = None


class ScreeningRecord(BaseModel):
    genotype_id: str
    genotype_name: str
    screening_date: str
    treatment: str
    duration_days: int
    control_value: float
    stress_value: float
    trait: str
    notes: Optional[str] = None


class StressIndicesRequest(BaseModel):
    control_yield: float
    stress_yield: float


class RankRequest(BaseModel):
    screenings: List[Dict[str, Any]]
    index: str = "STI"


# Stress type endpoints
@router.get("/stress-types")
async def list_stress_types(
    category: Optional[str] = None,
):
    """List abiotic stress types"""
    stresses = abiotic_stress_service.list_stress_types(category=category)
    return {"status": "success", "data": stresses, "count": len(stresses)}


@router.get("/stress-types/{stress_id}")
async def get_stress_type(stress_id: str):
    """Get stress type details"""
    stress = abiotic_stress_service.get_stress_type(stress_id)
    if not stress:
        raise HTTPException(status_code=404, detail=f"Stress type {stress_id} not found")
    return {"status": "success", "data": stress}


# Gene endpoints
@router.post("/genes")
async def register_gene(data: GeneCreate):
    """Register a tolerance gene"""
    gene = abiotic_stress_service.register_gene(**data.model_dump())
    return {"status": "success", "data": gene}


@router.get("/genes")
async def list_genes(
    stress_id: Optional[str] = None,
    crop: Optional[str] = None,
):
    """List tolerance genes"""
    genes = abiotic_stress_service.list_genes(
        stress_id=stress_id,
        crop=crop,
    )
    return {"status": "success", "data": genes, "count": len(genes)}


# Screening endpoints
@router.post("/stress-types/{stress_id}/screenings")
async def record_screening(stress_id: str, data: ScreeningRecord):
    """Record stress screening result"""
    try:
        screening = abiotic_stress_service.record_screening(
            stress_id=stress_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": screening}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stress-types/{stress_id}/screenings")
async def get_screenings(
    stress_id: str,
    genotype_id: Optional[str] = None,
):
    """Get screening results for a stress type"""
    screenings = abiotic_stress_service.get_screenings(
        stress_id=stress_id,
        genotype_id=genotype_id,
    )
    return {"status": "success", "data": screenings, "count": len(screenings)}


# Analysis endpoints
@router.post("/calculate/indices")
async def calculate_stress_indices(data: StressIndicesRequest):
    """Calculate various stress tolerance indices"""
    result = abiotic_stress_service.calculate_stress_indices(
        control_yield=data.control_yield,
        stress_yield=data.stress_yield,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.post("/rank")
async def rank_genotypes(data: RankRequest):
    """Rank genotypes by stress tolerance index"""
    results = abiotic_stress_service.rank_genotypes(
        screenings=data.screenings,
        index=data.index,
    )
    return {"status": "success", "data": results, "count": len(results)}


@router.get("/profile/{genotype_id}")
async def get_tolerance_profile(genotype_id: str):
    """Get complete stress tolerance profile for a genotype"""
    profile = abiotic_stress_service.get_tolerance_profile(genotype_id)
    return {"status": "success", "data": profile}


@router.get("/statistics")
async def get_statistics():
    """Get abiotic stress statistics"""
    stats = abiotic_stress_service.get_statistics()
    return {"status": "success", "data": stats}
