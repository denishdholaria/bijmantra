from typing import Any

from pydantic import BaseModel, Field


class ImageBase(BaseModel):
    """Base schema for Image"""
    imageName: str = Field(..., description="The human readable name of an image")
    imageFileName: str | None = Field(None, description="The name of the image file")
    imageFileSize: int | None = Field(None, description="The size of the image file in bytes")
    imageHeight: int | None = Field(None, description="The height of the image in pixels")
    imageWidth: int | None = Field(None, description="The width of the image in pixels")
    mimeType: str | None = Field(None, description="The valid MIME type of the image file")
    imageURL: str | None = Field(None, description="The absolute URL to the image file")
    imageTimeStamp: str | None = Field(None, description="The date and time the image was taken")
    copyright: str | None = Field(None, description="The copyright information of the image")
    description: str | None = Field(None, description="The description of the image")
    descriptiveOntologyTerms: list[str] | None = Field(None, description="A list of ontology terms to describe the image")
    observationUnitDbId: str | None = Field(None, description="The related observation unit")
    observationDbId: str | None = Field(None, description="The related observation")
    imageLocation: dict[str, Any] | None = Field(None, description="The GeoJSON object describing the location")
    additionalInfo: dict[str, Any] | None = Field(None, description="Additional arbitrary info")
    externalReferences: list[dict[str, Any]] | None = Field(None, description="External references")

class ImageNewRequest(ImageBase):
    """Schema for creating a new Image"""
    pass

class ImageUpdateRequest(ImageBase):
    """Schema for updating an Image"""
    imageName: str | None = None

class Image(ImageBase):
    """Schema for Image response"""
    imageDbId: str = Field(..., description="The unique identifier for the image")

class ImageSearchRequest(BaseModel):
    """Schema for searching images"""
    imageDbIds: list[str] | None = None
    imageNames: list[str] | None = None
    observationUnitDbIds: list[str] | None = None
    observationDbIds: list[str] | None = None
    descriptiveOntologyTerms: list[str] | None = None
    page: int = 0
    pageSize: int = 20
