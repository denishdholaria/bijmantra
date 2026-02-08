"""
Social Content Service
Posts, Comments, Hashtags
"""

import re
from datetime import datetime, timedelta, timezone
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.social import Post, Comment, Reaction, PostType, ReactionType, TargetType
from app.schemas.social import PostCreate, PostUpdate, CommentCreate, ReactionCreate

class ContentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _extract_hashtags(self, content: str) -> List[str]:
        if not content:
            return []
        return re.findall(r"#(\w+)", content)

    async def create_post(self, user_id: int, post_in: PostCreate) -> Post:
        # Extract hashtags if not provided or supplement them
        extracted = self._extract_hashtags(post_in.content)
        hashtags = list(set((post_in.hashtags or []) + extracted))

        post = Post(
            author_id=user_id,
            content=post_in.content,
            media_urls=post_in.media_urls,
            post_type=post_in.post_type,
            hashtags=hashtags,
            location_name=post_in.location_name,
            coordinates=post_in.coordinates,
            reference_id=post_in.reference_id,
            reference_type=post_in.reference_type,
            group_id=post_in.group_id
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def get_post(self, post_id: int) -> Optional[Post]:
        stmt = select(Post).where(Post.id == post_id)\
            .options(selectinload(Post.author))\
            .options(selectinload(Post.reactions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_post(self, post_id: int, user_id: int, post_in: PostUpdate) -> Optional[Post]:
        post = await self.get_post(post_id)
        if not post or post.author_id != user_id:
            return None

        update_data = post_in.model_dump(exclude_unset=True)

        # If content changed, re-extract hashtags
        if "content" in update_data:
            extracted = self._extract_hashtags(update_data["content"])
            # Merge with existing manually added hashtags? Or just replace?
            # For simplicity, we'll replace the auto-extracted ones but user might have manually added some via API.
            # Here we assume API passes full list if they want to update tags.
            # If hashtags not in update_data, we update them based on content.
            if "hashtags" not in update_data:
                update_data["hashtags"] = extracted

        for field, value in update_data.items():
            setattr(post, field, value)

        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def delete_post(self, post_id: int, user_id: int) -> bool:
        post = await self.get_post(post_id)
        if not post or post.author_id != user_id:
            return False

        await self.db.delete(post)
        await self.db.commit()
        return True

    async def create_comment(self, user_id: int, post_id: int, comment_in: CommentCreate) -> Optional[Comment]:
        # Verify post exists (lightweight check)
        stmt = select(Post.id).where(Post.id == post_id)
        result = await self.db.execute(stmt)
        if not result.scalar_one_or_none():
            return None

        comment = Comment(
            post_id=post_id,
            author_id=user_id,
            content=comment_in.content,
            parent_id=comment_in.parent_id
        )
        self.db.add(comment)

        # Atomic update post comments count
        await self.db.execute(
            update(Post).where(Post.id == post_id).values(comments_count=Post.comments_count + 1)
        )

        await self.db.commit()
        await self.db.refresh(comment)

        # Eager load author for response
        stmt = select(Comment).where(Comment.id == comment.id).options(selectinload(Comment.author))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_comments(self, post_id: int, skip: int = 0, limit: int = 50) -> List[Comment]:
        stmt = select(Comment).where(Comment.post_id == post_id)\
            .options(selectinload(Comment.author))\
            .order_by(Comment.created_at)\
            .offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_trending_hashtags(self, limit: int = 10, days: int = 7) -> List[dict]:
        # Simple Python-based aggregation for compatibility
        # Fetch posts from last N days
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(Post.hashtags).where(Post.created_at >= cutoff).limit(1000)

        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        # Flatten and count
        all_tags = []
        for tags in rows:
            if tags:
                all_tags.extend(tags)

        counter = Counter(all_tags)
        most_common = counter.most_common(limit)

        return [{"tag": tag, "count": count} for tag, count in most_common]

    async def toggle_reaction(self, user_id: int, reaction_in: ReactionCreate) -> dict:
        # Check if already reacted
        stmt = select(Reaction).where(
            Reaction.user_id == user_id,
            Reaction.target_id == reaction_in.target_id,
            Reaction.target_type == reaction_in.target_type
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        target_model = Post if reaction_in.target_type == TargetType.POST else Comment

        # Verify target exists
        target_stmt = select(target_model.id).where(target_model.id == reaction_in.target_id)
        target_res = await self.db.execute(target_stmt)
        if not target_res.scalar_one_or_none():
             return {"status": "error", "message": "Target not found"}

        if existing:
            # If same type, remove (toggle off)
            if existing.reaction_type == reaction_in.reaction_type:
                await self.db.delete(existing)
                # Atomic decrement
                await self.db.execute(
                    update(target_model).where(target_model.id == reaction_in.target_id)
                    .values(likes_count=func.greatest(0, target_model.likes_count - 1))
                )
                action = "removed"
            else:
                # Change reaction type
                existing.reaction_type = reaction_in.reaction_type
                action = "updated"
                # Count remains same
        else:
            # Add reaction
            reaction = Reaction(
                user_id=user_id,
                target_id=reaction_in.target_id,
                target_type=reaction_in.target_type,
                reaction_type=reaction_in.reaction_type
            )
            self.db.add(reaction)
            # Atomic increment
            await self.db.execute(
                update(target_model).where(target_model.id == reaction_in.target_id)
                .values(likes_count=target_model.likes_count + 1)
            )
            action = "added"

        await self.db.commit()

        # Get updated count
        count_stmt = select(target_model.likes_count).where(target_model.id == reaction_in.target_id)
        count_res = await self.db.execute(count_stmt)
        new_count = count_res.scalar_one()

        return {"status": "success", "action": action, "likes_count": new_count}
