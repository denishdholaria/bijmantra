"""
BrAPI v2.1 Images Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter()

_images_store: dict = {}
_images_counter = 0


class ImageBase(BaseModel):
    imageName: Optional[str] = None
    imageFileName: Optional[str] = None
    imageFileSize: Optional[int] = None
    imageWidth: Optional[int] = None
    imageHeight: Optional[int] = None
    mimeType: Optional[str] = None
    imageURL: Optional[str] = None
    description: Optional[str] = None
    observationUnitDbId: Optional[str] = None
    observationDbIds: Optional[List[str]] = []
    descriptiveOntologyTerms: Optional[List[str]] = []
    copyright: Optional[str] = None
    imageTimeStamp: Optional[str] = None
    imageLocation: Optional[dict] = None


class ImageCreate(ImageBase):
    pass


def _init_demo_data():
    global _images_counter
    if _images_store:
        return
    
    demo_images = [
        {"imageName": "Rice Plot 001", "imageFileName": "rice_plot_001.jpg", "mimeType": "image/jpeg", "imageWidth": 1920, "imageHeight": 1080, "description": "Rice plot at flowering stage", "imageURL": "/images/rice_plot_001.jpg"},
        {"imageName": "Wheat Disease", "imageFileName": "wheat_rust.jpg", "mimeType": "image/jpeg", "imageWidth": 1280, "imageHeight": 720, "description": "Wheat rust infection", "imageURL": "/images/wheat_rust.jpg"},
        {"imageName": "Maize Ear", "imageFileName": "maize_ear.jpg", "mimeType": "image/jpeg", "imageWidth": 1920, "imageHeight": 1080, "description": "Maize ear at maturity", "imageURL": "/images/maize_ear.jpg"},
        {"imageName": "Field Overview", "imageFileName": "field_drone.jpg", "mimeType": "image/jpeg", "imageWidth": 4000, "imageHeight": 3000, "description": "Drone image of trial field", "imageURL": "/images/field_drone.jpg"},
    ]
    
    for img in demo_images:
        _images_counter += 1
        iid = f"image_{_images_counter}"
        _images_store[iid] = {"imageDbId": iid, **img}


@router.get("/images")
async def list_images(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    observationUnitDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get list of images"""
    _init_demo_data()
    
    results = list(_images_store.values())
    
    if observationUnitDbId:
        results = [i for i in results if i.get("observationUnitDbId") == observationUnitDbId]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/images")
async def create_image(image: ImageCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new image record"""
    global _images_counter
    _init_demo_data()
    
    _images_counter += 1
    iid = f"image_{_images_counter}"
    new_image = {"imageDbId": iid, **image.model_dump()}
    _images_store[iid] = new_image
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_image}


@router.get("/images/{imageDbId}")
async def get_image(imageDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Get image by ID"""
    _init_demo_data()
    if imageDbId not in _images_store:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _images_store[imageDbId]}
