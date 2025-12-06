"""
Disease Resistance API
Track disease resistance genes, screening results, and resistance breeding
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.disease_resistance import disease_resistance_service

router = APIRouter(prefix="/disease", tags=["Disease Resistance"])


class DiseaseCreate(BaseModel):
    name: str
    pathogen: str
    crop: str
    disease_type: str
    symptoms: Optional[str] = None
    economic_impact: Optional[str] = None


class GeneCreate(BaseModel):
    name: str
    disease_id: str
    chromosome: str
    gene_type: str
    mechanism: Optional[str] = None
    markers: Optional[List[str]] = None
    donor_source: Optional[str] = None


class ScreeningRecord(BaseModel):
    genotype_id: str
    genotype_name: str
    screening_date: str
    method: str
    score: float
    scale: str
    reaction: str  # R, MR, MS, S, HS
    notes: Optional[str] = None


class GenePyramid(BaseModel):
    name: str
    target_disease_id: str
    gene_ids: List[str]
    description: Optional[str] = None


# Disease endpoints
@router.post("/diseases")
async def register_disease(data: DiseaseCreate):
    """Register a new disease"""
    disease = disease_resistance_service.register_disease(**data.model_dump())
    return {"status": "success", "data": disease}


@router.get("/diseases")
async def list_diseases(
    crop: Optional[str] = None,
    disease_type: Optional[str] = None,
):
    """List diseases with optional filters"""
    diseases = disease_resistance_service.list_diseases(
        crop=crop,
        disease_type=disease_type,
    )
    return {"status": "success", "data": diseases, "count": len(diseases)}


@router.get("/diseases/{disease_id}")
async def get_disease(disease_id: str):
    """Get disease details"""
    disease = disease_resistance_service.get_disease(disease_id)
    if not disease:
        raise HTTPException(status_code=404, detail=f"Disease {disease_id} not found")
    return {"status": "success", "data": disease}


# Gene endpoints
@router.post("/genes")
async def register_gene(data: GeneCreate):
    """Register a resistance gene"""
    gene = disease_resistance_service.register_gene(**data.model_dump())
    return {"status": "success", "data": gene}


@router.get("/genes")
async def list_genes(
    disease_id: Optional[str] = None,
    gene_type: Optional[str] = None,
):
    """List resistance genes"""
    genes = disease_resistance_service.list_genes(
        disease_id=disease_id,
        gene_type=gene_type,
    )
    return {"status": "success", "data": genes, "count": len(genes)}


@router.get("/genes/{gene_id}")
async def get_gene(gene_id: str):
    """Get gene details"""
    gene = disease_resistance_service.get_gene(gene_id)
    if not gene:
        raise HTTPException(status_code=404, detail=f"Gene {gene_id} not found")
    return {"status": "success", "data": gene}


# Screening endpoints
@router.post("/diseases/{disease_id}/screenings")
async def record_screening(disease_id: str, data: ScreeningRecord):
    """Record disease screening result"""
    try:
        screening = disease_resistance_service.record_screening(
            disease_id=disease_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": screening}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/diseases/{disease_id}/screenings")
async def get_screenings(
    disease_id: str,
    genotype_id: Optional[str] = None,
    reaction: Optional[str] = None,
):
    """Get screening results for a disease"""
    screenings = disease_resistance_service.get_screenings(
        disease_id=disease_id,
        genotype_id=genotype_id,
        reaction=reaction,
    )
    return {"status": "success", "data": screenings, "count": len(screenings)}


# Gene pyramid endpoints
@router.post("/pyramids")
async def create_pyramid(data: GenePyramid):
    """Create a gene pyramiding strategy"""
    pyramid = disease_resistance_service.create_gene_pyramid(**data.model_dump())
    return {"status": "success", "data": pyramid}


@router.get("/pyramids")
async def list_pyramids():
    """List all gene pyramids"""
    pyramids = disease_resistance_service.list_pyramids()
    return {"status": "success", "data": pyramids, "count": len(pyramids)}


@router.get("/pyramids/{pyramid_id}")
async def get_pyramid(pyramid_id: str):
    """Get gene pyramid details"""
    pyramid = disease_resistance_service.get_pyramid(pyramid_id)
    if not pyramid:
        raise HTTPException(status_code=404, detail=f"Pyramid {pyramid_id} not found")
    return {"status": "success", "data": pyramid}


# Profile and reference endpoints
@router.get("/profile/{genotype_id}")
async def get_resistance_profile(genotype_id: str):
    """Get complete resistance profile for a genotype"""
    profile = disease_resistance_service.get_resistance_profile(genotype_id)
    return {"status": "success", "data": profile}


@router.get("/reaction-scale")
async def get_reaction_scale():
    """Get standard disease reaction scale"""
    scale = disease_resistance_service.get_reaction_scale()
    return {"status": "success", "data": scale}


@router.get("/statistics")
async def get_statistics():
    """Get disease resistance statistics"""
    stats = disease_resistance_service.get_statistics()
    return {"status": "success", "data": stats}
