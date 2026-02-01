from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import random

from app.middleware.tenant_context import get_tenant_db
from app.services.ld_analysis import ld_service
from app.schemas.ld import (
    LDCalculateRequest, LDResult, LDMatrixRequest, LDMatrixResponse,
    LDDecayRequest, LDDecayResponse
)

router = APIRouter(prefix="/ld", tags=["Linkage Disequilibrium"])

@router.post("/calculate", response_model=LDResult)
async def calculate_ld(
    request: LDCalculateRequest,
    db: AsyncSession = Depends(get_tenant_db)
):
    genotypes = []
    positions = []
    marker_names = []
    n_samples = 0

    if request.variant_set_id:
        genotypes, marker_names, positions, n_samples = await ld_service.get_genotype_matrix(db, request.variant_set_id)
        if not genotypes:
             return LDResult(pairs=[], mean_r2=0, marker_count=0, sample_count=0)
    else:
        # Mock data simulation
        n_markers = 50
        n_samples = 200
        n_samples = n_samples # Correct variable

        # Initialize first marker
        g0 = [random.randint(0, 2) for _ in range(n_samples)]
        genotypes.append(g0)
        positions.append(0)
        marker_names.append("M0")

        # Generate correlated markers
        for i in range(1, n_markers):
            prev = genotypes[-1]
            curr = []
            positions.append(i * 1000)
            marker_names.append(f"M{i}")
            # Decay LD with distance index (just for simulation visual)
            ld_strength = max(0.0, 0.9 - (i % 10) * 0.1)

            for j in range(n_samples):
                if random.random() < ld_strength:
                    curr.append(prev[j])
                else:
                    curr.append(random.randint(0, 2))
            genotypes.append(curr)

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
    genotypes = []
    positions = []

    if request.variant_set_id:
        genotypes, _, positions, _ = await ld_service.get_genotype_matrix(db, request.variant_set_id)
    else:
        # Mock data
        n_markers = 100
        n_samples = 100
        g0 = [random.randint(0, 2) for _ in range(n_samples)]
        genotypes.append(g0)
        positions.append(0)

        for i in range(1, n_markers):
            pos = i * 1000
            positions.append(pos)
            prev = genotypes[-1]
            curr = []

            # Simple simulation: correlation drops with index distance
            for j in range(n_samples):
                if random.random() < 0.7:
                     curr.append(prev[j])
                else:
                     curr.append(random.randint(0, 2))
            genotypes.append(curr)

    points = ld_service.calculate_decay(genotypes, positions, request.max_distance or 100000, request.bin_size or 1000)
    return LDDecayResponse(decay_curve=points)

@router.get("/matrix/{region}", response_model=LDMatrixResponse)
async def get_ld_matrix(
    region: str,
    variant_set_id: Optional[str] = Query(None),
    population_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_tenant_db)
):
    if variant_set_id:
        genotypes, marker_names, positions, _ = await ld_service.get_genotype_matrix(db, variant_set_id)
        if not genotypes:
             return LDMatrixResponse(markers=[], matrix=[], region=region)

        _, matrix = ld_service.calculate_pairwise_ld(genotypes, positions, marker_names, window_size=1000) # Full matrix? might be big
        # If matrix is huge, we should return heatmap data or limit it.
        # For now return as is.
        return LDMatrixResponse(markers=marker_names, matrix=matrix, region=region)

    else:
        # Mock
        n_markers = 20
        markers = [f"M{i}" for i in range(n_markers)]
        matrix = [[random.random() for _ in range(n_markers)] for _ in range(n_markers)]

        for i in range(n_markers):
            matrix[i][i] = 1.0
            for j in range(i+1, n_markers):
                matrix[j][i] = matrix[i][j]

        return LDMatrixResponse(markers=markers, matrix=matrix, region=region)
