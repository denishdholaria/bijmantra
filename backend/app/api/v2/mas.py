"""
Marker-Assisted Selection (MAS) API for Plant Breeding
QTL analysis, marker scoring, and selection decisions

Endpoints:
- POST /api/v2/mas/markers - Register markers
- GET /api/v2/mas/markers - List markers
- POST /api/v2/mas/score - Score genotypes
- POST /api/v2/mas/foreground - Foreground selection
- POST /api/v2/mas/background - Background selection
- POST /api/v2/mas/mabc - MABC selection
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.services.marker_assisted import get_mas_service

router = APIRouter(prefix="/mas", tags=["Marker-Assisted Selection"])


# ============================================
# SCHEMAS
# ============================================

class MarkerRegisterRequest(BaseModel):
    """Request to register a marker"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "marker_id": "M1",
            "name": "Xa21_SNP",
            "chromosome": "11",
            "position": 45.2,
            "marker_type": "snp",
            "target_allele": "A",
            "linked_trait": "bacterial_blight_resistance",
            "distance_to_qtl": 0.5
        }
    })

    marker_id: str = Field(..., description="Unique marker ID")
    name: str = Field(..., description="Marker name")
    chromosome: str = Field(..., description="Chromosome")
    position: float = Field(..., description="Position (cM or bp)")
    marker_type: str = Field("snp", description="Type: snp, ssr, indel, kasp")
    target_allele: str = Field(..., description="Favorable allele")
    linked_trait: str = Field(..., description="Associated trait")
    distance_to_qtl: float = Field(0.0, description="Distance to QTL in cM")


class BulkMarkerRequest(BaseModel):
    """Request to register multiple markers"""
    markers: List[MarkerRegisterRequest]


class GenotypeScoreRequest(BaseModel):
    """Request to score a genotype"""
    individual_id: str
    marker_id: str
    allele1: str
    allele2: str


class BulkScoreRequest(BaseModel):
    """Request to score multiple genotypes"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": [
                {"individual_id": "P1", "marker_id": "M1", "allele1": "A", "allele2": "A"},
                {"individual_id": "P1", "marker_id": "M2", "allele1": "T", "allele2": "C"},
                {"individual_id": "P2", "marker_id": "M1", "allele1": "G", "allele2": "A"},
                {"individual_id": "P2", "marker_id": "M2", "allele1": "T", "allele2": "T"}
            ]
        }
    })

    genotypes: List[GenotypeScoreRequest]


class ForegroundRequest(BaseModel):
    """Request for foreground selection"""
    individual_ids: List[str] = Field(..., description="Individuals to evaluate")
    target_markers: List[str] = Field(..., description="Markers linked to target traits")


class BackgroundRequest(BaseModel):
    """Request for background selection"""
    individual_ids: List[str] = Field(..., description="Individuals to evaluate")
    recurrent_parent_id: str = Field(..., description="Recurrent parent ID")
    background_markers: List[str] = Field(..., description="Genome-wide markers")


class MABCRequest(BaseModel):
    """Request for MABC selection"""
    individual_ids: List[str] = Field(..., description="Individuals to evaluate")
    target_markers: List[str] = Field(..., description="Foreground markers")
    background_markers: List[str] = Field(..., description="Background markers")
    recurrent_parent_id: str = Field(..., description="Recurrent parent ID")
    fg_weight: float = Field(0.6, ge=0, le=1, description="Foreground weight")
    bg_weight: float = Field(0.4, ge=0, le=1, description="Background weight")
    min_fg_score: float = Field(50.0, ge=0, le=100, description="Min foreground score")
    min_bg_score: float = Field(0.0, ge=0, le=100, description="Min background score")
    n_select: int = Field(10, ge=1, description="Number to select")


# ============================================
# ENDPOINTS
# ============================================

@router.post("/markers")
async def register_marker(request: MarkerRegisterRequest):
    """
    Register a molecular marker
    
    Markers are linked to QTLs/genes controlling target traits.
    The target_allele is the favorable allele to select for.
    """
    service = get_mas_service()
    
    try:
        marker = service.register_marker(
            marker_id=request.marker_id,
            name=request.name,
            chromosome=request.chromosome,
            position=request.position,
            marker_type=request.marker_type,
            target_allele=request.target_allele,
            linked_trait=request.linked_trait,
            distance_to_qtl=request.distance_to_qtl,
        )
        
        return {
            "success": True,
            "message": f"Marker {request.marker_id} registered",
            **marker.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register marker: {str(e)}")


@router.post("/markers/bulk")
async def register_markers_bulk(request: BulkMarkerRequest):
    """Register multiple markers at once"""
    service = get_mas_service()
    
    registered = 0
    errors = []
    
    for m in request.markers:
        try:
            service.register_marker(
                marker_id=m.marker_id,
                name=m.name,
                chromosome=m.chromosome,
                position=m.position,
                marker_type=m.marker_type,
                target_allele=m.target_allele,
                linked_trait=m.linked_trait,
                distance_to_qtl=m.distance_to_qtl,
            )
            registered += 1
        except Exception as e:
            errors.append({"marker_id": m.marker_id, "error": str(e)})
    
    return {
        "success": True,
        "registered": registered,
        "errors": len(errors),
        "error_details": errors,
    }


@router.get("/markers")
async def list_markers(
    chromosome: Optional[str] = Query(None, description="Filter by chromosome"),
    trait: Optional[str] = Query(None, description="Filter by linked trait")
):
    """List registered markers"""
    service = get_mas_service()
    
    markers = service.list_markers(chromosome=chromosome, trait=trait)
    
    return {
        "success": True,
        "count": len(markers),
        "filters": {"chromosome": chromosome, "trait": trait},
        "markers": markers,
    }


@router.get("/markers/{marker_id}")
async def get_marker(marker_id: str):
    """Get marker details"""
    service = get_mas_service()
    
    marker = service.get_marker(marker_id)
    if marker is None:
        raise HTTPException(404, f"Marker {marker_id} not found")
    
    return {
        "success": True,
        **marker,
    }


@router.post("/score")
async def score_genotypes(request: BulkScoreRequest):
    """
    Score genotypes for registered markers
    
    Records allele calls for each individual at each marker.
    Automatically determines if target allele is present.
    """
    service = get_mas_service()
    
    try:
        data = [g.model_dump() for g in request.genotypes]
        result = service.bulk_score(data)
        
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Scoring failed: {str(e)}")


@router.get("/genotypes/{individual_id}")
async def get_individual_genotypes(individual_id: str):
    """Get all genotypes for an individual"""
    service = get_mas_service()
    
    genotypes = service.get_individual_genotypes(individual_id)
    
    return {
        "success": True,
        "individual_id": individual_id,
        "n_markers": len(genotypes),
        "genotypes": genotypes,
    }


@router.post("/foreground")
async def foreground_selection(request: ForegroundRequest):
    """
    Foreground selection - select for target alleles
    
    Evaluates individuals for presence of favorable alleles
    at markers linked to target traits (e.g., disease resistance,
    quality traits).
    
    Score = (target alleles present / max possible) × 100%
    
    Higher score = more target alleles = better for target traits.
    """
    service = get_mas_service()
    
    try:
        results = service.foreground_selection(
            individual_ids=request.individual_ids,
            target_markers=request.target_markers,
        )
        
        return {
            "success": True,
            "n_evaluated": len(request.individual_ids),
            "n_markers": len(request.target_markers),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(500, f"Foreground selection failed: {str(e)}")


@router.post("/background")
async def background_selection(request: BackgroundRequest):
    """
    Background selection - select for recurrent parent genome recovery
    
    In backcross breeding, we want to recover the recurrent parent
    genome while retaining the introgressed trait.
    
    Score = (alleles matching recurrent parent / total) × 100%
    
    Higher score = more genome recovery = closer to recurrent parent.
    """
    service = get_mas_service()
    
    try:
        results = service.background_selection(
            individual_ids=request.individual_ids,
            recurrent_parent_id=request.recurrent_parent_id,
            background_markers=request.background_markers,
        )
        
        return {
            "success": True,
            "recurrent_parent": request.recurrent_parent_id,
            "n_evaluated": len(request.individual_ids),
            "n_markers": len(request.background_markers),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(500, f"Background selection failed: {str(e)}")


@router.post("/mabc")
async def mabc_selection(request: MABCRequest):
    """
    Marker-Assisted Backcrossing (MABC) selection
    
    Combines foreground and background selection for optimal
    introgression of target traits while recovering recurrent
    parent genome.
    
    Overall Score = (fg_weight × FG%) + (bg_weight × BG%)
    
    Typical weights:
    - Early BC generations: Higher FG weight (0.7-0.8)
    - Later BC generations: Higher BG weight (0.6-0.7)
    
    Selection criteria:
    - Must have target alleles (foreground)
    - Maximize genome recovery (background)
    """
    service = get_mas_service()
    
    try:
        result = service.mabc_selection(
            individual_ids=request.individual_ids,
            target_markers=request.target_markers,
            background_markers=request.background_markers,
            recurrent_parent_id=request.recurrent_parent_id,
            fg_weight=request.fg_weight,
            bg_weight=request.bg_weight,
            min_fg_score=request.min_fg_score,
            min_bg_score=request.min_bg_score,
            n_select=request.n_select,
        )
        
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"MABC selection failed: {str(e)}")


@router.get("/stats")
async def get_mas_stats():
    """Get MAS system statistics"""
    service = get_mas_service()
    
    return {
        "success": True,
        "n_markers": len(service.markers),
        "n_individuals_genotyped": len(service.genotypes),
        "markers_by_chromosome": _count_by_chromosome(service),
        "markers_by_trait": _count_by_trait(service),
    }


def _count_by_chromosome(service) -> Dict[str, int]:
    """Count markers by chromosome"""
    counts = {}
    for marker in service.markers.values():
        chr_name = marker.chromosome
        counts[chr_name] = counts.get(chr_name, 0) + 1
    return counts


def _count_by_trait(service) -> Dict[str, int]:
    """Count markers by linked trait"""
    counts = {}
    for marker in service.markers.values():
        trait = marker.linked_trait
        counts[trait] = counts.get(trait, 0) + 1
    return counts
