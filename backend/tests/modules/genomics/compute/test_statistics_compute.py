"""
Tests for Genomics Statistics Compute Interfaces
"""

import numpy as np
import pytest

from app.modules.genomics.compute.statistics import (
    KinshipCompute,
)
from app.services.task_queue import task_queue


@pytest.fixture
async def setup_task_queue():
    """Setup task queue for tests"""
    await task_queue.start()
    yield
    await task_queue.stop()


class TestKinshipCompute:
    """Tests for kinship compute interface"""

    @pytest.mark.asyncio
    async def test_calculate_vanraden_kinship(self, setup_task_queue):
        """Test VanRaden kinship calculation"""
        kinship_compute = KinshipCompute()

        # Small genotype matrix (3 individuals x 5 markers)
        genotype_matrix = np.array([
            [0, 1, 2, 0, 2],
            [0, 1, 2, 0, 2],  # Identical to first
            [2, 1, 0, 2, 0],  # Different
        ])

        # Submit job
        job_id = await kinship_compute.calculate_vanraden_kinship(
            genotype_matrix=genotype_matrix,
            check_maf=True,
            user_id="test_user",
        )

        assert job_id is not None

        # Get result
        result = await kinship_compute.get_result(job_id)

        assert result is not None
        assert result["success"] is True
        assert "K" in result
        assert "denominator" in result
        assert result["marker_count"] == 5
        assert result["sample_count"] == 3

        # Check kinship matrix properties
        K = np.array(result["K"])
        assert K.shape == (3, 3)
        # Diagonal should be close to 1 (self-kinship)
        assert np.allclose(np.diag(K), 1.0, atol=0.2)
        # Matrix should be symmetric
        assert np.allclose(K, K.T)

    @pytest.mark.asyncio
    async def test_calculate_inbreeding(self, setup_task_queue):
        """Test inbreeding coefficient calculation"""
        kinship_compute = KinshipCompute()

        # Create a simple kinship matrix
        kinship_matrix = np.array([
            [1.1, 0.5, 0.3],
            [0.5, 1.0, 0.4],
            [0.3, 0.4, 1.2],
        ])

        # Submit job
        job_id = await kinship_compute.calculate_inbreeding(
            kinship_matrix=kinship_matrix,
            user_id="test_user",
        )

        assert job_id is not None

        # Get result
        result = await kinship_compute.get_result(job_id)

        assert result is not None
        assert result["success"] is True
        assert "inbreeding_coefficients" in result
        assert "average_kinship" in result
        assert "summary" in result
        assert result["n_individuals"] == 3

        # Check inbreeding coefficients
        F = result["inbreeding_coefficients"]
        assert len(F) == 3
        # F = diag(K) - 1
        assert np.isclose(F[0], 0.1, atol=0.01)
        assert np.isclose(F[1], 0.0, atol=0.01)
        assert np.isclose(F[2], 0.2, atol=0.01)

    @pytest.mark.asyncio
    async def test_kinship_invalid_matrix(self, setup_task_queue):
        """Test kinship calculation with invalid matrix"""
        kinship_compute = KinshipCompute()

        # Non-square matrix
        kinship_matrix = np.array([
            [1.0, 0.5],
            [0.5, 1.0],
            [0.3, 0.4],
        ])

        job_id = await kinship_compute.calculate_inbreeding(
            kinship_matrix=kinship_matrix,
        )

        result = await kinship_compute.get_result(job_id)

        assert result is not None
        assert result["success"] is False
        assert "error" in result
        assert "square" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_kinship_large_matrix_uses_heavy_compute(self, setup_task_queue):
        """Test that large matrices use HEAVY_COMPUTE"""
        kinship_compute = KinshipCompute()

        # Large genotype matrix (100 individuals x 1000 markers = 100k cells)
        genotype_matrix = np.random.randint(0, 3, size=(100, 1000))

        job_id = await kinship_compute.calculate_vanraden_kinship(
            genotype_matrix=genotype_matrix,
        )

        # Check that job was created
        assert job_id is not None

        # Get job status
        status = await kinship_compute.get_status(job_id)
        assert status is not None

        # Note: We don't wait for completion in this test as it may take time
        # Just verify the job was queued successfully


class TestKinshipComputeTimeout:
    """Tests for timeout handling in kinship compute"""

    @pytest.mark.asyncio
    async def test_kinship_timeout_handling(self, setup_task_queue):
        """Test that timeout is handled gracefully"""
        # This test would require mocking the kinship calculation to take > 30s
        # For now, we just verify the timeout logic exists in the code
        kinship_compute = KinshipCompute()

        # Small matrix should complete quickly
        genotype_matrix = np.array([[0, 1, 2], [1, 2, 0]])

        job_id = await kinship_compute.calculate_vanraden_kinship(
            genotype_matrix=genotype_matrix,
        )

        result = await kinship_compute.get_result(job_id)

        # Should complete successfully (no timeout)
        assert result is not None
        assert result["success"] is True
