"""
UAV Orthomosaic Stitcher Webhook Service

Handles incoming webhooks from UAV stitching services (e.g., WebODM, DroneDeploy).
Processes the results and updates the GISLayer database.
"""

import logging
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.spatial import GISLayer

logger = logging.getLogger(__name__)


class UAVWebhookPayload(BaseModel):
    """Payload for UAV stitching job completion webhook."""
    job_id: str
    status: str = Field(..., description="Status of the job (completed, failed, processing)")
    organization_id: int
    download_url: str | None = None
    metadata: dict[str, Any] | None = Field(default_factory=dict)


class UAVStitcherWebhookService:
    """Service to process UAV stitching webhooks."""

    async def process_webhook(self, payload: UAVWebhookPayload, db: AsyncSession) -> None:
        """
        Process the incoming webhook payload.

        Args:
            payload: The validated webhook payload.
            db: The database session.
        """
        logger.info(f"Received UAV stitching webhook for job {payload.job_id} with status {payload.status}")

        if payload.status.lower() == "completed":
            if not payload.download_url:
                logger.error(f"Job {payload.job_id} completed but no download_url provided.")
                return

            # Extract name or generate default
            name = payload.metadata.get("name") if payload.metadata else None
            if not name:
                name = f"UAV Orthomosaic {payload.job_id}"

            # Create GISLayer record
            new_layer = GISLayer(
                organization_id=payload.organization_id,
                name=name,
                layer_type="raster",
                category="orthomosaic",
                source_path=payload.download_url,
                driver="GTiff",  # Default assumption for orthomosaics
                description=f"Generated from UAV stitching job {payload.job_id}",
                is_active=True,
            )

            # Optional metadata mapping
            if payload.metadata:
                if "resolution" in payload.metadata:
                    try:
                        new_layer.resolution = float(payload.metadata["resolution"])
                    except (ValueError, TypeError):
                        pass
                if "band_count" in payload.metadata:
                    try:
                        new_layer.band_count = int(payload.metadata["band_count"])
                    except (ValueError, TypeError):
                        pass

            db.add(new_layer)
            await db.commit()
            await db.refresh(new_layer)
            logger.info(f"Created GISLayer {new_layer.id} for job {payload.job_id}")

        elif payload.status.lower() == "failed":
            logger.warning(f"UAV stitching job {payload.job_id} failed. No layer created.")
            # Optionally update a job status if we had a Job record, but for now just log.

        else:
            logger.info(f"Ignoring status {payload.status} for job {payload.job_id}")

uav_stitcher_service = UAVStitcherWebhookService()
