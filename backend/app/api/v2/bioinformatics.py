"""
Bioinformatics API for Plant Molecular Breeding
Sequence analysis, primer design, and molecular marker tools

Endpoints:
- POST /api/v2/bioinformatics/analyze - Sequence analysis
- POST /api/v2/bioinformatics/primers - Primer design
- POST /api/v2/bioinformatics/restriction - Restriction enzyme sites
- POST /api/v2/bioinformatics/translate - DNA to protein translation
- POST /api/v2/bioinformatics/reverse-complement - Reverse complement
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from app.services.bioinformatics import get_bioinformatics_service

router = APIRouter(prefix="/bioinformatics", tags=["Bioinformatics"])


# ============================================
# SCHEMAS
# ============================================

class SequenceInput(BaseModel):
    """Input for sequence analysis"""
    sequence: str = Field(..., min_length=1, description="DNA sequence")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sequence": "ATGCGATCGATCGATCGATCG"
        }
    })


class PrimerDesignRequest(BaseModel):
    """Request for primer design"""
    sequence: str = Field(..., min_length=50, description="Template DNA sequence")
    target_start: int = Field(..., ge=0, description="Start of target region (0-indexed)")
    target_end: int = Field(..., ge=1, description="End of target region")
    min_length: int = Field(18, ge=15, le=30, description="Minimum primer length")
    max_length: int = Field(25, ge=15, le=35, description="Maximum primer length")
    min_tm: float = Field(55.0, ge=40, le=80, description="Minimum melting temperature")
    max_tm: float = Field(65.0, ge=40, le=80, description="Maximum melting temperature")
    min_gc: float = Field(40.0, ge=20, le=80, description="Minimum GC content (%)")
    max_gc: float = Field(60.0, ge=20, le=80, description="Maximum GC content (%)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sequence": "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
            "target_start": 30,
            "target_end": 70,
            "min_length": 18,
            "max_length": 25,
            "min_tm": 55,
            "max_tm": 65,
            "min_gc": 40,
            "max_gc": 60
        }
    })


class RestrictionRequest(BaseModel):
    """Request for restriction site analysis"""
    sequence: str = Field(..., min_length=1, description="DNA sequence")
    enzymes: Optional[List[str]] = Field(None, description="Specific enzymes (None = all)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sequence": "ATGCGAATTCGATCGGATCCATCGATCG",
            "enzymes": ["EcoRI", "BamHI"]
        }
    })


class TranslateRequest(BaseModel):
    """Request for DNA translation"""
    sequence: str = Field(..., min_length=3, description="DNA sequence")
    frame: int = Field(0, ge=0, le=2, description="Reading frame (0, 1, or 2)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sequence": "ATGGCTAGCTAGCTAGCTAG",
            "frame": 0
        }
    })


class TmRequest(BaseModel):
    """Request for Tm calculation"""
    sequence: str = Field(..., min_length=10, max_length=50, description="Primer sequence")
    method: str = Field("nearest_neighbor", description="Method: basic, wallace, nearest_neighbor")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sequence": "ATGCGATCGATCGATCGATCG",
            "method": "nearest_neighbor"
        }
    })


# ============================================
# ENDPOINTS
# ============================================

@router.post("/analyze")
async def analyze_sequence(request: SequenceInput):
    """
    Analyze DNA sequence composition
    
    Returns:
    - Length
    - GC content (%)
    - AT content (%)
    - Base composition (A, T, G, C, N counts)
    - Molecular weight (Da)
    """
    service = get_bioinformatics_service()
    
    try:
        stats = service.analyze_sequence(request.sequence)
        
        return {
            "success": True,
            "input_length": len(request.sequence),
            "cleaned_length": stats.length,
            **stats.to_dict()
        }
    except Exception as e:
        raise HTTPException(500, f"Sequence analysis failed: {str(e)}")


@router.post("/primers")
async def design_primers(request: PrimerDesignRequest):
    """
    Design PCR primers for a target region
    
    Evaluates primers based on:
    - Melting temperature (Tm)
    - GC content
    - Self-complementarity
    - Hairpin potential
    
    Returns top 5 forward and reverse primer candidates.
    """
    service = get_bioinformatics_service()
    
    try:
        if request.target_start >= request.target_end:
            raise HTTPException(400, "target_start must be less than target_end")
        
        if request.target_end > len(request.sequence):
            raise HTTPException(400, "target_end exceeds sequence length")
        
        primers = service.design_primers(
            sequence=request.sequence,
            target_start=request.target_start,
            target_end=request.target_end,
            primer_length=(request.min_length, request.max_length),
            tm_range=(request.min_tm, request.max_tm),
            gc_range=(request.min_gc, request.max_gc),
        )
        
        return {
            "success": True,
            "target_region": {
                "start": request.target_start,
                "end": request.target_end,
                "length": request.target_end - request.target_start,
            },
            "parameters": {
                "primer_length": [request.min_length, request.max_length],
                "tm_range": [request.min_tm, request.max_tm],
                "gc_range": [request.min_gc, request.max_gc],
            },
            "forward_primers": primers["forward"],
            "reverse_primers": primers["reverse"],
            "forward_count": len(primers["forward"]),
            "reverse_count": len(primers["reverse"]),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Primer design failed: {str(e)}")


@router.post("/restriction")
async def find_restriction_sites(request: RestrictionRequest):
    """
    Find restriction enzyme cut sites in DNA sequence
    
    Supports 15 common enzymes:
    EcoRI, BamHI, HindIII, XbaI, SalI, PstI, SmaI, KpnI, SacI,
    NotI, XhoI, NcoI, NdeI, BglII, ClaI
    
    Returns position, recognition sequence, cut site, and overhang type.
    """
    service = get_bioinformatics_service()
    
    try:
        sites = service.find_restriction_sites(
            sequence=request.sequence,
            enzymes=request.enzymes,
        )
        
        # Group by enzyme
        by_enzyme = {}
        for site in sites:
            enzyme = site.enzyme
            if enzyme not in by_enzyme:
                by_enzyme[enzyme] = []
            by_enzyme[enzyme].append(site.to_dict())
        
        return {
            "success": True,
            "sequence_length": len(service.clean_sequence(request.sequence)),
            "total_sites": len(sites),
            "enzymes_searched": request.enzymes or "all",
            "sites": [s.to_dict() for s in sites],
            "by_enzyme": by_enzyme,
        }
    except Exception as e:
        raise HTTPException(500, f"Restriction analysis failed: {str(e)}")


@router.post("/translate")
async def translate_dna(request: TranslateRequest):
    """
    Translate DNA sequence to protein
    
    Uses standard genetic code. Stop codons shown as '*'.
    
    Reading frames:
    - 0: Start from position 0
    - 1: Start from position 1
    - 2: Start from position 2
    """
    service = get_bioinformatics_service()
    
    try:
        protein = service.translate_sequence(
            sequence=request.sequence,
            frame=request.frame,
        )
        
        # Find ORFs (start to stop)
        orfs = []
        current_orf = ""
        in_orf = False
        
        for aa in protein:
            if aa == "M" and not in_orf:
                in_orf = True
                current_orf = "M"
            elif in_orf:
                if aa == "*":
                    if len(current_orf) >= 10:  # Min ORF length
                        orfs.append(current_orf)
                    in_orf = False
                    current_orf = ""
                else:
                    current_orf += aa
        
        return {
            "success": True,
            "dna_length": len(service.clean_sequence(request.sequence)),
            "frame": request.frame,
            "protein": protein,
            "protein_length": len(protein),
            "stop_codons": protein.count("*"),
            "orfs_found": len(orfs),
            "orfs": orfs[:5],  # Top 5 ORFs
        }
    except Exception as e:
        raise HTTPException(500, f"Translation failed: {str(e)}")


@router.post("/reverse-complement")
async def reverse_complement(request: SequenceInput):
    """
    Get reverse complement of DNA sequence
    
    Useful for:
    - Designing reverse primers
    - Finding complementary strand
    - Sequence orientation
    """
    service = get_bioinformatics_service()
    
    try:
        rev_comp = service.reverse_complement(request.sequence)
        cleaned = service.clean_sequence(request.sequence)
        
        return {
            "success": True,
            "original": cleaned,
            "reverse_complement": rev_comp,
            "length": len(rev_comp),
        }
    except Exception as e:
        raise HTTPException(500, f"Reverse complement failed: {str(e)}")


@router.post("/tm")
async def calculate_tm(request: TmRequest):
    """
    Calculate melting temperature (Tm) of primer
    
    Methods:
    - basic: 4°C × (G+C) + 2°C × (A+T) - for short oligos
    - wallace: 2(A+T) + 4(G+C)
    - nearest_neighbor: Thermodynamic calculation (most accurate)
    """
    service = get_bioinformatics_service()
    
    try:
        tm = service.calculate_tm(request.sequence, method=request.method)
        stats = service.analyze_sequence(request.sequence)
        
        return {
            "success": True,
            "sequence": service.clean_sequence(request.sequence),
            "length": stats.length,
            "tm": round(tm, 1),
            "method": request.method,
            "gc_content": round(stats.gc_content, 1),
        }
    except Exception as e:
        raise HTTPException(500, f"Tm calculation failed: {str(e)}")


@router.get("/enzymes")
async def list_enzymes():
    """List available restriction enzymes"""
    from app.services.bioinformatics import RESTRICTION_ENZYMES
    
    enzymes = []
    for name, info in RESTRICTION_ENZYMES.items():
        enzymes.append({
            "name": name,
            "recognition_sequence": info["seq"],
            "cut_position": info["cut"],
            "overhang": info["overhang"],
        })
    
    return {
        "count": len(enzymes),
        "enzymes": enzymes,
    }
