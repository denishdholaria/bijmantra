"""
Social Graph API v2
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.core import User
from app.schemas.social import (
    PostCreate, PostUpdate, PostResponse,
    CommentCreate, CommentResponse,
    ReactionCreate, ReactionResponse,
    ReportCreate, ReportResponse,
    GroupCreate, GroupUpdate, GroupResponse, GroupMemberResponse,
    FollowCreate, FollowResponse, ReputationResponse
)
from app.services.social.graph import SocialGraphService
from app.services.social.content import ContentService
from app.services.social.moderation import ModerationService
from app.services.social.groups import GroupService

router = APIRouter(dependencies=[Depends(get_current_user)])

# Dependencies
def get_graph_service(db: AsyncSession = Depends(get_db)) -> SocialGraphService:
    return SocialGraphService(db)

def get_content_service(db: AsyncSession = Depends(get_db)) -> ContentService:
    return ContentService(db)

def get_moderation_service(db: AsyncSession = Depends(get_db)) -> ModerationService:
    return ModerationService(db)

def get_group_service(db: AsyncSession = Depends(get_db)) -> GroupService:
    return GroupService(db)

# =============================================================================
# FEED & GRAPH
# =============================================================================

@router.get("/feed", response_model=List[PostResponse], tags=["Social Graph"])
async def get_feed(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    graph_service: SocialGraphService = Depends(get_graph_service)
):
    """Get user's activity feed"""
    posts = await graph_service.get_feed(current_user.id, skip, limit)
    return posts

@router.get("/recommendations", response_model=List[dict], tags=["Social Graph"])
async def get_recommendations(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    graph_service: SocialGraphService = Depends(get_graph_service)
):
    """Get user recommendations"""
    users = await graph_service.get_recommendations(current_user.id, limit)
    # Return minimal user info
    return [{"id": u.id, "full_name": u.full_name, "email": u.email} for u in users]

@router.post("/users/{user_id}/follow", response_model=FollowResponse, tags=["Social Graph"])
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    graph_service: SocialGraphService = Depends(get_graph_service)
):
    """Follow a user"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    follow = await graph_service.follow_user(current_user.id, user_id)
    return follow

@router.delete("/users/{user_id}/follow", tags=["Social Graph"])
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    graph_service: SocialGraphService = Depends(get_graph_service)
):
    """Unfollow a user"""
    success = await graph_service.unfollow_user(current_user.id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
    return {"status": "success"}

# =============================================================================
# POSTS & CONTENT
# =============================================================================

@router.post("/posts", response_model=PostResponse, tags=["Social Content"])
async def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Create a new post"""
    # Check profanity
    if moderation_service.check_profanity(post_in.content):
         raise HTTPException(status_code=400, detail="Content contains profanity")

    post = await content_service.create_post(current_user.id, post_in)

    # Update reputation
    await moderation_service.update_reputation(current_user.id, "post_created")

    return post

@router.get("/posts/{post_id}", response_model=PostResponse, tags=["Social Content"])
async def get_post(
    post_id: int,
    content_service: ContentService = Depends(get_content_service)
):
    """Get a single post"""
    post = await content_service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/posts/{post_id}", response_model=PostResponse, tags=["Social Content"])
async def update_post(
    post_id: int,
    post_in: PostUpdate,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Update a post"""
    if post_in.content and moderation_service.check_profanity(post_in.content):
         raise HTTPException(status_code=400, detail="Content contains profanity")

    post = await content_service.update_post(post_id, current_user.id, post_in)
    if not post:
        raise HTTPException(status_code=403, detail="Cannot update post (not found or not owner)")
    return post

@router.delete("/posts/{post_id}", tags=["Social Content"])
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service)
):
    """Delete a post"""
    success = await content_service.delete_post(post_id, current_user.id)
    if not success:
        raise HTTPException(status_code=403, detail="Cannot delete post (not found or not owner)")
    return {"status": "success"}

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, tags=["Social Content"])
async def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Add a comment to a post"""
    if moderation_service.check_profanity(comment_in.content):
         raise HTTPException(status_code=400, detail="Content contains profanity")

    comment = await content_service.create_comment(current_user.id, post_id, comment_in)
    if not comment:
        raise HTTPException(status_code=404, detail="Post not found")
    return comment

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse], tags=["Social Content"])
async def get_comments(
    post_id: int,
    skip: int = 0,
    limit: int = 50,
    content_service: ContentService = Depends(get_content_service)
):
    """Get comments for a post"""
    return await content_service.get_comments(post_id, skip, limit)

@router.get("/trending/hashtags", response_model=List[dict], tags=["Social Content"])
async def get_trending_hashtags(
    limit: int = 10,
    days: int = 7,
    content_service: ContentService = Depends(get_content_service)
):
    """Get trending hashtags"""
    return await content_service.get_trending_hashtags(limit, days)

@router.post("/react", tags=["Social Content"])
async def react_to_content(
    reaction_in: ReactionCreate,
    current_user: User = Depends(get_current_user),
    content_service: ContentService = Depends(get_content_service),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """React to post or comment"""
    result = await content_service.toggle_reaction(current_user.id, reaction_in)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("message"))

    if result.get("action") == "added":
        await moderation_service.update_reputation(current_user.id, "helpful_vote") # Simplified logic

    return result

# =============================================================================
# GROUPS (CROP CIRCLES)
# =============================================================================

@router.post("/groups", response_model=GroupResponse, tags=["Social Groups"])
async def create_group(
    group_in: GroupCreate,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """Create a new group (Crop Circle)"""
    return await group_service.create_group(current_user.id, group_in)

@router.get("/groups", response_model=List[GroupResponse], tags=["Social Groups"])
async def list_groups(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    group_service: GroupService = Depends(get_group_service)
):
    """List groups"""
    return await group_service.get_groups(search, skip, limit)

@router.get("/groups/{group_id}", response_model=GroupResponse, tags=["Social Groups"])
async def get_group(
    group_id: int,
    group_service: GroupService = Depends(get_group_service)
):
    """Get group details"""
    group = await group_service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.post("/groups/{group_id}/join", tags=["Social Groups"])
async def join_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """Join a group"""
    member = await group_service.join_group(current_user.id, group_id)
    if not member:
        raise HTTPException(status_code=400, detail="Could not join group (already member or group not found)")
    return {"status": "success"}

@router.post("/groups/{group_id}/leave", tags=["Social Groups"])
async def leave_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """Leave a group"""
    success = await group_service.leave_group(current_user.id, group_id)
    if not success:
        raise HTTPException(status_code=400, detail="Could not leave group")
    return {"status": "success"}

# =============================================================================
# MODERATION
# =============================================================================

@router.post("/reports", response_model=ReportResponse, tags=["Social Moderation"])
async def create_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_user),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Report content or user"""
    return await moderation_service.create_report(current_user.id, report_in)

@router.get("/reputation/me", response_model=ReputationResponse, tags=["Social Moderation"])
async def get_my_reputation(
    current_user: User = Depends(get_current_user),
    moderation_service: ModerationService = Depends(get_moderation_service)
):
    """Get my reputation"""
    return await moderation_service.get_reputation(current_user.id)
