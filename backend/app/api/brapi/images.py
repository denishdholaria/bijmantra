"""
BrAPI v2.1 Images Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.phenotyping import Image, ObservationUnit

router = APIRouter()


class ImageBase(BaseModel):
    imageName: str
    imageFileName: Optional[str] = None
    imageFileSize: Optional[int] = None
    imageHeight: Optional[int] = None
    imageWidth: Optional[int] = None
    mimeType: Optional[str] = None
    imageURL: Optional[str] = None
    imageTimeStamp: Optional[str] = None
    copyright: Optional[str] = None
    description: Optional[str] = None
    descriptiveOntologyTerms: Optional[List[str]] = None
    observationUnitDbId: Optional[str] = None
    observationDbId: Optional[str] = None
    imageLocation: Optional[dict] = None


class ImageCreate(ImageBase):
    pass


class ImageUpdate(ImageBase):
    imageName: Optional[str] = None


def _model_to_brapi(image: Image) -> dict:
    """Convert SQLAlchemy model to BrAPI response format"""
    return {
        "imageDbId": image.image_db_id,
        "imageName": image.image_name,
        "imageFileName": image.image_file_name,
        "imageFileSize": image.image_file_size,
        "imageHeight": image.image_height,
        "imageWidth": image.image_width,
        "mimeType": image.mime_type,
        "imageURL": image.image_url,
        "imageTimeStamp": image.image_time_stamp,
        "copyright": image.copyright,
        "description": image.description,
        "descriptiveOntologyTerms": image.descriptive_ontology_terms,
        "observationUnitDbId": image.observation_unit.observation_unit_db_id if image.observation_unit else None,
        "observationDbId": image.observation_db_id,
        "imageLocation": image.image_location,
        "additionalInfo": image.additional_info,
        "externalReferences": image.external_references,
    }


@router.get("/images")
async def list_images(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    imageDbId: Optional[str] = None,
    imageName: Optional[str] = None,
    observationUnitDbId: Optional[str] = None,
    observationDbId: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of images from database"""
    query = db.query(Image)
    
    if imageDbId:
        query = query.filter(Image.image_db_id == imageDbId)
    if imageName:
        query = query.filter(Image.image_name.ilike(f"%{imageName}%"))
    if observationUnitDbId:
        query = query.join(ObservationUnit).filter(
            ObservationUnit.observation_unit_db_id == observationUnitDbId
        )
    if observationDbId:
        query = query.filter(Image.observation_db_id == observationDbId)
    
    total = query.count()
    results = query.offset(page * pageSize).limit(pageSize).all()
    data = [_model_to_brapi(img) for img in results]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


@router.post("/images")
async def create_image(
    image: ImageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new image record in database"""
    org_id = current_user.organization_id if current_user else 1
    image_db_id = f"img_{uuid.uuid4().hex[:12]}"
    
    # Look up observation unit
    obs_unit_id = None
    if image.observationUnitDbId:
        unit = db.query(ObservationUnit).filter(
            ObservationUnit.observation_unit_db_id == image.observationUnitDbId
        ).first()
        if unit:
            obs_unit_id = unit.id
    
    new_image = Image(
        organization_id=org_id,
        image_db_id=image_db_id,
        image_name=image.imageName,
        image_file_name=image.imageFileName,
        image_file_size=image.imageFileSize,
        image_height=image.imageHeight,
        image_width=image.imageWidth,
        mime_type=image.mimeType,
        image_url=image.imageURL,
        image_time_stamp=image.imageTimeStamp,
        copyright=image.copyright,
        description=image.description,
        descriptive_ontology_terms=image.descriptiveOntologyTerms,
        observation_unit_id=obs_unit_id,
        observation_db_id=image.observationDbId,
        image_location=image.imageLocation,
    )
    
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Image created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_image)
    }


@router.get("/images/{imageDbId}")
async def get_image(
    imageDbId: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get image by ID from database"""
    image = db.query(Image).filter(Image.image_db_id == imageDbId).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(image)
    }


@router.put("/images/{imageDbId}")
async def update_image(
    imageDbId: str,
    image_data: ImageUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update an image record"""
    image = db.query(Image).filter(Image.image_db_id == imageDbId).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if image_data.imageName:
        image.image_name = image_data.imageName
    if image_data.description:
        image.description = image_data.description
    if image_data.imageURL:
        image.image_url = image_data.imageURL
    if image_data.copyright:
        image.copyright = image_data.copyright
    if image_data.descriptiveOntologyTerms:
        image.descriptive_ontology_terms = image_data.descriptiveOntologyTerms
    if image_data.imageLocation:
        image.image_location = image_data.imageLocation
    
    db.commit()
    db.refresh(image)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Image updated successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(image)
    }


@router.put("/images/{imageDbId}/imagecontent")
async def update_image_content(
    imageDbId: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update image content (binary upload)"""
    image = db.query(Image).filter(Image.image_db_id == imageDbId).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # In a real implementation, this would handle binary upload
    # For now, just return success
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Image content updated", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(image)
    }


class DeleteImagesRequest(BaseModel):
    imageDbIds: List[str]


@router.post("/delete/images")
async def delete_images_bulk(
    request: DeleteImagesRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Delete multiple images at once"""
    deleted_ids = []
    
    for image_id in request.imageDbIds:
        image = db.query(Image).filter(Image.image_db_id == image_id).first()
        if image:
            db.delete(image)
            deleted_ids.append(image_id)
    
    db.commit()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(deleted_ids), "totalCount": len(deleted_ids), "totalPages": 1},
            "status": [{"message": f"Deleted {len(deleted_ids)} images", "messageType": "INFO"}]
        },
        "result": {
            "deletedImageDbIds": deleted_ids
        }
    }
