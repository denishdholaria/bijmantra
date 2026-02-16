"""
BrAPI v2.1 Breeding Methods Endpoints
GET /breedingmethods
GET /breedingmethods/{breedingMethodDbId}
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

router = APIRouter()


class BreedingMethod(BaseModel):
    breedingMethodDbId: str
    breedingMethodName: str
    abbreviation: Optional[str] = None
    description: Optional[str] = None


# Standard breeding methods
BREEDING_METHODS = [
    BreedingMethod(
        breedingMethodDbId="bm-001",
        breedingMethodName="Single Seed Descent",
        abbreviation="SSD",
        description="Advancing generations by selecting a single seed from each plant"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-002",
        breedingMethodName="Pedigree Selection",
        abbreviation="PED",
        description="Selection based on individual plant performance with pedigree tracking"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-003",
        breedingMethodName="Bulk Population",
        abbreviation="BULK",
        description="Advancing generations by bulking seeds from all plants"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-004",
        breedingMethodName="Backcross",
        abbreviation="BC",
        description="Repeated crossing to a recurrent parent to transfer specific traits"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-005",
        breedingMethodName="Marker Assisted Backcross",
        abbreviation="MABC",
        description="Backcrossing with molecular marker selection"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-006",
        breedingMethodName="Doubled Haploid",
        abbreviation="DH",
        description="Production of homozygous lines through haploid induction and chromosome doubling"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-007",
        breedingMethodName="Recurrent Selection",
        abbreviation="RS",
        description="Cyclic selection and intercrossing to improve population mean"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-008",
        breedingMethodName="Genomic Selection",
        abbreviation="GS",
        description="Selection based on genomic estimated breeding values"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-009",
        breedingMethodName="Mass Selection",
        abbreviation="MS",
        description="Selection of superior phenotypes from a population"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-010",
        breedingMethodName="Mutation Breeding",
        abbreviation="MUT",
        description="Induction and selection of mutations for desired traits"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-011",
        breedingMethodName="Hybrid Development",
        abbreviation="HYB",
        description="Development of F1 hybrids from inbred lines"
    ),
    BreedingMethod(
        breedingMethodDbId="bm-012",
        breedingMethodName="Speed Breeding",
        abbreviation="SB",
        description="Accelerated generation advancement under controlled conditions"
    ),
]


def create_response(data, page=0, page_size=1000, total_count=1):
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total_count,
                "totalPages": total_pages
            },
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": data
    }


@router.get("/breedingmethods")
async def get_breeding_methods(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
):
    """
    Get list of breeding methods
    
    BrAPI Endpoint: GET /breedingmethods
    """
    total_count = len(BREEDING_METHODS)
    start = page * pageSize
    end = start + pageSize
    paginated = BREEDING_METHODS[start:end]

    return create_response(
        {"data": [m.model_dump() for m in paginated]},
        page, pageSize, total_count
    )


@router.get("/breedingmethods/{breedingMethodDbId}")
async def get_breeding_method(breedingMethodDbId: str):
    """
    Get a single breeding method by DbId
    
    BrAPI Endpoint: GET /breedingmethods/{breedingMethodDbId}
    """
    for method in BREEDING_METHODS:
        if method.breedingMethodDbId == breedingMethodDbId:
            return create_response(method.model_dump())

    raise HTTPException(status_code=404, detail="Breeding method not found")
