"""
Caching Configuration

Provides persistent disk-based caching for expensive computations (GBLUP, GWAS, PCA)
using joblib.Memory. This is optimized for large numpy arrays.
"""

import os
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Try importing joblib
try:
    from joblib import Memory
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    logger.warning("Joblib not found. Caching will be disabled.")

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache_data")

# Global memory instance
_memory = None

def get_memory_cache() -> Any:
    """
    Get or create the joblib Memory instance.
    """
    global _memory

    if not JOBLIB_AVAILABLE:
        # Return a dummy object with a cache method that does nothing
        class DummyMemory:
            def cache(self, func):
                return func
            def clear(self):
                pass
        return DummyMemory()

    if _memory is None:
        if not os.path.exists(CACHE_DIR):
            try:
                os.makedirs(CACHE_DIR)
            except OSError:
                logger.warning(f"Could not create cache dir {CACHE_DIR}. Caching disabled.")
                return DummyMemory()

        # verbose=0 to reduce log noise
        _memory = Memory(location=CACHE_DIR, verbose=0)

    return _memory

def cache_compute_result(func: Callable) -> Callable:
    """
    Decorator to cache function results using joblib.
    Use this for pure functions with large array inputs/outputs.
    """
    if not JOBLIB_AVAILABLE:
        return func

    memory = get_memory_cache()
    return memory.cache(func)

def clear_cache():
    """Clear the computation cache"""
    if _memory:
        _memory.clear()
