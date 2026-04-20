from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.middleware.tenant_context import get_tenant_db
from app.schemas.ld import (
    LDCalculateRequest,
    LDDecayRequest,
    LDDecayResponse,
    LDMatrixResponse,
    LDResult,
)
from app.modules.genomics.services.ld_analysis_service import ld_service


router = APIRouter(prefix="/ld", tags=["Linkage Disequilibrium"], dependencies=[Depends(get_current_user)])

LD_VARIANT_SET_REQUIRED_DETAIL = (
    "variant_set_id is required for LD analysis. Provide a real VariantSetDbId; synthetic fallback data is disabled."
)


def _require_variant_set_id(variant_set_id: str | None) -> str:
    if not variant_set_id:
        raise HTTPException(status_code=400, detail=LD_VARIANT_SET_REQUIRED_DETAIL)

    return variant_set_id

@router.post("/calculate", response_model=LDResult)
async def calculate_ld(
    request: LDCalculateRequest,
    db: AsyncSession = Depends(get_tenant_db)
):
    variant_set_id = _require_variant_set_id(request.variant_set_id)
    genotypes, marker_names, positions, n_samples = await ld_service.get_genotype_matrix(db, variant_set_id)

    if not genotypes or n_samples < 1 or len(marker_names) < 2:
        return LDResult(
            pairs=[],
            mean_r2=0,
            marker_count=len(marker_names),
            sample_count=n_samples,
        )

    pairs, matrix = ld_service.calculate_pairwise_ld(genotypes, positions, marker_names, window_size=request.window_size or 100)

    return LDResult(
        pairs=pairs,
        mean_r2=sum(p.r2 for p in pairs)/len(pairs) if pairs else 0,
        marker_count=len(marker_names),
        sample_count=n_samples
    )

@router.post("/decay", response_model=LDDecayResponse)
async def analyze_decay(
    request: LDDecayRequest,
    db: AsyncSession = Depends(get_tenant_db)
):
    variant_set_id = _require_variant_set_id(request.variant_set_id)
    genotypes, _, positions, n_samples = await ld_service.get_genotype_matrix(db, variant_set_id)

    if not genotypes or n_samples < 1 or len(positions) < 2:
        return LDDecayResponse(decay_curve=[])

    points = ld_service.calculate_decay(genotypes, positions, request.max_distance or 100000, request.bin_size or 1000)
    return LDDecayResponse(decay_curve=points)

@router.get("/matrix/{region}", response_model=LDMatrixResponse)
async def get_ld_matrix(
    region: str,
    variant_set_id: str | None = Query(None),
    population_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db)
):
    resolved_variant_set_id = _require_variant_set_id(variant_set_id)
    genotypes, marker_names, positions, n_samples = await ld_service.get_genotype_matrix(db, resolved_variant_set_id)
    if not genotypes or n_samples < 1 or len(marker_names) < 2:
        return LDMatrixResponse(markers=[], matrix=[], region=region)

    _, matrix = ld_service.calculate_pairwise_ld(genotypes, positions, marker_names, window_size=1000)
    return LDMatrixResponse(markers=marker_names, matrix=matrix, region=region)
