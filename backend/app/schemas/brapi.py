"""
BrAPI Common Schemas
Metadata, Pagination, Response wrappers
"""

from typing import List, Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict


class Status(BaseModel):
    """BrAPI Status message"""
    message: str
    message_type: str = "INFO"


class Pagination(BaseModel):
    """BrAPI Pagination metadata"""
    current_page: int = Field(alias="currentPage")
    page_size: int = Field(alias="pageSize")
    total_count: int = Field(alias="totalCount")
    total_pages: int = Field(alias="totalPages")
    
    model_config = ConfigDict(populate_by_name=True)


class Metadata(BaseModel):
    """BrAPI Metadata wrapper"""
    datafiles: List[str] = []
    pagination: Pagination
    status: List[Status] = [Status(message="Success", message_type="INFO")]


T = TypeVar('T')


class BrAPIResponse(BaseModel, Generic[T]):
    """BrAPI Response wrapper"""
    metadata: Metadata
    result: T


class ExternalReference(BaseModel):
    """BrAPI External Reference"""
    reference_id: Optional[str] = Field(None, alias="referenceId")
    reference_source: Optional[str] = Field(None, alias="referenceSource")
    
    model_config = ConfigDict(populate_by_name=True)


class AdditionalInfo(BaseModel):
    """BrAPI Additional Info - flexible key-value pairs"""
    model_config = ConfigDict(extra="allow")
