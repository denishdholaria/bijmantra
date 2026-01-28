"""
Quality Control API for Plant Breeding
Seed quality testing, sample analysis, and certification

Endpoints:
- POST /api/v2/quality/samples - Register sample
- GET /api/v2/quality/samples - List samples
- GET /api/v2/quality/samples/{id} - Get sample details
- POST /api/v2/quality/tests - Record test result
- POST /api/v2/quality/certificates - Issue certificate
- GET /api/v2/quality/standards - Get quality standards
- GET /api/v2/quality/summary - Get QC summary
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.services.quality_control import get_qc_service

router = APIRouter(prefix="/quality", tags=["Quality Control"])


# ============================================
# SCHEMAS
# ============================================

class SampleRegisterRequest(BaseModel):
    """Request to register a QC sample"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "lot_id": "LOT-000001",
            "variety": "IR64",
            "sample_date": "2025-01-15",
            "sample_weight": 500.0,
            "source": "Processing Plant A"
        }
    })

    lot_id: str = Field(..., description="Seed lot ID")
    variety: str = Field(..., description="Variety name")
    sample_date: str = Field(..., description="Sample date (YYYY-MM-DD)")
    sample_weight: float = Field(..., gt=0, description="Sample weight in grams")
    source: str = Field(..., description="Sample source/location")


class TestRecordRequest(BaseModel):
    """Request to record a test result"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sample_id": "QC-000001",
            "test_type": "germination",
            "result_value": 92.5,
            "tester": "Dr. Smith",
            "method": "Standard germination test (ISTA)",
            "seed_class": "certified",
            "notes": "Normal conditions"
        }
    })

    sample_id: str = Field(..., description="Sample ID")
    test_type: str = Field(..., description="Test type: purity, moisture, germination, vigor, health, genetic_purity")
    result_value: float = Field(..., description="Test result value")
    tester: str = Field(..., description="Person who conducted test")
    method: str = Field(..., description="Testing method used")
    seed_class: str = Field("certified", description="Seed class for standards")
    notes: str = Field("", description="Additional notes")


class CertificateRequest(BaseModel):
    """Request to issue certificate"""
    sample_id: str = Field(..., description="Sample ID")
    seed_class: str = Field(..., description="Seed class: foundation, certified, truthful")
    valid_months: int = Field(12, ge=1, le=24, description="Certificate validity in months")


# ============================================
# ENDPOINTS
# ============================================

@router.post("/samples")
async def register_sample(request: SampleRegisterRequest):
    """
    Register a sample for quality testing
    
    Creates a new QC sample record for tracking tests and certification.
    """
    service = get_qc_service()
    
    try:
        sample = service.register_sample(
            lot_id=request.lot_id,
            variety=request.variety,
            sample_date=request.sample_date,
            sample_weight=request.sample_weight,
            source=request.source,
        )
        
        return {
            "success": True,
            "message": f"Sample {sample.sample_id} registered",
            **sample.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register sample: {str(e)}")


@router.get("/samples")
async def list_samples(
    status: Optional[str] = Query(None, description="Filter by status: pending, passed, failed"),
    lot_id: Optional[str] = Query(None, description="Filter by lot ID")
):
    """List QC samples with optional filters"""
    service = get_qc_service()
    
    samples = service.list_samples(status=status, lot_id=lot_id)
    
    return {
        "success": True,
        "count": len(samples),
        "filters": {"status": status, "lot_id": lot_id},
        "samples": samples,
    }


@router.get("/samples/{sample_id}")
async def get_sample(sample_id: str):
    """
    Get sample details with all test results
    """
    service = get_qc_service()
    
    sample = service.get_sample(sample_id)
    if sample is None:
        raise HTTPException(404, f"Sample {sample_id} not found")
    
    return {
        "success": True,
        **sample,
    }


@router.post("/tests")
async def record_test(request: TestRecordRequest):
    """
    Record a quality test result
    
    Automatically checks result against standards for the seed class.
    Updates sample status based on all test results.
    """
    service = get_qc_service()
    
    try:
        test = service.record_test(
            sample_id=request.sample_id,
            test_type=request.test_type,
            result_value=request.result_value,
            tester=request.tester,
            method=request.method,
            seed_class=request.seed_class,
            notes=request.notes,
        )
        
        status = "PASSED ✓" if test.passed else "FAILED ✗"
        
        return {
            "success": True,
            "message": f"Test recorded: {status}",
            **test.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to record test: {str(e)}")


@router.post("/certificates")
async def issue_certificate(request: CertificateRequest):
    """
    Issue quality certificate for a sample
    
    Requirements:
    - All required tests for the seed class must be completed
    - All tests must have passed
    """
    service = get_qc_service()
    
    try:
        cert = service.issue_certificate(
            sample_id=request.sample_id,
            seed_class=request.seed_class,
            valid_months=request.valid_months,
        )
        
        return {
            "success": True,
            "message": f"Certificate {cert['certificate_id']} issued",
            **cert,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to issue certificate: {str(e)}")


@router.get("/standards")
async def get_standards(
    seed_class: str = Query("certified", description="Seed class: foundation, certified, truthful")
):
    """
    Get quality standards for a seed class
    
    Returns minimum and maximum acceptable values for each test type.
    """
    service = get_qc_service()
    
    standards = service.get_standards(seed_class)
    
    return {
        "success": True,
        **standards,
    }


@router.get("/summary")
async def get_qc_summary():
    """
    Get QC summary statistics
    
    Returns counts of samples, tests, pass rates, and certificates.
    """
    service = get_qc_service()
    
    summary = service.get_summary()
    
    return {
        "success": True,
        **summary,
    }


@router.get("/test-types")
async def list_test_types():
    """List available test types"""
    return {
        "test_types": [
            {
                "id": "purity",
                "name": "Physical Purity",
                "description": "Percentage of pure seed by weight",
                "unit": "%",
            },
            {
                "id": "moisture",
                "name": "Moisture Content",
                "description": "Seed moisture percentage",
                "unit": "%",
            },
            {
                "id": "germination",
                "name": "Germination",
                "description": "Percentage of seeds that germinate",
                "unit": "%",
            },
            {
                "id": "vigor",
                "name": "Seed Vigor",
                "description": "Seed vigor index",
                "unit": "index",
            },
            {
                "id": "health",
                "name": "Seed Health",
                "description": "Freedom from seed-borne diseases",
                "unit": "%",
            },
            {
                "id": "genetic_purity",
                "name": "Genetic Purity",
                "description": "Varietal purity from grow-out test",
                "unit": "%",
            },
        ]
    }


@router.get("/seed-classes")
async def list_seed_classes():
    """List seed certification classes"""
    return {
        "seed_classes": [
            {
                "id": "foundation",
                "name": "Foundation Seed",
                "description": "Highest purity class, source for certified seed",
                "tag_color": "white",
            },
            {
                "id": "certified",
                "name": "Certified Seed",
                "description": "Standard commercial seed class",
                "tag_color": "blue",
            },
            {
                "id": "truthful",
                "name": "Truthfully Labeled",
                "description": "Quality declared by producer",
                "tag_color": "green",
            },
            {
                "id": "research",
                "name": "Research Material",
                "description": "For research purposes only",
                "tag_color": "yellow",
            },
        ]
    }
