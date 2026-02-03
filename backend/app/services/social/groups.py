"""
Social Groups Service (Crop Circles)
Groups management
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, update
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.social import Group, GroupMember, GroupRole
from app.schemas.social import GroupCreate, GroupUpdate

class GroupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_group(self, user_id: int, group_in: GroupCreate) -> Group:
        group = Group(
            name=group_in.name,
            description=group_in.description,
            cover_image_url=group_in.cover_image_url,
            crop_type=group_in.crop_type,
            is_private=group_in.is_private,
            creator_id=user_id,
            member_count=1 # Creator is first member
        )
        self.db.add(group)
        await self.db.flush() # Get ID

        # Add creator as admin
        member = GroupMember(
            group_id=group.id,
            user_id=user_id,
            role=GroupRole.ADMIN
        )
        self.db.add(member)

        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_group(self, group_id: int) -> Optional[Group]:
        stmt = select(Group).where(Group.id == group_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_groups(self, search: str = None, skip: int = 0, limit: int = 20) -> List[Group]:
        stmt = select(Group)
        if search:
            stmt = stmt.where(
                or_(
                    Group.name.ilike(f"%{search}%"),
                    Group.description.ilike(f"%{search}%"),
                    Group.crop_type.ilike(f"%{search}%")
                )
            )
        stmt = stmt.order_by(desc(Group.member_count)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_group(self, group_id: int, user_id: int, group_in: GroupUpdate) -> Optional[Group]:
        group = await self.get_group(group_id)
        if not group or group.creator_id != user_id:
            # Also check if user is admin
            return None

        update_data = group_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)

        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def join_group(self, user_id: int, group_id: int) -> Optional[GroupMember]:
        # Verify group exists
        stmt = select(Group.id).where(Group.id == group_id)
        result = await self.db.execute(stmt)
        if not result.scalar_one_or_none():
            return None

        # Check if already member
        stmt = select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            return None # Already joined

        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=GroupRole.MEMBER
        )
        self.db.add(member)

        # Atomic increment
        await self.db.execute(
            update(Group).where(Group.id == group_id).values(member_count=Group.member_count + 1)
        )

        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def leave_group(self, user_id: int, group_id: int) -> bool:
        stmt = select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()

        if member:
            await self.db.delete(member)

            # Atomic decrement
            await self.db.execute(
                update(Group).where(Group.id == group_id)
                .values(member_count=func.greatest(0, Group.member_count - 1))
            )

            await self.db.commit()
            return True
        return False

    async def get_members(self, group_id: int, skip: int = 0, limit: int = 20) -> List[GroupMember]:
        stmt = select(GroupMember).where(GroupMember.group_id == group_id)\
            .options(selectinload(GroupMember.user))\
            .offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
