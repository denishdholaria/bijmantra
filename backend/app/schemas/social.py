"""
Social Graph Schemas
Pydantic models for social features
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.social import GroupRole, PostType, ReactionType, ReportStatus, TargetType


# Shared
class UserSummary(BaseModel):
    id: int
    full_name: str | None = None
    # avatar_url: Optional[str] = None # If we had it on User model or UserProfile

    model_config = ConfigDict(from_attributes=True)

# Follows
class FollowCreate(BaseModel):
    followed_id: int

class FollowResponse(BaseModel):
    follower_id: int
    followed_id: int
    created_at: datetime | None = None # UserFollow doesn't have it explicitly in my model, I should have added it.
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
    parent_id: int | None = None

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    post_id: int
    author_id: int
    author: UserSummary | None = None
    likes_count: int
    created_at: datetime
    updated_at: datetime

    # Nested comments are usually fetched separately or up to a depth
    # We'll just return parent_id

    model_config = ConfigDict(from_attributes=True)

# Posts
class PostBase(BaseModel):
    content: str | None = None
    media_urls: list[str] = []
    post_type: PostType = PostType.TEXT
    hashtags: list[str] = []
    location_name: str | None = None
    coordinates: dict[str, float] | None = None

    # References
    reference_id: str | None = None
    reference_type: str | None = None

    group_id: int | None = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    content: str | None = None
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None

class PostResponse(PostBase):
    id: int
    author_id: int
    author: UserSummary | None = None

    likes_count: int
    comments_count: int
    share_count: int
    view_count: int

    created_at: datetime
    updated_at: datetime

    # We might want to include the user's reaction if authenticated
    user_reaction: str | None = None

    model_config = ConfigDict(from_attributes=True)

# Reports
class ReportCreate(BaseModel):
    target_id: int
    target_type: TargetType
    reason: str
    description: str | None = None

class ReportResponse(ReportCreate):
    id: int
    reporter_id: int
    status: ReportStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Groups
class GroupBase(BaseModel):
    name: str
    description: str | None = None
    cover_image_url: str | None = None
    crop_type: str | None = None
    is_private: bool = False

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    cover_image_url: str | None = None
    is_private: bool | None = None

class GroupResponse(GroupBase):
    id: int
    creator_id: int
    member_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GroupMemberResponse(BaseModel):
    group_id: int
    user_id: int
    user: UserSummary | None = None
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
