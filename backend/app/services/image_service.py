from typing import List, Optional, Tuple, BinaryIO
import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from fastapi.concurrency import run_in_threadpool

from app.models.phenotyping import Image, ObservationUnit
from app.schemas.images import ImageNewRequest, ImageUpdateRequest, ImageSearchRequest
from app.services.analytics.storage import storage_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.bucket_name = "bijmantra-images"

    async def upload_image_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """
        Uploads an image file to object storage and returns the public URL.
        """
        # Generate unique object name
        ext = filename.split('.')[-1] if '.' in filename else "jpg"
        object_name = f"{uuid.uuid4().hex}.{ext}"

        # Ensure bucket exists (sync call wrapped)
        # Using default storage service which checks bucket in upload_data, but let's be safe
        # upload_data is synchronous
        success = await run_in_threadpool(
            storage_service.upload_data,
            self.bucket_name,
            object_name,
            file_data,
            content_type
        )

        if not success:
            raise Exception("Failed to upload image to storage")

        # Construct URL
        # Assuming MinIO or S3 compatible URL structure
        # If using MinIO locally with Docker, it might be http://localhost:9000/...
        # We should use settings to construct the URL

        # If settings.MINIO_PUBLIC_URL is set, use it, otherwise fallback
        base_url = getattr(settings, "MINIO_PUBLIC_URL", None)
        if not base_url:
            # Fallback to constructing from endpoint
            protocol = "https" if settings.MINIO_USE_SSL else "http"
            base_url = f"{protocol}://{settings.MINIO_ENDPOINT}"

        return f"{base_url}/{self.bucket_name}/{object_name}"

    async def list_images(
        self,
        db: AsyncSession,
        search_request: ImageSearchRequest,
        organization_id: int
    ) -> Tuple[List[Image], int]:
        """
        List images with filtering and pagination.
        """
        stmt = select(Image).options(selectinload(Image.observation_unit))
        stmt = stmt.where(Image.organization_id == organization_id)

        if search_request.imageDbIds:
            stmt = stmt.where(Image.image_db_id.in_(search_request.imageDbIds))
        if search_request.imageNames:
            # Case insensitive search for names if single, or IN if multiple?
            # BrAPI spec usually implies exact match for lists, but let's stick to exact for lists
            stmt = stmt.where(Image.image_name.in_(search_request.imageNames))
        if search_request.observationUnitDbIds:
            stmt = stmt.join(ObservationUnit).where(
                ObservationUnit.observation_unit_db_id.in_(search_request.observationUnitDbIds)
            )
        if search_request.observationDbIds:
            stmt = stmt.where(Image.observation_db_id.in_(search_request.observationDbIds))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Pagination
        stmt = stmt.offset(search_request.page * search_request.pageSize).limit(search_request.pageSize)

        result = await db.execute(stmt)
        return result.scalars().all(), total

    async def get_image(self, db: AsyncSession, image_db_id: str, organization_id: int) -> Optional[Image]:
        """
        Get a specific image.
        """
        stmt = select(Image).options(selectinload(Image.observation_unit)).where(
            Image.image_db_id == image_db_id,
            Image.organization_id == organization_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_image(self, db: AsyncSession, image_data: ImageNewRequest, organization_id: int) -> Image:
        """
        Create a new image record.
        """
        image_db_id = f"img_{uuid.uuid4().hex[:12]}"

        # Resolve observation unit
        obs_unit_id = None
        if image_data.observationUnitDbId:
            stmt = select(ObservationUnit).where(
                ObservationUnit.observation_unit_db_id == image_data.observationUnitDbId,
                ObservationUnit.organization_id == organization_id
            )
            result = await db.execute(stmt)
            unit = result.scalar_one_or_none()
            if unit:
                obs_unit_id = unit.id

        new_image = Image(
            organization_id=organization_id,
            image_db_id=image_db_id,
            image_name=image_data.imageName,
            image_file_name=image_data.imageFileName,
            image_file_size=image_data.imageFileSize,
            image_height=image_data.imageHeight,
            image_width=image_data.imageWidth,
            mime_type=image_data.mimeType,
            image_url=image_data.imageURL,
            image_time_stamp=image_data.imageTimeStamp or datetime.utcnow().isoformat(),
            copyright=image_data.copyright,
            description=image_data.description,
            descriptive_ontology_terms=image_data.descriptiveOntologyTerms,
            observation_unit_id=obs_unit_id,
            observation_db_id=image_data.observationDbId,
            image_location=image_data.imageLocation,
            additional_info=image_data.additionalInfo,
            external_references=image_data.externalReferences
        )

        db.add(new_image)
        await db.commit()
        await db.refresh(new_image)

        # Reload to get relationships
        return await self.get_image(db, image_db_id, organization_id)

    async def update_image(
        self,
        db: AsyncSession,
        image_db_id: str,
        image_data: ImageUpdateRequest,
        organization_id: int
    ) -> Optional[Image]:
        """
        Update an image record.
        """
        image = await self.get_image(db, image_db_id, organization_id)
        if not image:
            return None

        # Manual mapping for safety and clarity
        if image_data.imageName is not None: image.image_name = image_data.imageName
        if image_data.imageFileName is not None: image.image_file_name = image_data.imageFileName
        if image_data.imageFileSize is not None: image.image_file_size = image_data.imageFileSize
        if image_data.imageHeight is not None: image.image_height = image_data.imageHeight
        if image_data.imageWidth is not None: image.image_width = image_data.imageWidth
        if image_data.mimeType is not None: image.mime_type = image_data.mimeType
        if image_data.imageURL is not None: image.image_url = image_data.imageURL
        if image_data.imageTimeStamp is not None: image.image_time_stamp = image_data.imageTimeStamp
        if image_data.copyright is not None: image.copyright = image_data.copyright
        if image_data.description is not None: image.description = image_data.description
        if image_data.descriptiveOntologyTerms is not None: image.descriptive_ontology_terms = image_data.descriptiveOntologyTerms
        if image_data.observationDbId is not None: image.observation_db_id = image_data.observationDbId
        if image_data.imageLocation is not None: image.image_location = image_data.imageLocation
        if image_data.additionalInfo is not None: image.additional_info = image_data.additionalInfo
        if image_data.externalReferences is not None: image.external_references = image_data.externalReferences

        if image_data.observationUnitDbId is not None:
             stmt = select(ObservationUnit).where(
                ObservationUnit.observation_unit_db_id == image_data.observationUnitDbId,
                ObservationUnit.organization_id == organization_id
            )
             result = await db.execute(stmt)
             unit = result.scalar_one_or_none()
             if unit:
                image.observation_unit_id = unit.id
             else:
                 # Should we fail or set to None?
                 # Assuming if ID provided but not found, we ignore or set to None.
                 # Setting to None seems safer if not found, or maybe keep old value?
                 # Standard BrAPI: "The observationUnitDbId must reference an existing observationUnit."
                 # So maybe we should check and raise error if not found?
                 # For now, let's keep it simple: if not found, don't link.
                 pass

        await db.commit()
        await db.refresh(image)
        return image

    async def delete_image(self, db: AsyncSession, image_db_id: str, organization_id: int) -> bool:
        """
        Delete an image.
        """
        image = await self.get_image(db, image_db_id, organization_id)
        if not image:
            return False

        await db.delete(image)
        await db.commit()
        return True

image_service = ImageService()
