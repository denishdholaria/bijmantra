"""
BrAPI v2.1 Images Endpoints

Database-backed implementation with MinIO support.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.services.image_service import image_service
from app.schemas.images import Image, ImageNewRequest, ImageUpdateRequest, ImageSearchRequest
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status

router = APIRouter()

def create_brapi_response(data: any, page: int = 0, page_size: int = 0, total_count: int = 0) -> BrAPIResponse:
    total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0
    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=page_size,
                totalCount=total_count,
                totalPages=total_pages
            ),
            status=[Status(message="Success", message_type="INFO")]
        ),
        result=data
    )

def _model_to_dict(image) -> dict:
    """Helper to convert SQLAlchemy model to BrAPI dict if Pydantic fails with relations"""
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

@router.post("/images/upload", status_code=201)
async def upload_image_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Upload an image file and get a public URL.
    This is a helper endpoint to facilitate creating Image objects.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    content = await file.read()
    url = await image_service.upload_image_file(content, file.filename, file.content_type)

    return {
        "metadata": Metadata(
            pagination=Pagination(currentPage=0, pageSize=1, totalCount=1, totalPages=1),
            status=[Status(message="File uploaded successfully", message_type="INFO")]
        ),
        "result": {
            "imageURL": url
        }
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
    """Retrieves a filtered list of images."""
    org_id = current_user.organization_id if current_user else 1

    search_request = ImageSearchRequest(
        imageDbIds=[imageDbId] if imageDbId else None,
        imageNames=[imageName] if imageName else None,
        observationUnitDbIds=[observationUnitDbId] if observationUnitDbId else None,
        observationDbIds=[observationDbId] if observationDbId else None,
        page=page,
        pageSize=pageSize
    )

    images, total = await image_service.list_images(db, search_request, org_id)

    data = {"data": [_model_to_dict(img) for img in images]}
    return create_brapi_response(data, page, pageSize, total)

@router.post("/images")
async def create_image(
    image: ImageNewRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Creates a new image record."""
    org_id = current_user.organization_id if current_user else 1

    # Check if observationUnitDbId is provided but not found is handled in service (will create without link)
    # or strict validation? BrAPI says "The observationUnitDbId must reference an existing observationUnit."

    new_image = await image_service.create_image(db, image, org_id)

    return create_brapi_response(_model_to_dict(new_image), 0, 1, 1)

@router.get("/images/{imageDbId}")
async def get_image(
    imageDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Retrieves a specific image."""
    org_id = current_user.organization_id if current_user else 1
    image = await image_service.get_image(db, imageDbId, org_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return create_brapi_response(_model_to_dict(image), 0, 1, 1)

@router.put("/images/{imageDbId}")
async def update_image(
    imageDbId: str,
    image_data: ImageUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Updates an existing image."""
    org_id = current_user.organization_id if current_user else 1
    image = await image_service.update_image(db, imageDbId, image_data, org_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return create_brapi_response(_model_to_dict(image), 0, 1, 1)

@router.delete("/images/{imageDbId}")
async def delete_image(
    imageDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Deletes an image."""
    org_id = current_user.organization_id if current_user else 1
    success = await image_service.delete_image(db, imageDbId, org_id)

    if not success:
        raise HTTPException(status_code=404, detail="Image not found")

    return create_brapi_response(None, 0, 0, 0)
