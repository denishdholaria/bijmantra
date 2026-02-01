"""
Trait Ontology API for Plant Breeding
Standardized trait definitions and measurement protocols

Endpoints:
- GET /api/v2/ontology/traits - List traits
- POST /api/v2/ontology/traits - Register trait
- GET /api/v2/ontology/traits/search - Search traits
- GET /api/v2/ontology/scales - List scales
- POST /api/v2/ontology/scales - Register scale
- GET /api/v2/ontology/methods - List methods
- POST /api/v2/ontology/methods - Register method
- GET /api/v2/ontology/variables - List variables
- POST /api/v2/ontology/variables - Create variable
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.services.trait_ontology import get_ontology_service

router = APIRouter(prefix="/ontology", tags=["Trait Ontology"])


# ============================================
# SCHEMAS
# ============================================

class TraitRegisterRequest(BaseModel):
    """Request to register a trait"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "trait_id": "T100",
            "name": "Leaf Area",
            "description": "Total leaf area per plant",
            "category": "morphological",
            "ontology_id": "CO_320:0000100",
            "synonyms": ["LA", "leaf size"]
        }
    })

    trait_id: str = Field(..., description="Unique trait ID")
    name: str = Field(..., description="Trait name")
    description: str = Field(..., description="Trait description")
    category: str = Field(..., description="Category: morphological, agronomic, physiological, biochemical, phenological, quality, stress, molecular")
    ontology_id: str = Field("", description="External ontology ID (e.g., CO_320:0000001)")
    synonyms: List[str] = Field([], description="Alternative names")


class ScaleRegisterRequest(BaseModel):
    """Request to register a scale"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "scale_id": "S100",
            "name": "Square centimeters",
            "scale_type": "numerical",
            "unit": "cm²",
            "min_value": 0,
            "max_value": 10000,
            "decimal_places": 1
        }
    })

    scale_id: str = Field(..., description="Unique scale ID")
    name: str = Field(..., description="Scale name")
    scale_type: str = Field(..., description="Type: nominal, ordinal, numerical, date, text")
    unit: str = Field("", description="Unit of measurement")
    min_value: Optional[float] = Field(None, description="Minimum value (for numerical)")
    max_value: Optional[float] = Field(None, description="Maximum value (for numerical)")
    categories: Optional[List[Dict[str, str]]] = Field(None, description="Categories (for nominal/ordinal)")
    decimal_places: int = Field(2, description="Decimal places (for numerical)")


class MethodRegisterRequest(BaseModel):
    """Request to register a method"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "method_id": "M100",
            "name": "Leaf area meter",
            "description": "Measure using LI-COR leaf area meter",
            "formula": "",
            "reference": "LI-COR LI-3100C"
        }
    })

    method_id: str = Field(..., description="Unique method ID")
    name: str = Field(..., description="Method name")
    description: str = Field(..., description="Method description")
    formula: str = Field("", description="Calculation formula (if applicable)")
    reference: str = Field("", description="Reference/citation")


class VariableCreateRequest(BaseModel):
    """Request to create a variable"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "variable_id": "V001",
            "name": "Plant Height (cm)",
            "trait_id": "T001",
            "method_id": "M001",
            "scale_id": "S001"
        }
    })

    variable_id: str = Field(..., description="Unique variable ID")
    name: str = Field(..., description="Variable name")
    trait_id: str = Field(..., description="Trait ID")
    method_id: str = Field(..., description="Method ID")
    scale_id: str = Field(..., description="Scale ID")


# ============================================
# ENDPOINTS
# ============================================

@router.get("/traits")
async def list_traits(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    List trait definitions
    
    Includes 15 common plant breeding traits by default.
    """
    service = get_ontology_service()
    
    traits = service.list_traits(category=category)
    
    return {
        "success": True,
        "count": len(traits),
        "category_filter": category,
        "traits": traits,
    }


@router.post("/traits")
async def register_trait(request: TraitRegisterRequest):
    """Register a new trait definition"""
    service = get_ontology_service()
    
    try:
        trait = service.register_trait(
            trait_id=request.trait_id,
            name=request.name,
            description=request.description,
            category=request.category,
            ontology_id=request.ontology_id,
            synonyms=request.synonyms,
        )
        
        return {
            "success": True,
            "message": f"Trait {request.trait_id} registered",
            **trait.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register trait: {str(e)}")


@router.get("/traits/search")
async def search_traits(
    q: str = Query(..., min_length=2, description="Search query")
):
    """Search traits by name or synonym"""
    service = get_ontology_service()
    
    results = service.search_traits(q)
    
    return {
        "success": True,
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/scales")
async def list_scales():
    """
    List measurement scales
    
    Includes common scales for plant breeding measurements.
    """
    service = get_ontology_service()
    
    scales = service.list_scales()
    
    return {
        "success": True,
        "count": len(scales),
        "scales": scales,
    }


@router.post("/scales")
async def register_scale(request: ScaleRegisterRequest):
    """Register a new measurement scale"""
    service = get_ontology_service()
    
    try:
        scale = service.register_scale(
            scale_id=request.scale_id,
            name=request.name,
            scale_type=request.scale_type,
            unit=request.unit,
            min_value=request.min_value,
            max_value=request.max_value,
            categories=request.categories,
            decimal_places=request.decimal_places,
        )
        
        return {
            "success": True,
            "message": f"Scale {request.scale_id} registered",
            **scale.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register scale: {str(e)}")


@router.get("/methods")
async def list_methods():
    """
    List measurement methods
    
    Includes common methods for plant breeding observations.
    """
    service = get_ontology_service()
    
    methods = service.list_methods()
    
    return {
        "success": True,
        "count": len(methods),
        "methods": methods,
    }


@router.post("/methods")
async def register_method(request: MethodRegisterRequest):
    """Register a new measurement method"""
    service = get_ontology_service()
    
    try:
        method = service.register_method(
            method_id=request.method_id,
            name=request.name,
            description=request.description,
            formula=request.formula,
            reference=request.reference,
        )
        
        return {
            "success": True,
            "message": f"Method {request.method_id} registered",
            **method.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register method: {str(e)}")


@router.get("/variables")
async def list_variables():
    """
    List observation variables
    
    Variables combine trait + method + scale for standardized observations.
    """
    service = get_ontology_service()
    
    variables = service.list_variables()
    
    return {
        "success": True,
        "count": len(variables),
        "variables": variables,
    }


@router.post("/variables")
async def create_variable(request: VariableCreateRequest):
    """
    Create an observation variable
    
    Combines a trait, method, and scale into a standardized variable.
    """
    service = get_ontology_service()
    
    try:
        variable = service.create_variable(
            variable_id=request.variable_id,
            name=request.name,
            trait_id=request.trait_id,
            method_id=request.method_id,
            scale_id=request.scale_id,
        )
        
        return {
            "success": True,
            "message": f"Variable {request.variable_id} created",
            **variable.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to create variable: {str(e)}")


@router.get("/categories")
async def list_categories():
    """List trait categories"""
    return {
        "categories": [
            {"id": "morphological", "name": "Morphological", "description": "Plant structure and form"},
            {"id": "agronomic", "name": "Agronomic", "description": "Yield and production traits"},
            {"id": "physiological", "name": "Physiological", "description": "Plant function and processes"},
            {"id": "biochemical", "name": "Biochemical", "description": "Chemical composition"},
            {"id": "phenological", "name": "Phenological", "description": "Growth stages and timing"},
            {"id": "quality", "name": "Quality", "description": "Grain/product quality"},
            {"id": "stress", "name": "Stress", "description": "Biotic and abiotic stress response"},
            {"id": "molecular", "name": "Molecular", "description": "Molecular markers and genes"},
        ]
    }


@router.get("/scale-types")
async def list_scale_types():
    """List scale types"""
    return {
        "scale_types": [
            {"id": "nominal", "name": "Nominal", "description": "Categories without order (e.g., color)"},
            {"id": "ordinal", "name": "Ordinal", "description": "Ordered categories (e.g., 1-9 scale)"},
            {"id": "numerical", "name": "Numerical", "description": "Continuous values (e.g., height in cm)"},
            {"id": "date", "name": "Date", "description": "Date values"},
            {"id": "text", "name": "Text", "description": "Free text observations"},
        ]
    }
