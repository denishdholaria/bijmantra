
import pytest
import os
import shutil
import time
import numpy as np
from app.core.caching import get_memory_cache, CACHE_DIR
from app.services.compute_engine import compute_engine

# Top-level helper for multiprocessing
def heavy_dummy_compute(arr):
    """Simulate heavy compute"""
    return np.sum(arr ** 2)

class TestOptimization:
    
    @pytest.fixture(autouse=True)
    def clean_cache(self):
        """Clean cache before and after tests"""
        # Clear specific cache for this test? Or global?
        # Joblib memory.clear() clears everything under that memory location
        memory = get_memory_cache()
        memory.clear()
        yield
        # Cleanup
        memory.clear()

    def test_joblib_caching_mechanism(self):
        """Test if caching works (disk file creation)"""
        memory = get_memory_cache()
        
        # Define a cached function locally (joblib might complain if local?)
        # Joblib prefers top-level. But let's try decorating the helper.
        
        @memory.cache
        def cached_op(x):
            return x * x
            
        # 1. Call first time
        res1 = cached_op(10)
        assert res1 == 100
        
        # Check if cache dir has content
        # joblib creates a directory structure based on function name
        assert os.path.exists(CACHE_DIR)
        assert len(os.listdir(CACHE_DIR)) > 0
        
        # 2. Call second time (should be hit)
        start = time.time()
        res2 = cached_op(10)
        end = time.time()
        assert res2 == 100
        # Timing check is unreliable in CI/cloud, but logic check is good.
        
        # 3. Call with different arg (miss)
        res3 = cached_op(20)
        assert res3 == 400

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test ProcessPoolExecutor via run_async_task"""
        arr = np.array([1, 2, 3, 4, 5])
        
        # Run standard numpy function in pool
        # sum(arr^2) = 1+4+9+16+25 = 55
        
        # We use a top-level function that is importable/picklable
        # sum is built-in, but heavy_dummy_compute is defined above
        
        result = await compute_engine.run_async_task(heavy_dummy_compute, arr)
        
        assert result == 55
        
    def test_numpy_kernels_caching(self):
        """Verify that the refactored kernels in compute_engine are cached"""
        from app.services.compute_engine import compute_grm_numpy_kernel
        
        # Create dummy genotypes (10 ind, 100 markers)
        G = np.random.randint(0, 3, size=(10, 100))
        
        # 1. First call
        res1 = compute_grm_numpy_kernel(G, "vanraden1")
        
        # 2. Second call (same input)
        res2 = compute_grm_numpy_kernel(G, "vanraden1")
        
        np.testing.assert_array_equal(res1, res2)
        
        # Check cache directory again
        # The function `compute_grm_numpy_kernel` should have a folder in cache
        func_name = compute_grm_numpy_kernel.__name__ # might be decorated wrapper
        # Joblib uses the underlying name? 
        # Usually checking `joblib` folder
        found = False
        for root, dirs, files in os.walk(CACHE_DIR):
            for d in dirs:
                if "compute_grm_numpy_kernel" in d:
                    found = True
        
        # Might fail if joblib uses hash names, but usually it includes func name
        # If joblib is available, found should be True
        # If fallback dummy, found False
        
        try:
            import joblib
            assert found, "Cache directory for kernel not found"
        except ImportError:
            pass
