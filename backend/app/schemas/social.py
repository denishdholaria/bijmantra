"""
Social Graph Schemas
Pydantic models for social features
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.social import PostType, ReactionType, TargetType, GroupRole, ReportStatus

# Shared
class UserSummary(BaseModel):
    id: int
    full_name: Optional[str] = None
    # avatar_url: Optional[str] = None # If we had it on User model or UserProfile

    model_config = ConfigDict(from_attributes=True)

# Follows
class FollowCreate(BaseModel):
    followed_id: int

class FollowResponse(BaseModel):
    follower_id: int
    followed_id: int
    created_at: Optional[datetime] = None # UserFollow doesn't have it explicitly in my model, I should have added it.
    # Base model has created_at, but UserFollow inherited BaseModel? Yes.

    model_config = ConfigDict(from_attributes=True)

# Reactions
class ReactionCreate(BaseModel):
    target_id: int
    target_type: TargetType
    reaction_type: ReactionType = ReactionType.LIKE

class ReactionResponse(BaseModel):
    id: int
    user_id: int
    target_id: int
    target_type: str
    reaction_type: str

    model_config = ConfigDict(from_attributes=True)

# Comments
class CommentBase(BaseModel):
    content: str
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    post_id: int
    author_id: int
    author: Optional[UserSummary] = None
    likes_count: int
    created_at: datetime
    updated_at: datetime

    # Nested comments are usually fetched separately or up to a depth
    # We'll just return parent_id

    model_config = ConfigDict(from_attributes=True)

# Posts
class PostBase(BaseModel):
    content: Optional[str] = None
    media_urls: List[str] = []
    post_type: PostType = PostType.TEXT
    hashtags: List[str] = []
    location_name: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None

    # References
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None

    group_id: Optional[int] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None

class PostResponse(PostBase):
    id: int
    author_id: int
    author: Optional[UserSummary] = None

    likes_count: int
    comments_count: int
    share_count: int
    view_count: int

    created_at: datetime
    updated_at: datetime

    # We might want to include the user's reaction if authenticated
    user_reaction: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Reports
class ReportCreate(BaseModel):
    target_id: int
    target_type: TargetType
    reason: str
    description: Optional[str] = None

class ReportResponse(ReportCreate):
    id: int
    reporter_id: int
    status: ReportStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Groups
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    crop_type: Optional[str] = None
    is_private: bool = False

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_private: Optional[bool] = None

class GroupResponse(GroupBase):
    id: int
    creator_id: int
    member_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GroupMemberResponse(BaseModel):
    group_id: int
    user_id: int
    user: Optional[UserSummary] = None
    role: GroupRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Reputation
class ReputationResponse(BaseModel):
    user_id: int
    score: int
    level: str
    posts_count: int
    helpful_votes: int

    model_config = ConfigDict(from_attributes=True)
