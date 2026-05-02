"""
Verify compute wrapper structure without running
"""

import inspect


def verify_compute_interface():
    """Verify compute interfaces are properly structured"""
    
    print("=" * 60)
    print("Verifying Compute Interface Structure")
    print("=" * 60)
    
    # Check breeding analytics compute
    print("\n1. Breeding Analytics Compute:")
    try:
        from app.modules.breeding.compute.analytics import (
            GBLUPAnalyticsCompute,
            GxEAnalyticsCompute,
        )
        
        gblup = GBLUPAnalyticsCompute()
        print(f"   ✓ GBLUPAnalyticsCompute imported")
        print(f"     - Domain: {gblup.domain_name}")
        print(f"     - Methods: {[m for m in dir(gblup) if not m.startswith('_') and callable(getattr(gblup, m))]}")
        
        gxe = GxEAnalyticsCompute()
        print(f"   ✓ GxEAnalyticsCompute imported")
        print(f"     - Domain: {gxe.domain_name}")
        print(f"     - Methods: {[m for m in dir(gxe) if not m.startswith('_') and callable(getattr(gxe, m))]}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Check genomics statistics compute
    print("\n2. Genomics Statistics Compute:")
    try:
        from app.modules.genomics.compute.statistics import (
            KinshipCompute,
            GWASPlinkCompute,
        )
        
        kinship = KinshipCompute()
        print(f"   ✓ KinshipCompute imported")
        print(f"     - Domain: {kinship.domain_name}")
        print(f"     - Methods: {[m for m in dir(kinship) if not m.startswith('_') and callable(getattr(kinship, m))]}")
        
        plink = GWASPlinkCompute()
        print(f"   ✓ GWASPlinkCompute imported")
        print(f"     - Domain: {plink.domain_name}")
        print(f"     - Methods: {[m for m in dir(plink) if not m.startswith('_') and callable(getattr(plink, m))]}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Check base interface
    print("\n3. Base Compute Interface:")
    try:
        from app.services.compute_interface import BaseComputeInterface
        
        methods = [m for m in dir(BaseComputeInterface) if not m.startswith('_') and callable(getattr(BaseComputeInterface, m))]
        print(f"   ✓ BaseComputeInterface imported")
        print(f"     - Methods: {methods}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Verify timeout and error handling
    print("\n4. Timeout and Error Handling:")
    try:
        from app.modules.breeding.compute.analytics.gblup_analytics_compute import GBLUPAnalyticsCompute
        
        # Check worker method has timeout handling
        source = inspect.getsource(GBLUPAnalyticsCompute._gblup_worker)
        
        has_timeout = "asyncio.wait_for" in source
        has_timeout_error = "asyncio.TimeoutError" in source
        has_error_handling = "except Exception" in source
        
        print(f"   ✓ Timeout handling: {has_timeout}")
        print(f"   ✓ Timeout error handling: {has_timeout_error}")
        print(f"   ✓ General error handling: {has_error_handling}")
        
        if not (has_timeout and has_timeout_error and has_error_handling):
            print("   ✗ Missing timeout or error handling")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Verify async execution for operations > 30s
    print("\n5. Async Execution Configuration:")
    try:
        from app.modules.breeding.compute.analytics.gblup_analytics_compute import GBLUPAnalyticsCompute
        
        source = inspect.getsource(GBLUPAnalyticsCompute._gblup_worker)
        
        # Check for timeout configuration based on size
        has_conditional_timeout = "timeout = 300 if" in source or "timeout = 30" in source
        has_asyncio_to_thread = "asyncio.to_thread" in source
        
        print(f"   ✓ Conditional timeout (>30s for large ops): {has_conditional_timeout}")
        print(f"   ✓ Async thread execution: {has_asyncio_to_thread}")
        
        if not (has_conditional_timeout and has_asyncio_to_thread):
            print("   ✗ Missing async execution configuration")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All compute wrappers properly structured!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = verify_compute_interface()
    exit(0 if success else 1)
