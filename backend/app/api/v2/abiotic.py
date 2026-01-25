"""
Abiotic Stress API
Endpoints for abiotic stress tolerance tracking and analysis

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
from app.models.stress_resistance import AbioticStress, ToleranceGene, PyramidingStrategy

router = APIRouter(prefix="/abiotic", tags=["Abiotic Stress"])


# ============================================
# SCHEMAS
# ============================================

class StressCreate(BaseModel):
    name: str
    category: str
    description: str


class GeneCreate(BaseModel):
    name: str
    stress_id: str
    mechanism: str
    crop: str
    chromosome: Optional[str] = None
    markers: List[str] = []


class IndicesRequest(BaseModel):
    control_yield: float
    stress_yield: float


# ============================================
# HELPER FUNCTIONS
# ============================================

def stress_to_dict(stress: AbioticStress) -> dict:
    """Convert AbioticStress model to API response dict"""
    return {
        "stress_id": stress.stress_code,
        "id": str(stress.id),
        "name": stress.name,
        "category": stress.category.value if stress.category else None,
        "description": stress.description,
        "screening_method": stress.screening_method,
        "screening_stages": stress.screening_stages or [],
        "screening_duration": stress.screening_duration,
        "indicators": stress.indicators or [],
    }


def gene_to_dict(gene: ToleranceGene, stress_name: str = None) -> dict:
    """Convert ToleranceGene model to API response dict"""
    return {
        "gene_id": gene.gene_code,
        "id": str(gene.id),
        "name": gene.name,
        "stress_id": str(gene.stress_id),
        "stress_name": stress_name,
        "mechanism": gene.mechanism,
        "crop": gene.crop,
        "chromosome": gene.chromosome,
        "markers": gene.markers or [],
        "source_germplasm": gene.source_germplasm,
        "is_validated": gene.is_validated,
    }


# ============================================
# ENDPOINTS
# ============================================

@router.get("/stress-types")
async def get_stress_types(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term"),
    db: AsyncSession = Depends(get_db),
):
    """Get all stress types with optional filters"""
    query = select(AbioticStress).where(AbioticStress.is_active == True)
    
    if category:
        query = query.where(AbioticStress.category == category.lower())
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (AbioticStress.name.ilike(search_pattern)) |
            (AbioticStress.description.ilike(search_pattern))
        )
    
    result = await db.execute(query.order_by(AbioticStress.name))
    stresses = result.scalars().all()
    
    return {
        "data": [stress_to_dict(s) for s in stresses],
        "total": len(stresses)
    }


@router.get("/stress-types/{stress_id}")
async def get_stress_type(
    stress_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific stress type"""
    # Try to find by stress_code first, then by UUID
    query = select(AbioticStress).where(
        (AbioticStress.stress_code == stress_id) |
        (AbioticStress.id == stress_id if len(stress_id) == 36 else False)
    )
    
    result = await db.execute(query)
    stress = result.scalar_one_or_none()
    
    if not stress:
        raise HTTPException(status_code=404, detail="Stress type not found")
    
    return stress_to_dict(stress)


@router.get("/genes")
async def get_genes(
    stress_id: Optional[str] = Query(None, description="Filter by stress type"),
    crop: Optional[str] = Query(None, description="Filter by crop"),
    search: Optional[str] = Query(None, description="Search term"),
    db: AsyncSession = Depends(get_db),
):
    """Get all tolerance genes with optional filters"""
    query = select(ToleranceGene).options(
        selectinload(ToleranceGene.stress)
    ).where(ToleranceGene.is_active == True)
    
    if stress_id:
        # Find stress by code or UUID
        stress_query = select(AbioticStress).where(
            (AbioticStress.stress_code == stress_id) |
            (AbioticStress.id == stress_id if len(stress_id) == 36 else False)
        )
        stress_result = await db.execute(stress_query)
        stress = stress_result.scalar_one_or_none()
        if stress:
            query = query.where(ToleranceGene.stress_id == stress.id)
    
    if crop:
        query = query.where(
            (ToleranceGene.crop.ilike(crop)) |
            (ToleranceGene.crop == "Multiple")
        )
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (ToleranceGene.name.ilike(search_pattern)) |
            (ToleranceGene.mechanism.ilike(search_pattern))
        )
    
    result = await db.execute(query.order_by(ToleranceGene.name))
    genes = result.scalars().all()
    
    return {
        "data": [gene_to_dict(g, g.stress.name if g.stress else None) for g in genes],
        "total": len(genes)
    }


@router.get("/genes/{gene_id}")
async def get_gene(
    gene_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific tolerance gene"""
    query = select(ToleranceGene).options(
        selectinload(ToleranceGene.stress)
    ).where(
        (ToleranceGene.gene_code == gene_id) |
        (ToleranceGene.id == gene_id if len(gene_id) == 36 else False)
    )
    
    result = await db.execute(query)
    gene = result.scalar_one_or_none()
    
    if not gene:
        raise HTTPException(status_code=404, detail="Gene not found")
    
    return gene_to_dict(gene, gene.stress.name if gene.stress else None)


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get list of stress categories"""
    query = select(AbioticStress.category).where(
        AbioticStress.is_active == True
    ).distinct()
    
    result = await db.execute(query)
    categories = [row[0].value for row in result.all() if row[0]]
    
    return {"categories": sorted(set(categories))}


@router.get("/crops")
async def get_crops(db: AsyncSession = Depends(get_db)):
    """Get list of crops with tolerance genes"""
    query = select(ToleranceGene.crop).where(
        (ToleranceGene.is_active == True) &
        (ToleranceGene.crop != "Multiple")
    ).distinct()
    
    result = await db.execute(query)
    crops = [row[0] for row in result.all() if row[0]]
    
    return {"crops": sorted(set(crops))}


@router.get("/statistics")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """Get abiotic stress statistics"""
    # Count stresses
    stress_count = await db.execute(
        select(func.count(AbioticStress.id)).where(AbioticStress.is_active == True)
    )
    total_stresses = stress_count.scalar() or 0
    
    # Count genes
    gene_count = await db.execute(
        select(func.count(ToleranceGene.id)).where(ToleranceGene.is_active == True)
    )
    total_genes = gene_count.scalar() or 0
    
    # Count categories
    cat_result = await db.execute(
        select(AbioticStress.category).where(AbioticStress.is_active == True).distinct()
    )
    categories = [row[0].value for row in cat_result.all() if row[0]]
    
    # Count MAS-ready genes (have markers)
    mas_count = await db.execute(
        select(func.count(ToleranceGene.id)).where(
            (ToleranceGene.is_active == True) &
            (ToleranceGene.markers != None) &
            (func.array_length(ToleranceGene.markers, 1) > 0)
        )
    )
    mas_ready = mas_count.scalar() or 0
    
    # Stresses by category
    stresses_by_cat = {}
    for cat in categories:
        count_result = await db.execute(
            select(func.count(AbioticStress.id)).where(
                (AbioticStress.is_active == True) &
                (AbioticStress.category == cat)
            )
        )
        stresses_by_cat[cat] = count_result.scalar() or 0
    
    # Genes by stress
    genes_by_stress = {}
    stress_result = await db.execute(
        select(AbioticStress).where(AbioticStress.is_active == True)
    )
    for stress in stress_result.scalars().all():
        gene_count_result = await db.execute(
            select(func.count(ToleranceGene.id)).where(
                (ToleranceGene.is_active == True) &
                (ToleranceGene.stress_id == stress.id)
            )
        )
        genes_by_stress[stress.name] = gene_count_result.scalar() or 0
    
    return {
        "totalStressTypes": total_stresses,
        "totalGenes": total_genes,
        "totalCategories": len(categories),
        "masReadyGenes": mas_ready,
        "stressesByCategory": stresses_by_cat,
        "genesByStress": genes_by_stress,
    }


@router.post("/calculate/indices")
async def calculate_indices(request: IndicesRequest):
    """Calculate stress tolerance indices from yield data"""
    control = request.control_yield
    stress = request.stress_yield
    
    if control <= 0:
        raise HTTPException(status_code=400, detail="Control yield must be positive")
    
    # Calculate various stress indices
    ssi = (control - stress) / control  # Stress Susceptibility Index
    sti = (control * stress) / (control ** 2)  # Stress Tolerance Index
    ysi = stress / control  # Yield Stability Index
    gmp = (control * stress) ** 0.5  # Geometric Mean Productivity
    mp = (control + stress) / 2  # Mean Productivity
    tol = control - stress  # Tolerance Index
    hm = (2 * control * stress) / (control + stress) if (control + stress) > 0 else 0  # Harmonic Mean
    
    return {
        "data": {
            "indices": {
                "SSI": round(ssi, 4),
                "STI": round(sti, 4),
                "YSI": round(ysi, 4),
                "GMP": round(gmp, 4),
                "MP": round(mp, 4),
                "TOL": round(tol, 4),
                "HM": round(hm, 4),
            },
            "interpretation": {
                "SSI": "Lower is better (less susceptible)" if ssi > 0.5 else "Good tolerance",
                "STI": "Higher is better" if sti < 0.7 else "Good tolerance",
                "YSI": "Higher is better (more stable)" if ysi < 0.7 else "Good stability",
            },
            "recommendation": "tolerant" if ysi >= 0.7 and ssi <= 0.5 else "susceptible",
        }
    }


@router.get("/screening-protocols")
async def get_screening_protocols(db: AsyncSession = Depends(get_db)):
    """Get standard screening protocols for abiotic stresses"""
    # Get protocols from database (screening info stored in AbioticStress)
    query = select(AbioticStress).where(
        (AbioticStress.is_active == True) &
        (AbioticStress.screening_method != None)
    )
    
    result = await db.execute(query)
    stresses = result.scalars().all()
    
    protocols = []
    for stress in stresses:
        if stress.screening_method:
            protocols.append({
                "stress": stress.name,
                "method": stress.screening_method,
                "stages": stress.screening_stages or [],
                "duration": stress.screening_duration,
                "indicators": stress.indicators or [],
            })
    
    return {"protocols": protocols}
