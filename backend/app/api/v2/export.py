"""
Data Export API for Plant Breeding
Export data in various formats (CSV, JSON, TSV)

Endpoints:
- POST /api/v2/export/trial - Export trial data
- POST /api/v2/export/phenotype-matrix - Export phenotype matrix
- POST /api/v2/export/pedigree - Export pedigree data
- POST /api/v2/export/markers - Export marker data
- POST /api/v2/export/field-book - Generate field book template
- POST /api/v2/export/custom - Custom data export
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, ConfigDict

from app.services.data_export import get_export_service
from app.api.deps import get_current_user

router = APIRouter(prefix="/export", tags=["Data Export"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class TrialExportRequest(BaseModel):
    """Request to export trial data"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "trial_id": "TRIAL-2025-001",
            "observations": [
                {"plot_id": "P001", "genotype": "G1", "block": 1, "trait": "yield", "value": 4.5, "date": "2025-10-15"},
                {"plot_id": "P002", "genotype": "G2", "block": 1, "trait": "yield", "value": 5.2, "date": "2025-10-15"}
            ],
            "format": "csv"
        }
    })

    trial_id: str = Field(..., description="Trial identifier")
    observations: List[Dict[str, Any]] = Field(..., description="Observation data")
    format: str = Field("csv", description="Export format: csv, tsv, json")


class PhenotypeMatrixRequest(BaseModel):
    """Request to export phenotype matrix"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": ["G1", "G2", "G3"],
            "traits": ["yield", "height", "days_to_flower"],
            "values": {
                "G1": {"yield": 4.5, "height": 95, "days_to_flower": 65},
                "G2": {"yield": 5.2, "height": 102, "days_to_flower": 62},
                "G3": {"yield": 4.1, "height": 88, "days_to_flower": 70}
            },
            "format": "csv"
        }
    })

    genotypes: List[str] = Field(..., description="List of genotype IDs")
    traits: List[str] = Field(..., description="List of trait names")
    values: Dict[str, Dict[str, Any]] = Field(..., description="Genotype -> Trait -> Value")
    format: str = Field("csv", description="Export format")


class PedigreeExportRequest(BaseModel):
    """Request to export pedigree data"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "pedigree": [
                {"id": "G1", "sire": "P1", "dam": "P2", "generation": 1, "inbreeding_coefficient": 0},
                {"id": "G2", "sire": "P1", "dam": "P3", "generation": 1, "inbreeding_coefficient": 0},
                {"id": "G3", "sire": "G1", "dam": "G2", "generation": 2, "inbreeding_coefficient": 0.125}
            ],
            "format": "csv"
        }
    })

    pedigree: List[Dict[str, Any]] = Field(..., description="Pedigree records")
    format: str = Field("csv", description="Export format")


class MarkerExportRequest(BaseModel):
    """Request to export marker data"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "genotypes": ["G1", "G2", "G3"],
            "markers": ["M1", "M2", "M3"],
            "calls": {
                "G1": {"M1": "AA", "M2": "AT", "M3": "GG"},
                "G2": {"M1": "AG", "M2": "TT", "M3": "GC"},
                "G3": {"M1": "GG", "M2": "AT", "M3": "CC"}
            },
            "format": "csv"
        }
    })

    genotypes: List[str] = Field(..., description="List of genotype IDs")
    markers: List[str] = Field(..., description="List of marker IDs")
    calls: Dict[str, Dict[str, str]] = Field(..., description="Genotype -> Marker -> Call")
    format: str = Field("csv", description="Export format")


class FieldBookRequest(BaseModel):
    """Request to generate field book"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "trial_id": "TRIAL-2025-001",
            "plots": [
                {"plot_id": "P001", "row": 1, "column": 1, "block": 1, "genotype": "G1"},
                {"plot_id": "P002", "row": 1, "column": 2, "block": 1, "genotype": "G2"}
            ],
            "traits": ["yield", "height", "days_to_flower"],
            "format": "csv"
        }
    })

    trial_id: str = Field(..., description="Trial identifier")
    plots: List[Dict[str, Any]] = Field(..., description="Plot layout")
    traits: List[str] = Field(..., description="Traits to collect")
    format: str = Field("csv", description="Export format")


class CustomExportRequest(BaseModel):
    """Request for custom data export"""
    data: List[Dict[str, Any]] = Field(..., description="Data to export")
    columns: Optional[List[str]] = Field(None, description="Column order (optional)")
    format: str = Field("csv", description="Export format")
    filename_prefix: str = Field("export", description="Filename prefix")


# ============================================
# ENDPOINTS
# ============================================

@router.post("/trial")
async def export_trial_data(request: TrialExportRequest):
    """
    Export trial observation data
    
    Exports plot-level observations with genotype, trait, and value columns.
    """
    service = get_export_service()
    
    try:
        result = service.export_trial_data(
            trial_id=request.trial_id,
            observations=request.observations,
            format=request.format,
        )
        
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.post("/phenotype-matrix")
async def export_phenotype_matrix(request: PhenotypeMatrixRequest):
    """
    Export phenotype data as genotype × trait matrix
    
    Creates a matrix with genotypes as rows and traits as columns.
    Useful for statistical analysis software.
    """
    service = get_export_service()
    
    try:
        result = service.export_phenotype_matrix(
            genotypes=request.genotypes,
            traits=request.traits,
            values=request.values,
            format=request.format,
        )
        
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.post("/pedigree")
async def export_pedigree(request: PedigreeExportRequest):
    """
    Export pedigree data
    
    Standard format: id, sire, dam, generation, inbreeding_coefficient
    Compatible with pedigree analysis software.
    """
    service = get_export_service()
    
    try:
        result = service.export_pedigree(
            pedigree_data=request.pedigree,
            format=request.format,
        )
        
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.post("/markers")
async def export_marker_data(request: MarkerExportRequest):
    """
    Export marker genotype data
    
    Creates a matrix with genotypes as rows and markers as columns.
    Compatible with genomic analysis software.
    """
    service = get_export_service()
    
    try:
        result = service.export_marker_data(
            genotypes=request.genotypes,
            markers=request.markers,
            calls=request.calls,
            format=request.format,
        )
        
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.post("/field-book")
async def generate_field_book(request: FieldBookRequest):
    """
    Generate field book template for data collection
    
    Creates a template with plot information and empty columns for traits.
    Can be printed or used in mobile data collection apps.
    """
    service = get_export_service()
    
    try:
        result = service.generate_field_book(
            trial_id=request.trial_id,
            plots=request.plots,
            traits=request.traits,
            format=request.format,
        )
        
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.post("/custom")
async def custom_export(request: CustomExportRequest):
    """
    Custom data export
    
    Export any data in CSV, TSV, or JSON format.
    """
    service = get_export_service()
    
    try:
        if request.format == "csv":
            content = service.export_to_csv(request.data, request.columns)
        elif request.format == "tsv":
            content = service.export_to_tsv(request.data, request.columns)
        else:
            content = service.export_to_json(request.data)
        
        from datetime import datetime
        filename = f"{request.filename_prefix}_{datetime.now().strftime('%Y%m%d')}.{request.format}"
        
        return {
            "success": True,
            "format": request.format,
            "row_count": len(request.data),
            "content": content,
            "filename": filename,
        }
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")


@router.get("/formats")
async def list_export_formats():
    """List available export formats"""
    return {
        "formats": [
            {
                "id": "csv",
                "name": "CSV",
                "description": "Comma-separated values",
                "mime_type": "text/csv",
                "extension": ".csv",
            },
            {
                "id": "tsv",
                "name": "TSV",
                "description": "Tab-separated values",
                "mime_type": "text/tab-separated-values",
                "extension": ".tsv",
            },
            {
                "id": "json",
                "name": "JSON",
                "description": "JavaScript Object Notation",
                "mime_type": "application/json",
                "extension": ".json",
            },
        ]
    }
