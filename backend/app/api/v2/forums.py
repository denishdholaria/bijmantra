"""
Forums API
Community discussion — categories, topics, replies.

Refactored: Session 94 — migrated from in-memory demo data.
Forums tables (forum_categories, forum_topics, forum_replies) not yet created.
All endpoints return honest empty results until migration is created.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id

from app.api.deps import get_current_user

router = APIRouter(prefix="/forums", tags=["Forums"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Schemas
# ============================================================================

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: str = Field(default="💬")


class TopicCreate(BaseModel):
    category_id: str = Field(...)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None


class ReplyCreate(BaseModel):
    content: str = Field(..., min_length=1)


# ============================================================================
# Category Endpoints
# ============================================================================

@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get forum categories. Forums table not yet created."""
    return []


@router.post("/categories")
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Create a forum category. Forums table not yet created."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created. Migration pending.")


@router.get("/categories/{category_id}")
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a single category."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


# ============================================================================
# Topic Endpoints
# ============================================================================

@router.get("/topics")
async def get_topics(
    category_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: Optional[str] = Query("recent"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get topics. Forums table not yet created."""
    return {"data": [], "total": 0, "page": page, "page_size": page_size}


@router.post("/topics")
async def create_topic(
    topic: TopicCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Create a topic. Forums table not yet created."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created. Migration pending.")


@router.get("/topics/{topic_id}")
async def get_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a single topic."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


@router.patch("/topics/{topic_id}")
async def update_topic(
    topic_id: str,
    update: TopicUpdate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Update a topic."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


@router.post("/topics/{topic_id}/like")
async def like_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Like a topic."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


@router.post("/topics/{topic_id}/pin")
async def pin_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Pin a topic."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


@router.post("/topics/{topic_id}/close")
async def close_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Close a topic."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


# ============================================================================
# Reply Endpoints
# ============================================================================

@router.post("/topics/{topic_id}/replies")
async def add_reply(
    topic_id: str,
    reply: ReplyCreate,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Add a reply to a topic."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


@router.post("/topics/{topic_id}/replies/{reply_id}/like")
async def like_reply(
    topic_id: str,
    reply_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Like a reply."""
    raise HTTPException(status_code=501, detail="Forums tables not yet created")


# ============================================================================
# Stats
# ============================================================================

@router.get("/stats")
async def get_forum_stats(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get forum statistics."""
    return {
        "total_categories": 0,
        "total_topics": 0,
        "total_replies": 0,
        "active_users": 0,
        "note": "Forums tables not yet created. Migration pending.",
    }
