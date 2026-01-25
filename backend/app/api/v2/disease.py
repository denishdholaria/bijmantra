"""
Disease Resistance API
Endpoints for disease management and resistance gene tracking

Migrated to database: December 25, 2025 (Session 17)
"""
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.stress_resistance import Disease, ResistanceGene, PyramidingStrategy

router = APIRouter(prefix="/disease", tags=["Disease Resistance"])


# ============================================
# SCHEMAS
# ============================================

class DiseaseCreate(BaseModel):
    name: str
    pathogen: str
    pathogen_type: str
    crop: str
    symptoms: str
    severity_scale: List[str] = []


class GeneCreate(BaseModel):
    gene_name: str
    disease_id: str
    chromosome: Optional[str] = None
    resistance_type: str
    source_germplasm: Optional[str] = None
    markers: List[str] = []


# ============================================
# HELPER FUNCTIONS
# ============================================

def disease_to_dict(disease: Disease) -> dict:
    """Convert Disease model to API response dict"""
    return {
        "id": disease.disease_code,
        "db_id": str(disease.id),
        "name": disease.name,
        "pathogen": disease.pathogen,
        "pathogen_type": disease.pathogen_type.value if disease.pathogen_type else None,
        "crop": disease.crop,
        "symptoms": disease.symptoms,
        "severity_scale": disease.severity_scale or [],
    }


def gene_to_dict(gene: ResistanceGene, disease_name: str = None) -> dict:
    """Convert ResistanceGene model to API response dict"""
    return {
        "id": gene.gene_code,
        "db_id": str(gene.id),
        "gene_name": gene.name,
        "disease_id": str(gene.disease_id),
        "disease_name": disease_name,
        "chromosome": gene.chromosome,
        "resistance_type": gene.resistance_type.value if gene.resistance_type else None,
        "source_germplasm": gene.source_germplasm,
        "markers": gene.markers or [],
        "is_validated": gene.is_validated,
    }


# ============================================
# ENDPOINTS
# ============================================

@router.get("/diseases")
async def get_diseases(
    crop: Optional[str] = Query(None, description="Filter by crop"),
    pathogen_type: Optional[str] = Query(None, description="Filter by pathogen type"),
    search: Optional[str] = Query(None, description="Search term"),
    db: AsyncSession = Depends(get_db),
):
    """Get all diseases with optional filters"""
    query = select(Disease).where(Disease.is_active == True)
    
    if crop:
        query = query.where(Disease.crop.ilike(crop))
    
    if pathogen_type:
        query = query.where(Disease.pathogen_type == pathogen_type.lower())
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Disease.name.ilike(search_pattern)) |
            (Disease.pathogen.ilike(search_pattern))
        )
    
    result = await db.execute(query.order_by(Disease.name))
    diseases = result.scalars().all()
    
    return {
        "diseases": [disease_to_dict(d) for d in diseases],
        "total": len(diseases)
    }


@router.get("/diseases/{disease_id}")
async def get_disease(
    disease_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific disease"""
    query = select(Disease).where(
        (Disease.disease_code == disease_id) |
        (Disease.id == disease_id if len(disease_id) == 36 else False)
    )
    
    result = await db.execute(query)
    disease = result.scalar_one_or_none()
    
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    return disease_to_dict(disease)


@router.get("/genes")
async def get_genes(
    disease_id: Optional[str] = Query(None, description="Filter by disease"),
    resistance_type: Optional[str] = Query(None, description="Filter by resistance type"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    search: Optional[str] = Query(None, description="Search term"),
    db: AsyncSession = Depends(get_db),
):
    """Get all resistance genes with optional filters"""
    query = select(ResistanceGene).options(
        selectinload(ResistanceGene.disease)
    ).where(ResistanceGene.is_active == True)
    
    if disease_id:
        # Find disease by code or UUID
        disease_query = select(Disease).where(
            (Disease.disease_code == disease_id) |
            (Disease.id == disease_id if len(disease_id) == 36 else False)
        )
        disease_result = await db.execute(disease_query)
        disease = disease_result.scalar_one_or_none()
        if disease:
            query = query.where(ResistanceGene.disease_id == disease.id)
    
    if resistance_type:
        query = query.where(ResistanceGene.resistance_type == resistance_type.lower())
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(ResistanceGene.name.ilike(search_pattern))
    
    result = await db.execute(query.order_by(ResistanceGene.name))
    genes = result.scalars().all()
    
    return {
        "genes": [gene_to_dict(g, g.disease.name if g.disease else None) for g in genes],
        "total": len(genes)
    }


@router.get("/genes/{gene_id}")
async def get_gene(
    gene_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific resistance gene"""
    query = select(ResistanceGene).options(
        selectinload(ResistanceGene.disease)
    ).where(
        (ResistanceGene.gene_code == gene_id) |
        (ResistanceGene.id == gene_id if len(gene_id) == 36 else False)
    )
    
    result = await db.execute(query)
    gene = result.scalar_one_or_none()
    
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")
    
    return gene_to_dict(gene, gene.disease.name if gene.disease else None)


@router.get("/crops")
async def get_crops(db: AsyncSession = Depends(get_db)):
    """Get list of unique crops"""
    query = select(Disease.crop).where(Disease.is_active == True).distinct()
    
    result = await db.execute(query)
    crops = [row[0] for row in result.all() if row[0]]
    
    return {"crops": sorted(set(crops))}


@router.get("/pathogen-types")
async def get_pathogen_types(db: AsyncSession = Depends(get_db)):
    """Get list of pathogen types"""
    query = select(Disease.pathogen_type).where(Disease.is_active == True).distinct()
    
    result = await db.execute(query)
    types = [row[0].value for row in result.all() if row[0]]
    
    return {"pathogenTypes": sorted(set(types))}


@router.get("/resistance-types")
async def get_resistance_types(db: AsyncSession = Depends(get_db)):
    """Get list of resistance types"""
    query = select(ResistanceGene.resistance_type).where(
        ResistanceGene.is_active == True
    ).distinct()
    
    result = await db.execute(query)
    types = [row[0].value for row in result.all() if row[0]]
    
    return {"resistanceTypes": sorted(set(types))}


@router.get("/statistics")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Get disease resistance statistics"""
    # Count diseases
    disease_count = await db.execute(
        select(func.count(Disease.id)).where(Disease.is_active == True)
    )
    total_diseases = disease_count.scalar() or 0
    
    # Count genes
    gene_count = await db.execute(
        select(func.count(ResistanceGene.id)).where(ResistanceGene.is_active == True)
    )
    total_genes = gene_count.scalar() or 0
    
    # Count crops
    crop_result = await db.execute(
        select(Disease.crop).where(Disease.is_active == True).distinct()
    )
    crops = [row[0] for row in crop_result.all() if row[0]]
    
    # Count MAS-ready genes (have markers)
    mas_count = await db.execute(
        select(func.count(ResistanceGene.id)).where(
            (ResistanceGene.is_active == True) &
            (ResistanceGene.markers != None) &
            (func.array_length(ResistanceGene.markers, 1) > 0)
        )
    )
    mas_ready = mas_count.scalar() or 0
    
    # Diseases by crop
    diseases_by_crop = {}
    for crop in crops:
        count_result = await db.execute(
            select(func.count(Disease.id)).where(
                (Disease.is_active == True) &
                (Disease.crop == crop)
            )
        )
        diseases_by_crop[crop] = count_result.scalar() or 0
    
    # Genes by resistance type
    genes_by_type = {}
    type_result = await db.execute(
        select(ResistanceGene.resistance_type).where(
            ResistanceGene.is_active == True
        ).distinct()
    )
    for row in type_result.all():
        if row[0]:
            rt = row[0].value
            count_result = await db.execute(
                select(func.count(ResistanceGene.id)).where(
                    (ResistanceGene.is_active == True) &
                    (ResistanceGene.resistance_type == row[0])
                )
            )
            genes_by_type[rt] = count_result.scalar() or 0
    
    return {
        "totalDiseases": total_diseases,
        "totalGenes": total_genes,
        "totalCrops": len(crops),
        "masReadyGenes": mas_ready,
        "diseasesByCrop": diseases_by_crop,
        "genesByResistanceType": genes_by_type,
    }


@router.get("/pyramiding-strategies")
async def get_pyramiding_strategies(db: AsyncSession = Depends(get_db)):
    """Get gene pyramiding strategies"""
    query = select(PyramidingStrategy).where(PyramidingStrategy.is_active == True)
    
    result = await db.execute(query.order_by(PyramidingStrategy.name))
    strategies = result.scalars().all()
    
    return {
        "strategies": [
            {
                "id": s.strategy_code,
                "name": s.name,
                "disease": s.target_disease,
                "stress": s.target_stress,
                "genes": s.gene_names or [],
                "description": s.description,
                "status": s.status,
                "warning": s.warning_message,
            }
            for s in strategies
        ]
    }
