"""
Tests for Breeding Analytics Compute Interfaces
"""

import numpy as np
import pytest

from app.modules.breeding.compute.analytics import (
    GBLUPAnalyticsCompute,
    GxEAnalyticsCompute,
)
from app.services.task_queue import task_queue


@pytest.fixture
async def setup_task_queue():
    """Setup task queue for tests"""
    await task_queue.start()
    yield
    await task_queue.stop()


class TestGBLUPAnalyticsCompute:
    """Tests for GBLUP analytics compute interface"""

    @pytest.mark.asyncio
    async def test_solve_gblup_small_matrix(self, setup_task_queue):
        """Test GBLUP solver with small matrix (should use LIGHT_PYTHON)"""
        gblup_compute = GBLUPAnalyticsCompute()

        # Small dataset
        phenotypes = [10.0, 12.0, 11.0]
        g_matrix = [
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.4],
            [0.3, 0.4, 1.0],
        ]
        heritability = 0.5

        # Submit job
        job_id = await gblup_compute.solve_gblup(
            phenotypes=phenotypes,
            g_matrix=g_matrix,
            heritability=heritability,
            user_id="test_user",
        )

        assert job_id is not None

        # Get result
        result = await gblup_compute.get_result(job_id)

        assert result is not None
        assert "gebv" in result
        assert "reliability" in result
        assert "heritability" in result
        assert result["heritability"] == heritability

    @pytest.mark.asyncio
    async def test_solve_gblup_invalid_heritability(self, setup_task_queue):
        """Test GBLUP solver with invalid heritability"""
        gblup_compute = GBLUPAnalyticsCompute()

        phenotypes = [10.0, 12.0]
        g_matrix = [[1.0, 0.5], [0.5, 1.0]]
        heritability = 1.5  # Invalid

        job_id = await gblup_compute.solve_gblup(
            phenotypes=phenotypes,
            g_matrix=g_matrix,
            heritability=heritability,
        )

        result = await gblup_compute.get_result(job_id)

        assert result is not None
        assert result.get("error") is not None
        assert "Heritability must be in (0, 1]" in result["error"]

    @pytest.mark.asyncio
    async def test_solve_gblup_dimension_mismatch(self, setup_task_queue):
        """Test GBLUP solver with dimension mismatch"""
        gblup_compute = GBLUPAnalyticsCompute()

        phenotypes = [10.0, 12.0, 11.0]
        g_matrix = [[1.0, 0.5], [0.5, 1.0]]  # Wrong size
        heritability = 0.5

        job_id = await gblup_compute.solve_gblup(
            phenotypes=phenotypes,
            g_matrix=g_matrix,
            heritability=heritability,
        )

        result = await gblup_compute.get_result(job_id)

        assert result is not None
        assert result.get("error") is not None
        assert "dimension" in result["error"].lower()


class TestGxEAnalyticsCompute:
    """Tests for GxE analytics compute interface"""

    @pytest.mark.asyncio
    async def test_calculate_all_scores(self, setup_task_queue):
        """Test GxE stability scores calculation"""
        gxe_compute = GxEAnalyticsCompute()

        # Small yield matrix (3 genotypes x 4 environments)
        yield_matrix = np.array([
            [10.0, 12.0, 11.0, 13.0],
            [9.0, 11.0, 10.0, 12.0],
            [11.0, 13.0, 12.0, 14.0],
        ])
        genotype_names = ["G1", "G2", "G3"]
        environment_names = ["E1", "E2", "E3", "E4"]

        # Submit job
        job_id = await gxe_compute.calculate_all_scores(
            yield_matrix=yield_matrix,
            genotype_names=genotype_names,
            environment_names=environment_names,
            user_id="test_user",
        )

        assert job_id is not None

        # Get result
        result = await gxe_compute.get_result(job_id)

        assert result is not None
        assert "wricke_ecovalence" in result
        assert "shukla_stability" in result
        assert "lin_binns_superiority" in result
        assert "kang_rank_sum" in result
        assert "interaction_matrix" in result
        assert len(result["genotype_names"]) == 3
        assert len(result["environment_names"]) == 4

    @pytest.mark.asyncio
    async def test_calculate_interaction_matrix(self, setup_task_queue):
        """Test GxE interaction matrix calculation"""
        gxe_compute = GxEAnalyticsCompute()

        yield_matrix = np.array([
            [10.0, 12.0],
            [9.0, 11.0],
        ])

        job_id = await gxe_compute.calculate_interaction_matrix(
            yield_matrix=yield_matrix,
            user_id="test_user",
        )

        assert job_id is not None

        result = await gxe_compute.get_result(job_id)

        assert result is not None
        assert "interaction_matrix" in result
        assert "shape" in result
        assert result["shape"] == [2, 2]

    @pytest.mark.asyncio
    async def test_gxe_empty_matrix(self, setup_task_queue):
        """Test GxE with empty matrix"""
        gxe_compute = GxEAnalyticsCompute()

        yield_matrix = np.array([]).reshape(0, 0)
        genotype_names = []
        environment_names = []

        job_id = await gxe_compute.calculate_all_scores(
            yield_matrix=yield_matrix,
            genotype_names=genotype_names,
            environment_names=environment_names,
        )

        result = await gxe_compute.get_result(job_id)

        # Should handle gracefully
        assert result is not None
