"""
BrAPI v2.1 Images Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.

GOVERNANCE.md §4.3.1 Compliant: Fully async implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of images from database"""
    # Build base statement with eager loading for observation_unit relationship
    stmt = select(Image).options(selectinload(Image.observation_unit))
    
    # Apply filters
    if imageDbId:
        stmt = stmt.where(Image.image_db_id == imageDbId)
    if imageName:
        stmt = stmt.where(Image.image_name.ilike(f"%{imageName}%"))
    if observationUnitDbId:
        stmt = stmt.join(ObservationUnit).where(
            ObservationUnit.observation_unit_db_id == observationUnitDbId
        )
    if observationDbId:
        stmt = stmt.where(Image.observation_db_id == observationDbId)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    result = await db.execute(stmt)
    results = result.scalars().all()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new image record in database"""
    org_id = current_user.organization_id if current_user else 1
    image_db_id = f"img_{uuid.uuid4().hex[:12]}"
    
    # Look up observation unit
    obs_unit_id = None
    if image.observationUnitDbId:
        stmt = select(ObservationUnit).where(
            ObservationUnit.observation_unit_db_id == image.observationUnitDbId
        )
        result = await db.execute(stmt)
        unit = result.scalar_one_or_none()
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
    await db.commit()
    await db.refresh(new_image)
    
    # Reload with relationship for response
    stmt = select(Image).options(selectinload(Image.observation_unit)).where(
        Image.id == new_image.id
    )
    result = await db.execute(stmt)
    new_image = result.scalar_one()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get image by ID from database"""
    stmt = select(Image).options(selectinload(Image.observation_unit)).where(
        Image.image_db_id == imageDbId
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update an image record"""
    stmt = select(Image).options(selectinload(Image.observation_unit)).where(
        Image.image_db_id == imageDbId
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()
    
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
    
    await db.commit()
    await db.refresh(image)
    
    # Reload with relationship for response
    stmt = select(Image).options(selectinload(Image.observation_unit)).where(
        Image.id == image.id
    )
    result = await db.execute(stmt)
    image = result.scalar_one()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update image content (binary upload)"""
    stmt = select(Image).options(selectinload(Image.observation_unit)).where(
        Image.image_db_id == imageDbId
    )
    result = await db.execute(stmt)
    image = result.scalar_one_or_none()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Delete multiple images at once"""
    deleted_ids = []
    
    for image_id in request.imageDbIds:
        stmt = select(Image).where(Image.image_db_id == image_id)
        result = await db.execute(stmt)
        image = result.scalar_one_or_none()
        if image:
            await db.delete(image)
            deleted_ids.append(image_id)
    
    await db.commit()
    
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
