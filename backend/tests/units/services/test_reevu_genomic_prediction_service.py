"""Unit tests for the REEVU genomic prediction service."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from app.modules.ai.services.reevu.genomic_prediction_service import (
    GEBVEntry,
    GEBVResult,
    GRMResult,
    GenomicPredictionService,
)
from app.services.compute_engine import BLUPResult


class FakeCache:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.set_calls = 0
        self.get_calls = 0

    async def get(self, key: str):
        self.get_calls += 1
        return self.values.get(key)

    async def set(self, key: str, value: object, ttl_seconds: int = 0):
        self.set_calls += 1
        self.values[key] = value
        self.values[f"{key}:ttl"] = ttl_seconds
        return True


class FakeComputeEngine:
    def __init__(self) -> None:
        self.compute_grm_calls = 0
        self.compute_gblup_calls = 0

    def compute_grm(self, genotypes, method="vanraden1"):
        self.compute_grm_calls += 1
        return SimpleNamespace(
            matrix=np.eye(genotypes.shape[0]),
            method=method,
            n_individuals=genotypes.shape[0],
            n_markers=genotypes.shape[1],
        )

    def compute_gblup(self, *, genotypes, phenotypes, heritability):
        self.compute_gblup_calls += 1
        breeding_values = np.array([float(index) for index in range(len(phenotypes))])
        reliability = np.linspace(0.1, 0.9, len(phenotypes))
        return BLUPResult(
            fixed_effects=np.array([float(np.mean(phenotypes))]),
            breeding_values=breeding_values,
            reliability=reliability,
            accuracy=np.full(len(phenotypes), 0.2),
            genetic_variance=float(np.var(breeding_values)),
            error_variance=0.12,
            converged=True,
        )

    def compute_gblup_from_grm(self, *, phenotypes, grm, heritability):
        breeding_values = np.array([float(index) for index in range(len(phenotypes))])
        return BLUPResult(
            fixed_effects=np.array([float(np.mean(phenotypes))]),
            breeding_values=breeding_values,
            reliability=np.full(len(phenotypes), 0.7),
            accuracy=np.full(len(phenotypes), 0.8),
            genetic_variance=float(np.var(breeding_values)),
            error_variance=0.2,
            converged=True,
        )


def _genotype_matrix(n_individuals: int = 10, n_markers: int = 100) -> list[list[float]]:
    return [
        [float((individual + marker) % 3) for marker in range(n_markers)]
        for individual in range(n_individuals)
    ]


def test_data_models_and_constants_match_spec():
    entry = GEBVEntry(
        germplasm_id="G1",
        germplasm_name="Line A",
        gebv=1.2,
        reliability=0.8,
        rank=1,
    )
    grm = GRMResult(
        n_individuals=10,
        n_markers=100,
        matrix_available=True,
        cache_key="grm:1:x",
        matrix=[[1.0]],
    )
    result = GEBVResult(
        trait_name="Yield",
        method="GBLUP",
        gebvs=[entry],
        accuracy=0.8,
        n_individuals=10,
        n_markers=100,
    )

    assert GenomicPredictionService.MIN_INDIVIDUALS == 10
    assert GenomicPredictionService.MIN_MARKERS == 100
    assert result.gebvs == [entry]
    assert grm.matrix_available is True


@pytest.mark.asyncio
async def test_build_grm_caches_result_and_reuses_cache():
    cache = FakeCache()
    compute_engine = FakeComputeEngine()
    service = GenomicPredictionService(compute_engine=compute_engine, cache=cache)
    germplasm_ids = [f"G{index}" for index in range(10)]
    matrix = _genotype_matrix()

    first = await service._build_grm(
        db=SimpleNamespace(),
        organization_id=7,
        germplasm_ids=germplasm_ids,
        genotype_matrix=matrix,
    )
    second = await service._build_grm(
        db=SimpleNamespace(),
        organization_id=7,
        germplasm_ids=germplasm_ids,
        genotype_matrix=matrix,
    )

    assert first.matrix_available is True
    assert first.cache_hit is False
    assert second.matrix_available is True
    assert second.cache_hit is True
    assert second.matrix == first.matrix
    assert compute_engine.compute_grm_calls == 1
    assert cache.set_calls == 1
    assert cache.values[f"{first.cache_key}:ttl"] == service.GRM_CACHE_TTL_SECONDS


@pytest.mark.asyncio
async def test_build_grm_returns_insufficient_data_below_thresholds():
    service = GenomicPredictionService(compute_engine=FakeComputeEngine(), cache=FakeCache())

    result = await service._build_grm(
        db=SimpleNamespace(),
        organization_id=1,
        germplasm_ids=["G1", "G2"],
        genotype_matrix=[[0.0, 1.0, 2.0], [2.0, 1.0, 0.0]],
    )

    assert result.matrix_available is False
    assert result.n_individuals == 2
    assert result.n_markers == 3
    assert "requires at least 10 individuals and 100 markers" in result.reason


@pytest.mark.asyncio
async def test_compute_gebv_ranking_reliability_bounds_and_low_accuracy_warning():
    service = GenomicPredictionService(
        compute_engine=FakeComputeEngine(),
        cache=FakeCache(),
    )
    germplasm_ids = [f"G{index}" for index in range(10)]

    result = await service.compute_gebv(
        db=SimpleNamespace(),
        organization_id=1,
        trait_name="Yield",
        germplasm_ids=germplasm_ids,
        phenotype_values=[float(index) for index in range(10)],
        genotype_matrix=_genotype_matrix(),
        heritability=0.4,
    )

    assert result.insufficient_data is False
    assert result.n_individuals == 10
    assert result.n_markers == 100
    assert [entry.rank for entry in result.gebvs] == list(range(1, 11))
    assert [entry.gebv for entry in result.gebvs] == sorted(
        [entry.gebv for entry in result.gebvs],
        reverse=True,
    )
    assert all(
        entry.reliability is not None and 0.0 <= entry.reliability <= 1.0
        for entry in result.gebvs
    )
    assert result.accuracy == pytest.approx(0.2)
    assert "low_accuracy" in result.warnings
    assert result.evidence_refs
    assert result.calculation_steps


@pytest.mark.asyncio
async def test_compute_gebv_returns_safe_failure_for_insufficient_individuals():
    service = GenomicPredictionService(
        compute_engine=FakeComputeEngine(),
        cache=FakeCache(),
    )

    result = await service.compute_gebv(
        db=SimpleNamespace(),
        organization_id=1,
        trait_name="Yield",
        germplasm_ids=["G1", "G2"],
        phenotype_values=[1.0, 2.0],
        genotype_matrix=[[0.0, 1.0, 2.0], [2.0, 1.0, 0.0]],
    )

    assert result.insufficient_data is True
    assert result.n_individuals == 2
    assert result.n_markers == 3
    assert result.reason
    assert result.evidence_refs[0].source_type == "function"
