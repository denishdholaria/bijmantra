"""
BrAPI Common Schemas
Metadata, Pagination, Response wrappers
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


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
    datafiles: list[str] = []
    pagination: Pagination
    status: list[Status] = [Status(message="Success", message_type="INFO")]


T = TypeVar('T')


class BrAPIResponse(BaseModel, Generic[T]):
    """BrAPI Response wrapper"""
    metadata: Metadata
    result: T


class ExternalReference(BaseModel):
    """BrAPI External Reference"""
    reference_id: str | None = Field(None, alias="referenceId")
    reference_source: str | None = Field(None, alias="referenceSource")

    model_config = ConfigDict(populate_by_name=True)


class AdditionalInfo(BaseModel):
    """BrAPI Additional Info - flexible key-value pairs"""
    model_config = ConfigDict(extra="allow")
