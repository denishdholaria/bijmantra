"""
Haplotype Analysis API

Endpoints for haplotype-based breeding analysis.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.services.haplotype_analysis import haplotype_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user


router = APIRouter(prefix="/haplotype", tags=["Haplotype Analysis"])


@router.get("/blocks", summary="List haplotype blocks")
async def list_blocks(
    chromosome: Optional[str] = Query(None, description="Filter by chromosome"),
    min_length: Optional[int] = Query(None, description="Minimum block length in kb"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get list of haplotype blocks
    
    Returns blocks with their properties including diversity and marker count.
    """
    blocks =  await haplotype_service.get_blocks(db, current_user.organization_id, chromosome=chromosome, min_length=min_length)
    return {
        "success": True,
        "count": len(blocks),
        "blocks": blocks,
    }


@router.get("/blocks/{block_id}", summary="Get haplotype block")
async def get_block(
    block_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get details of a specific haplotype block
    
    Returns block info with all haplotypes.
    """
    block =  await haplotype_service.get_block(db, current_user.organization_id, block_id)
    if not block:
        raise HTTPException(404, f"Block {block_id} not found")

    return {
        "success": True,
        "data": block,
    }


@router.get("/blocks/{block_id}/haplotypes", summary="Get block haplotypes")
async def get_block_haplotypes(
    block_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get haplotypes for a specific block
    
    Returns all haplotypes with frequencies and associations.
    """
    haplotypes =  await haplotype_service.get_haplotypes(db, current_user.organization_id, block_id)
    return {
        "success": True,
        "block_id": block_id,
        "count": len(haplotypes),
        "haplotypes": haplotypes,
    }


@router.get("/associations", summary="Get haplotype-trait associations")
async def get_associations(
    trait: Optional[str] = Query(None, description="Filter by trait name"),
    chromosome: Optional[str] = Query(None, description="Filter by chromosome"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get haplotype-trait associations
    
    Returns significant associations with effect sizes and p-values.
    """
    associations =  await haplotype_service.get_associations(db, current_user.organization_id, trait=trait, chromosome=chromosome)
    return {
        "success": True,
        "count": len(associations),
        "associations": associations,
    }


@router.get("/favorable", summary="Get favorable haplotypes")
async def get_favorable_haplotypes(
    trait: Optional[str] = Query(None, description="Filter by trait"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get favorable haplotypes for breeding
    
    Returns haplotypes associated with positive trait effects.
    """
    favorable =  await haplotype_service.get_favorable_haplotypes(db, current_user.organization_id, trait=trait)
    return {
        "success": True,
        "count": len(favorable),
        "favorable_haplotypes": favorable,
    }


@router.get("/diversity", summary="Get diversity summary")
async def get_diversity_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get haplotype diversity summary
    
    Returns diversity statistics across all blocks.
    """
    summary =  await haplotype_service.get_diversity_summary(db, current_user.organization_id)
    return {
        "success": True,
        "data": summary,
    }


@router.get("/statistics", summary="Get statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get overall haplotype analysis statistics
    """
    stats =  await haplotype_service.get_statistics(db, current_user.organization_id)
    return {
        "success": True,
        "data": stats,
    }


@router.get("/traits", summary="Get analyzed traits")
async def get_traits(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get list of traits with haplotype associations
    """
    associations =  await haplotype_service.get_associations(db, current_user.organization_id)
    traits = {}

    for assoc in associations:
        trait = assoc["trait"]
        if trait not in traits:
            traits[trait] = {
                "trait": trait,
                "n_associations": 0,
                "top_effect": 0,
                "min_pvalue": 1,
            }
        traits[trait]["n_associations"] += 1
        traits[trait]["top_effect"] = max(traits[trait]["top_effect"], assoc["effect_size"])
        traits[trait]["min_pvalue"] = min(traits[trait]["min_pvalue"], assoc["p_value"])

    return {
        "success": True,
        "count": len(traits),
        "traits": list(traits.values()),
    }
