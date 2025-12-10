"""
Community Forums API

Endpoints for discussion forums.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.forums import get_forums_service

router = APIRouter(prefix="/forums", tags=["Forums"])


# Request/Response Models
class CategoryCreate(BaseModel):
    name: str
    description: str
    icon: str = "💬"


class TopicCreate(BaseModel):
    category_id: str
    title: str
    content: str
    tags: list[str] = []


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    is_pinned: Optional[bool] = None
    is_closed: Optional[bool] = None


class ReplyCreate(BaseModel):
    content: str


# Category Endpoints
@router.get("/categories")
async def list_categories():
    """Get all forum categories."""
    service = get_forums_service()
    return {"categories": service.get_categories()}


@router.post("/categories")
async def create_category(data: CategoryCreate):
    """Create a new category (admin only)."""
    service = get_forums_service()
    category = service.create_category(
        name=data.name,
        description=data.description,
        icon=data.icon,
    )
    return category


@router.get("/categories/{category_id}")
async def get_category(category_id: str):
    """Get a single category."""
    service = get_forums_service()
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# Topic Endpoints
@router.get("/topics")
async def list_topics(
    category_id: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(0, ge=0),
    page_size: int = Query(20, ge=1, le=100),
):
    """List topics with filtering and pagination."""
    service = get_forums_service()
    return service.get_topics(
        category_id=category_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("/topics")
async def create_topic(data: TopicCreate):
    """Create a new topic."""
    service = get_forums_service()
    
    # Verify category exists
    if not service.get_category(data.category_id):
        raise HTTPException(status_code=404, detail="Category not found")
    
    # In production, get author from JWT
    topic = service.create_topic(
        category_id=data.category_id,
        title=data.title,
        content=data.content,
        author_id="current-user",
        author_name="Current User",
        tags=data.tags,
    )
    return topic


@router.get("/topics/{topic_id}")
async def get_topic(topic_id: str):
    """Get a topic with all replies."""
    service = get_forums_service()
    topic = service.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.put("/topics/{topic_id}")
async def update_topic(topic_id: str, data: TopicUpdate):
    """Update a topic."""
    service = get_forums_service()
    topic = service.update_topic(topic_id, **data.model_dump(exclude_none=True))
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.post("/topics/{topic_id}/like")
async def like_topic(topic_id: str):
    """Like a topic."""
    service = get_forums_service()
    topic = service.like_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"likes": topic["likes"]}


@router.post("/topics/{topic_id}/pin")
async def pin_topic(topic_id: str):
    """Pin/unpin a topic (admin only)."""
    service = get_forums_service()
    topic = service.topics.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    topic["is_pinned"] = not topic["is_pinned"]
    return {"is_pinned": topic["is_pinned"]}


@router.post("/topics/{topic_id}/close")
async def close_topic(topic_id: str):
    """Close/reopen a topic."""
    service = get_forums_service()
    topic = service.topics.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    topic["is_closed"] = not topic["is_closed"]
    return {"is_closed": topic["is_closed"]}


# Reply Endpoints
@router.post("/topics/{topic_id}/replies")
async def add_reply(topic_id: str, data: ReplyCreate):
    """Add a reply to a topic."""
    service = get_forums_service()
    
    # In production, get author from JWT
    reply = service.add_reply(
        topic_id=topic_id,
        content=data.content,
        author_id="current-user",
        author_name="Current User",
    )
    if not reply:
        raise HTTPException(status_code=400, detail="Cannot reply to this topic")
    return reply


@router.post("/topics/{topic_id}/replies/{reply_id}/like")
async def like_reply(topic_id: str, reply_id: str):
    """Like a reply."""
    service = get_forums_service()
    reply = service.like_reply(topic_id, reply_id)
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    return {"likes": reply["likes"]}


# Stats Endpoint
@router.get("/stats")
async def get_stats():
    """Get forum statistics."""
    service = get_forums_service()
    return service.get_stats()
