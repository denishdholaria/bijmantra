"""
Phenotype Comparison API
Compare phenotypic data across germplasm entries
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import random

router = APIRouter(prefix="/phenotype-comparison", tags=["Phenotype Comparison"])


class GermplasmEntry(BaseModel):
    """Germplasm entry for comparison"""
    germplasm_db_id: str
    germplasm_name: str
    default_display_name: Optional[str] = None
    species: Optional[str] = None
    is_check: bool = False


class TraitValue(BaseModel):
    """Trait value for a germplasm"""
    trait_id: str
    trait_name: str
    value: float
    unit: str


class ComparisonResult(BaseModel):
    """Comparison result"""
    germplasm_id: str
    germplasm_name: str
    traits: Dict[str, float]
    vs_check: Optional[Dict[str, float]] = None


@router.get("/germplasm")
async def get_germplasm_for_comparison(
    limit: int = Query(default=20, le=100),
    search: Optional[str] = None,
    species: Optional[str] = None,
):
    """
    Get germplasm entries available for comparison
    """
    # Demo germplasm data
    germplasm_list = [
        {"germplasmDbId": "G001", "germplasmName": "Elite Variety 2024", "defaultDisplayName": "Elite-2024", "species": "Oryza sativa"},
        {"germplasmDbId": "G002", "germplasmName": "High Yield Line A", "defaultDisplayName": "HYL-A", "species": "Oryza sativa"},
        {"germplasmDbId": "G003", "germplasmName": "Disease Resistant B", "defaultDisplayName": "DR-B", "species": "Oryza sativa"},
        {"germplasmDbId": "G004", "germplasmName": "Drought Tolerant C", "defaultDisplayName": "DT-C", "species": "Oryza sativa"},
        {"germplasmDbId": "G005", "germplasmName": "Check Variety", "defaultDisplayName": "Check", "species": "Oryza sativa", "isCheck": True},
        {"germplasmDbId": "G006", "germplasmName": "Premium Line D", "defaultDisplayName": "PL-D", "species": "Oryza sativa"},
        {"germplasmDbId": "G007", "germplasmName": "Aromatic Rice E", "defaultDisplayName": "AR-E", "species": "Oryza sativa"},
        {"germplasmDbId": "G008", "germplasmName": "Short Duration F", "defaultDisplayName": "SD-F", "species": "Oryza sativa"},
    ]
    
    # Filter by search
    if search:
        search_lower = search.lower()
        germplasm_list = [g for g in germplasm_list if search_lower in g["germplasmName"].lower()]
    
    return {
        "result": {
            "data": germplasm_list[:limit]
        },
        "metadata": {
            "pagination": {
                "currentPage": 0,
                "pageSize": limit,
                "totalCount": len(germplasm_list),
                "totalPages": 1,
            }
        }
    }


@router.post("/observations")
async def get_observations_for_germplasm(
    germplasm_ids: List[str],
    traits: Optional[List[str]] = None,
):
    """
    Get observations for selected germplasm entries
    """
    # Demo trait data for each germplasm
    trait_data = {
        "G001": {"yield": 5.2, "height": 95, "maturity": 120, "protein": 12.5, "disease": 8},
        "G002": {"yield": 5.8, "height": 105, "maturity": 125, "protein": 11.2, "disease": 6},
        "G003": {"yield": 4.5, "height": 90, "maturity": 115, "protein": 13.1, "disease": 9},
        "G004": {"yield": 4.2, "height": 85, "maturity": 110, "protein": 12.8, "disease": 7},
        "G005": {"yield": 4.8, "height": 100, "maturity": 118, "protein": 11.8, "disease": 5},
        "G006": {"yield": 5.0, "height": 98, "maturity": 122, "protein": 12.0, "disease": 7},
        "G007": {"yield": 4.3, "height": 92, "maturity": 130, "protein": 14.2, "disease": 6},
        "G008": {"yield": 4.9, "height": 88, "maturity": 105, "protein": 11.5, "disease": 8},
    }
    
    trait_info = {
        "yield": {"name": "Grain Yield", "unit": "t/ha"},
        "height": {"name": "Plant Height", "unit": "cm"},
        "maturity": {"name": "Days to Maturity", "unit": "days"},
        "protein": {"name": "Protein Content", "unit": "%"},
        "disease": {"name": "Disease Resistance", "unit": "score 1-9"},
    }
    
    observations = []
    for germ_id in germplasm_ids:
        if germ_id in trait_data:
            for trait_key, value in trait_data[germ_id].items():
                if traits is None or trait_key in traits:
                    observations.append({
                        "observationDbId": f"obs-{germ_id}-{trait_key}",
                        "germplasmDbId": germ_id,
                        "observationVariableName": trait_info[trait_key]["name"],
                        "observationVariableDbId": f"var-{trait_key}",
                        "value": str(value),
                        "observationTimeStamp": "2024-12-01T00:00:00Z",
                    })
    
    return {
        "result": {
            "data": observations
        },
        "metadata": {
            "pagination": {
                "currentPage": 0,
                "pageSize": len(observations),
                "totalCount": len(observations),
                "totalPages": 1,
            }
        }
    }


@router.get("/traits")
async def get_comparison_traits():
    """
    Get available traits for comparison
    """
    return {
        "data": [
            {"id": "yield", "name": "Grain Yield", "unit": "t/ha", "higher_is_better": True},
            {"id": "height", "name": "Plant Height", "unit": "cm", "higher_is_better": False},
            {"id": "maturity", "name": "Days to Maturity", "unit": "days", "higher_is_better": False},
            {"id": "protein", "name": "Protein Content", "unit": "%", "higher_is_better": True},
            {"id": "disease", "name": "Disease Resistance", "unit": "score 1-9", "higher_is_better": True},
        ]
    }


@router.post("/compare")
async def compare_germplasm(
    germplasm_ids: List[str],
    check_id: Optional[str] = "G005",
):
    """
    Compare germplasm entries against a check variety
    """
    # Demo trait data
    trait_data = {
        "G001": {"yield": 5.2, "height": 95, "maturity": 120, "protein": 12.5, "disease": 8},
        "G002": {"yield": 5.8, "height": 105, "maturity": 125, "protein": 11.2, "disease": 6},
        "G003": {"yield": 4.5, "height": 90, "maturity": 115, "protein": 13.1, "disease": 9},
        "G004": {"yield": 4.2, "height": 85, "maturity": 110, "protein": 12.8, "disease": 7},
        "G005": {"yield": 4.8, "height": 100, "maturity": 118, "protein": 11.8, "disease": 5},
        "G006": {"yield": 5.0, "height": 98, "maturity": 122, "protein": 12.0, "disease": 7},
        "G007": {"yield": 4.3, "height": 92, "maturity": 130, "protein": 14.2, "disease": 6},
        "G008": {"yield": 4.9, "height": 88, "maturity": 105, "protein": 11.5, "disease": 8},
    }
    
    germplasm_names = {
        "G001": "Elite Variety 2024",
        "G002": "High Yield Line A",
        "G003": "Disease Resistant B",
        "G004": "Drought Tolerant C",
        "G005": "Check Variety",
        "G006": "Premium Line D",
        "G007": "Aromatic Rice E",
        "G008": "Short Duration F",
    }
    
    check_traits = trait_data.get(check_id, {})
    
    results = []
    for germ_id in germplasm_ids:
        if germ_id in trait_data:
            traits = trait_data[germ_id]
            vs_check = {}
            
            if check_traits and germ_id != check_id:
                for trait, value in traits.items():
                    check_value = check_traits.get(trait, 0)
                    if check_value > 0:
                        vs_check[trait] = round(((value - check_value) / check_value) * 100, 1)
            
            results.append({
                "germplasm_id": germ_id,
                "germplasm_name": germplasm_names.get(germ_id, germ_id),
                "traits": traits,
                "vs_check": vs_check if vs_check else None,
            })
    
    return {
        "data": results,
        "check_id": check_id,
        "check_name": germplasm_names.get(check_id, check_id),
    }


@router.get("/statistics")
async def get_comparison_statistics(
    germplasm_ids: Optional[str] = None,
):
    """
    Get summary statistics for comparison
    """
    return {
        "total_germplasm": 8,
        "total_traits": 5,
        "trait_summary": {
            "yield": {"min": 4.2, "max": 5.8, "mean": 4.84, "std": 0.48},
            "height": {"min": 85, "max": 105, "mean": 94.1, "std": 6.2},
            "maturity": {"min": 105, "max": 130, "mean": 118.1, "std": 7.8},
            "protein": {"min": 11.2, "max": 14.2, "mean": 12.4, "std": 0.9},
            "disease": {"min": 5, "max": 9, "mean": 7.0, "std": 1.3},
        },
    }
