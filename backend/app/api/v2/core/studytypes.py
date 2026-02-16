"""
BrAPI Core - Study Types endpoint
GET /studytypes - Returns list of study types
"""

from typing import List
from fastapi import APIRouter, Query

router = APIRouter()

# Standard study types in plant breeding
STUDY_TYPES = [
    "Phenotyping Study",
    "Genotyping Study",
    "Yield Trial",
    "Multi-Environment Trial",
    "Preliminary Yield Trial",
    "Advanced Yield Trial",
    "Regional Trial",
    "National Trial",
    "Observation Nursery",
    "Crossing Block",
    "Seed Multiplication",
    "DUS Trial",
    "VCU Trial",
    "Agronomic Trial",
    "Disease Screening",
    "Pest Screening",
    "Drought Screening",
    "Heat Screening",
    "Salinity Screening",
    "Quality Evaluation",
    "Molecular Breeding",
    "Genomic Selection",
    "Speed Breeding",
    "Doubled Haploid Production",
    "Tissue Culture",
    "Field Evaluation",
    "Greenhouse Study",
    "Growth Chamber Study",
    "Laboratory Study",
    "On-Farm Trial",
]


@router.get("/studytypes")
async def get_study_types(
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(1000, ge=1, le=2000, description="Page size"),
):
    """
    Get list of study types
    
    BrAPI Endpoint: GET /studytypes
    """
    # Paginate
    start = page * pageSize
    end = start + pageSize
    paginated = STUDY_TYPES[start:end]

    total_count = len(STUDY_TYPES)
    total_pages = (total_count + pageSize - 1) // pageSize

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total_count,
                "totalPages": total_pages
            },
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": {
            "data": paginated
        }
    }
