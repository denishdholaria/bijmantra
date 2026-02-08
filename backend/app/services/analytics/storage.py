import io
import logging
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    """
    Service for interacting with Object Storage (MinIO).
    Handles file uploads/downloads for the Data Lake.
    """

    def __init__(self):
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=settings.MINIO_USE_SSL,
            )
            self._available = True
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self._available = False

    def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """Ensure a bucket exists, creating it if necessary."""
        if not self._available:
            return False

        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"MinIO S3Error checking/creating bucket {bucket_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking/creating bucket {bucket_name}: {e}")
            return False

    def upload_data(self, bucket_name: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> bool:
        """Upload bytes data to MinIO."""
        if not self._available:
            return False

        if not self.ensure_bucket_exists(bucket_name):
            return False

        try:
            stream = io.BytesIO(data)
            self.client.put_object(
                bucket_name,
                object_name,
                stream,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded {object_name} to {bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {object_name} to {bucket_name}: {e}")
            return False

storage_service = StorageService()
