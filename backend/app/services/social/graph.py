"""
Social Graph Service
Follows, Feed, Recommendations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.social import UserFollow, Post
from app.models.core import User

class SocialGraphService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def follow_user(self, follower_id: int, followed_id: int) -> UserFollow:
        if follower_id == followed_id:
            raise ValueError("Cannot follow yourself")

        # Check if already following
        stmt = select(UserFollow).where(
            UserFollow.follower_id == follower_id,
            UserFollow.followed_id == followed_id
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create follow
        follow = UserFollow(follower_id=follower_id, followed_id=followed_id)
        self.db.add(follow)
        await self.db.commit()
        await self.db.refresh(follow)
        return follow

    async def unfollow_user(self, follower_id: int, followed_id: int) -> bool:
        stmt = select(UserFollow).where(
            UserFollow.follower_id == follower_id,
            UserFollow.followed_id == followed_id
        )
        result = await self.db.execute(stmt)
        follow = result.scalar_one_or_none()

        if follow:
            await self.db.delete(follow)
            await self.db.commit()
            return True
        return False

    async def get_followers(self, user_id: int, skip: int = 0, limit: int = 20) -> List[User]:
        stmt = select(User).join(UserFollow, UserFollow.follower_id == User.id)\
            .where(UserFollow.followed_id == user_id)\
            .offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_following(self, user_id: int, skip: int = 0, limit: int = 20) -> List[User]:
        stmt = select(User).join(UserFollow, UserFollow.followed_id == User.id)\
            .where(UserFollow.follower_id == user_id)\
            .offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_following_ids(self, user_id: int) -> List[int]:
        stmt = select(UserFollow.followed_id).where(UserFollow.follower_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_feed(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Post]:
        # Get list of users the current user follows
        following_ids = await self.get_following_ids(user_id)

        # Add own id to see own posts? Usually yes.
        following_ids.append(user_id)

        # Query posts
        stmt = select(Post).where(Post.author_id.in_(following_ids))\
            .options(selectinload(Post.author))\
            .options(selectinload(Post.reactions))\
            .order_by(desc(Post.created_at))\
            .offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_recommendations(self, user_id: int, limit: int = 5) -> List[User]:
        # Simple recommendation: Users with most followers who I don't follow yet
        following_ids = await self.get_following_ids(user_id)
        following_ids.append(user_id) # Exclude self

        subquery = select(UserFollow.followed_id, func.count(UserFollow.follower_id).label("count"))\
            .group_by(UserFollow.followed_id)\
            .order_by(desc("count"))\
            .subquery()

        stmt = select(User).join(subquery, User.id == subquery.c.followed_id)\
            .where(User.id.notin_(following_ids))\
            .limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()
