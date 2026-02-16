"""
BrAPI Core - Common Crop Names endpoint
GET /commoncropnames - Returns list of crops supported by this server
"""

from typing import List
from fastapi import APIRouter, Query
from app.core.config import settings

router = APIRouter()

# Common crops supported by Bijmantra
COMMON_CROPS = [
    "Rice",
    "Wheat",
    "Maize",
    "Sorghum",
    "Pearl Millet",
    "Finger Millet",
    "Barley",
    "Oats",
    "Chickpea",
    "Pigeonpea",
    "Groundnut",
    "Soybean",
    "Lentil",
    "Mungbean",
    "Urdbean",
    "Cotton",
    "Sugarcane",
    "Sunflower",
    "Mustard",
    "Sesame",
    "Safflower",
    "Castor",
    "Potato",
    "Tomato",
    "Onion",
    "Chilli",
    "Brinjal",
    "Okra",
    "Cabbage",
    "Cauliflower",
    "Carrot",
    "Radish",
    "Cucumber",
    "Pumpkin",
    "Watermelon",
    "Mango",
    "Banana",
    "Citrus",
    "Grape",
    "Apple",
    "Papaya",
    "Guava",
    "Pomegranate",
    "Coconut",
    "Arecanut",
    "Cashew",
    "Coffee",
    "Tea",
    "Rubber",
    "Jute",
]


@router.get("/commoncropnames")
async def get_common_crop_names(
    page: int = Query(0, ge=0, description="Page number"),
    pageSize: int = Query(1000, ge=1, le=2000, description="Page size"),
):
    """
    Get list of common crop names supported by this server
    
    BrAPI Endpoint: GET /commoncropnames
    """
    # Paginate
    start = page * pageSize
    end = start + pageSize
    paginated_crops = COMMON_CROPS[start:end]

    total_count = len(COMMON_CROPS)
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
            "data": paginated_crops
        }
    }
