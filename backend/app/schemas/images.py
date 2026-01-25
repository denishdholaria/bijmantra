from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ImageBase(BaseModel):
    """Base schema for Image"""
    imageName: str = Field(..., description="The human readable name of an image")
    imageFileName: Optional[str] = Field(None, description="The name of the image file")
    imageFileSize: Optional[int] = Field(None, description="The size of the image file in bytes")
    imageHeight: Optional[int] = Field(None, description="The height of the image in pixels")
    imageWidth: Optional[int] = Field(None, description="The width of the image in pixels")
    mimeType: Optional[str] = Field(None, description="The valid MIME type of the image file")
    imageURL: Optional[str] = Field(None, description="The absolute URL to the image file")
    imageTimeStamp: Optional[str] = Field(None, description="The date and time the image was taken")
    copyright: Optional[str] = Field(None, description="The copyright information of the image")
    description: Optional[str] = Field(None, description="The description of the image")
    descriptiveOntologyTerms: Optional[List[str]] = Field(None, description="A list of ontology terms to describe the image")
    observationUnitDbId: Optional[str] = Field(None, description="The related observation unit")
    observationDbId: Optional[str] = Field(None, description="The related observation")
    imageLocation: Optional[Dict[str, Any]] = Field(None, description="The GeoJSON object describing the location")
    additionalInfo: Optional[Dict[str, Any]] = Field(None, description="Additional arbitrary info")
    externalReferences: Optional[List[Dict[str, Any]]] = Field(None, description="External references")

class ImageNewRequest(ImageBase):
    """Schema for creating a new Image"""
    pass

class ImageUpdateRequest(ImageBase):
    """Schema for updating an Image"""
    imageName: Optional[str] = None

class Image(ImageBase):
    """Schema for Image response"""
    imageDbId: str = Field(..., description="The unique identifier for the image")

class ImageSearchRequest(BaseModel):
    """Schema for searching images"""
    imageDbIds: Optional[List[str]] = None
    imageNames: Optional[List[str]] = None
    observationUnitDbIds: Optional[List[str]] = None
    observationDbIds: Optional[List[str]] = None
    descriptiveOntologyTerms: Optional[List[str]] = None
    page: int = 0
    pageSize: int = 20
