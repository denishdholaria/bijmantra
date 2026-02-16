"""
BrAPI v2.1 Allele Matrix Endpoints
Allele matrix for genotype data
"""

from fastapi import APIRouter, Query
from typing import Optional, List
import uuid

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000):
    """Standard BrAPI response wrapper"""
    if isinstance(result, list):
        total = len(result)
        start = page * page_size
        end = start + page_size
        data = result[start:end]
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": (total + page_size - 1) // page_size
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": data}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }


@router.get("/allelematrix")
async def get_allele_matrix(
    dimensionVariantPage: int = Query(0, ge=0),
    dimensionVariantPageSize: int = Query(1000, ge=1, le=10000),
    dimensionCallSetPage: int = Query(0, ge=0),
    dimensionCallSetPageSize: int = Query(1000, ge=1, le=10000),
    preview: bool = False,
    dataMatrixAbbreviations: Optional[List[str]] = Query(None),
    dataMatrixNames: Optional[List[str]] = Query(None),
    germplasmDbId: Optional[List[str]] = Query(None),
    germplasmName: Optional[List[str]] = Query(None),
    germplasmPUI: Optional[List[str]] = Query(None),
    callSetDbId: Optional[List[str]] = Query(None),
    variantDbId: Optional[List[str]] = Query(None),
    variantSetDbId: Optional[List[str]] = Query(None),
    expandHomozygotes: bool = False,
    unknownString: str = ".",
    sepPhased: str = "|",
    sepUnphased: str = "/"
):
    """Get allele matrix data"""
    # Demo allele matrix
    callset_ids = ["callset-001", "callset-002", "callset-003"]
    variant_ids = ["variant-001", "variant-002", "variant-003"]

    # Filter if specified
    if callSetDbId:
        callset_ids = [c for c in callset_ids if c in callSetDbId]
    if variantDbId:
        variant_ids = [v for v in variant_ids if v in variantDbId]

    # Build matrix
    data_matrices = [
        {
            "dataMatrixAbbreviation": "GT",
            "dataMatrixName": "Genotype",
            "dataType": "string",
            "dataMatrix": [
                ["A/A", "G/T", "AT/A"],  # callset-001
                ["A/G", "G/G", "AT/AT"],  # callset-002
                ["G/G", "T/T", "A/A"]     # callset-003
            ][:len(callset_ids)]
        }
    ]

    result = {
        "callSetDbIds": callset_ids,
        "variantDbIds": variant_ids,
        "variantSetDbIds": ["variantset-001"],
        "dataMatrices": data_matrices,
        "expandHomozygotes": expandHomozygotes,
        "sepPhased": sepPhased,
        "sepUnphased": sepUnphased,
        "unknownString": unknownString,
        "pagination": [
            {
                "dimension": "VARIANTS",
                "page": dimensionVariantPage,
                "pageSize": dimensionVariantPageSize,
                "totalCount": len(variant_ids),
                "totalPages": 1
            },
            {
                "dimension": "CALLSETS",
                "page": dimensionCallSetPage,
                "pageSize": dimensionCallSetPageSize,
                "totalCount": len(callset_ids),
                "totalPages": 1
            }
        ]
    }

    return {
        "metadata": {
            "datafiles": [],
            "pagination": None,
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }
