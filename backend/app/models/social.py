"""
Social Graph Models
User relationships, Content (Posts, Comments), Groups, Moderation
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Boolean, DateTime, Enum, Table
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum
from datetime import datetime, timezone

# Enums
class PostType(str, enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    OBSERVATION = "observation"
    MARKET = "market"

class ReactionType(str, enum.Enum):
    LIKE = "like"
    LOVE = "love"
    INSIGHTFUL = "insightful"
    CELEBRATE = "celebrate"

class TargetType(str, enum.Enum):
    POST = "post"
    COMMENT = "comment"
    USER = "user"
    GROUP = "group"

class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class GroupRole(str, enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"

# Join table for User Follows
# We can use a model for this to store extra metadata like 'created_at'
class UserFollow(BaseModel):
    """User following relationship"""
    __tablename__ = "user_follows"

    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    followed_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    follower = relationship("User", foreign_keys=[follower_id])
    followed = relationship("User", foreign_keys=[followed_id])

    __table_args__ = (
        {'extend_existing': True}
    )

class Post(BaseModel):
    """Social Feed Post"""
    __tablename__ = "posts"

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Content
    content = Column(Text)
    media_urls = Column(JSON, default=list) # List of image URLs
    post_type = Column(String(50), default=PostType.TEXT) # text, photo, observation, market

    # Metadata
    hashtags = Column(JSON, default=list)
    location_name = Column(String(255))
    coordinates = Column(JSON) # {lat, lng}

    # Integration with other modules (e.g. Observation Report ID)
    reference_id = Column(String(255))
    reference_type = Column(String(50))

    # Metrics
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Context (e.g. posted in a group)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)

    # Relationships
    author = relationship("User")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship("Reaction", primaryjoin="and_(Reaction.target_id==Post.id, Reaction.target_type=='post')", foreign_keys="[Reaction.target_id]", cascade="all, delete-orphan", viewonly=True)

    __table_args__ = (
        {'extend_existing': True}
    )

class Comment(BaseModel):
    """Post Comment"""
    __tablename__ = "comments"

    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True) # Nested comments

    content = Column(Text, nullable=False)

    # Metrics
    likes_count = Column(Integer, default=0)

    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User")
    parent = relationship("Comment", remote_side="[Comment.id]", backref="replies")

    __table_args__ = (
        {'extend_existing': True}
    )

class Reaction(BaseModel):
    """User reactions (Like, etc.)"""
    __tablename__ = "reactions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    target_id = Column(Integer, nullable=False, index=True)
    target_type = Column(String(20), nullable=False) # post, comment
    reaction_type = Column(String(20), default=ReactionType.LIKE)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        {'extend_existing': True}
    )

class Report(BaseModel):
    """Content/User Reporting"""
    __tablename__ = "reports"

    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    target_id = Column(Integer, nullable=False)
    target_type = Column(String(20), nullable=False) # post, comment, user, group

    reason = Column(String(50), nullable=False) # spam, harassment, etc.
    description = Column(Text)

    status = Column(String(20), default=ReportStatus.PENDING)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text)

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])

    __table_args__ = (
        {'extend_existing': True}
    )

class Reputation(BaseModel):
    """User Reputation (Karma)"""
    __tablename__ = "reputation"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    score = Column(Integer, default=0)
    level = Column(String(50), default="Newcomer")

    # Breakdown
    posts_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        {'extend_existing': True}
    )

class Group(BaseModel):
    """Crop Circles (Groups)"""
    __tablename__ = "groups"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    cover_image_url = Column(String(500))

    crop_type = Column(String(100), index=True) # Optional constraint
    is_private = Column(Boolean, default=False)

    creator_id = Column(Integer, ForeignKey("users.id"))

    member_count = Column(Integer, default=0)

    # Relationships
    creator = relationship("User")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")

    __table_args__ = (
        {'extend_existing': True}
    )

class GroupMember(BaseModel):
    """Group Membership"""
    __tablename__ = "group_members"

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    role = Column(String(20), default=GroupRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        {'extend_existing': True}
    )
