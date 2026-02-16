"""
Crossing Planner Service
Manages planned crosses between germplasm

Converted to database queries per Zero Mock Data Policy (Session 77).
Queries PlannedCross and Germplasm tables for real data.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.germplasm import PlannedCross, Germplasm


class CrossingPlannerService:
    """Service for managing crossing plans.
    
    All methods are async and require database session.
    Queries PlannedCross table for real data.
    """

    async def list_crosses(
        self,
        db: AsyncSession,
        organization_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        season: Optional[str] = None,
        breeder: Optional[str] = None,
        page: int = 0,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List planned crosses with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            status: Filter by status (planned, scheduled, in_progress, completed, failed)
            priority: Filter by priority (high, medium, low)
            season: Filter by season
            breeder: Filter by breeder name (partial match)
            page: Page number (0-indexed)
            page_size: Number of results per page
            
        Returns:
            Paginated list of planned crosses
        """
        # Build query
        stmt = select(PlannedCross).where(
            PlannedCross.organization_id == organization_id
        ).options(
            selectinload(PlannedCross.parent1),
            selectinload(PlannedCross.parent2),
        )

        # Apply filters
        if status:
            stmt = stmt.where(PlannedCross.status == status.upper())

        # Note: priority, season, breeder stored in additional_info JSON
        # These filters require JSON querying which varies by database

        # Count total
        count_stmt = select(func.count()).select_from(PlannedCross).where(
            PlannedCross.organization_id == organization_id
        )
        if status:
            count_stmt = count_stmt.where(PlannedCross.status == status.upper())

        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.offset(page * page_size).limit(page_size)
        stmt = stmt.order_by(PlannedCross.created_at.desc())

        result = await db.execute(stmt)
        crosses = result.scalars().all()

        # Transform to response format
        data = []
        for cross in crosses:
            additional = cross.additional_info or {}
            data.append({
                "crossId": cross.planned_cross_db_id or str(cross.id),
                "crossName": cross.planned_cross_name,
                "femaleParentId": str(cross.parent1_db_id) if cross.parent1_db_id else None,
                "femaleParentName": cross.parent1.germplasm_name if cross.parent1 else None,
                "maleParentId": str(cross.parent2_db_id) if cross.parent2_db_id else None,
                "maleParentName": cross.parent2.germplasm_name if cross.parent2 else None,
                "objective": additional.get("objective", ""),
                "priority": additional.get("priority", "medium"),
                "targetDate": additional.get("targetDate", ""),
                "status": (cross.status or "PLANNED").lower(),
                "expectedProgeny": cross.number_of_progeny or 0,
                "actualProgeny": additional.get("actualProgeny", 0),
                "crossType": cross.cross_type or "single",
                "season": additional.get("season", ""),
                "location": additional.get("location", ""),
                "breeder": additional.get("breeder", ""),
                "notes": additional.get("notes", ""),
                "created": cross.created_at.strftime("%Y-%m-%d") if cross.created_at else None,
            })

        return {
            "data": data,
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": (total + page_size - 1) // page_size if total > 0 else 0,
            },
        }

    async def get_cross(
        self,
        db: AsyncSession,
        organization_id: int,
        cross_id: str,
    ) -> Optional[Dict]:
        """Get a single cross by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            cross_id: Cross ID (planned_cross_db_id or numeric id)
            
        Returns:
            Cross data or None if not found
        """
        stmt = select(PlannedCross).where(
            and_(
                PlannedCross.organization_id == organization_id,
                or_(
                    PlannedCross.planned_cross_db_id == cross_id,
                    PlannedCross.id == int(cross_id) if cross_id.isdigit() else False,
                )
            )
        ).options(
            selectinload(PlannedCross.parent1),
            selectinload(PlannedCross.parent2),
        )

        result = await db.execute(stmt)
        cross = result.scalar_one_or_none()

        if not cross:
            return None

        additional = cross.additional_info or {}
        return {
            "crossId": cross.planned_cross_db_id or str(cross.id),
            "crossName": cross.planned_cross_name,
            "femaleParentId": str(cross.parent1_db_id) if cross.parent1_db_id else None,
            "femaleParentName": cross.parent1.germplasm_name if cross.parent1 else None,
            "maleParentId": str(cross.parent2_db_id) if cross.parent2_db_id else None,
            "maleParentName": cross.parent2.germplasm_name if cross.parent2 else None,
            "objective": additional.get("objective", ""),
            "priority": additional.get("priority", "medium"),
            "targetDate": additional.get("targetDate", ""),
            "status": (cross.status or "PLANNED").lower(),
            "expectedProgeny": cross.number_of_progeny or 0,
            "actualProgeny": additional.get("actualProgeny", 0),
            "crossType": cross.cross_type or "single",
            "season": additional.get("season", ""),
            "location": additional.get("location", ""),
            "breeder": additional.get("breeder", ""),
            "notes": additional.get("notes", ""),
            "created": cross.created_at.strftime("%Y-%m-%d") if cross.created_at else None,
        }

    async def create_cross(
        self,
        db: AsyncSession,
        organization_id: int,
        data: Dict,
    ) -> Dict:
        """Create a new planned cross.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            data: Cross data including parent IDs, objective, priority, etc.
            
        Returns:
            Created cross data
        """
        # Generate cross ID
        count_result = await db.execute(
            select(func.count()).select_from(PlannedCross).where(
                PlannedCross.organization_id == organization_id
            )
        )
        count = count_result.scalar() or 0
        cross_db_id = f"CX{count + 1:03d}"

        # Get parent names if IDs provided
        female_name = data.get("femaleParentName", "Unknown")
        male_name = data.get("maleParentName", "Unknown")

        if data.get("femaleParentId"):
            female_result = await db.execute(
                select(Germplasm).where(Germplasm.id == int(data["femaleParentId"]))
            )
            female = female_result.scalar_one_or_none()
            if female:
                female_name = female.germplasm_name

        if data.get("maleParentId"):
            male_result = await db.execute(
                select(Germplasm).where(Germplasm.id == int(data["maleParentId"]))
            )
            male = male_result.scalar_one_or_none()
            if male:
                male_name = male.germplasm_name

        # Create cross name if not provided
        cross_name = data.get("crossName", f"{female_name} × {male_name}")

        # Create PlannedCross record
        cross = PlannedCross(
            organization_id=organization_id,
            planned_cross_db_id=cross_db_id,
            planned_cross_name=cross_name,
            cross_type=data.get("crossType", "single"),
            parent1_db_id=int(data["femaleParentId"]) if data.get("femaleParentId") else None,
            parent1_type="FEMALE",
            parent2_db_id=int(data["maleParentId"]) if data.get("maleParentId") else None,
            parent2_type="MALE",
            number_of_progeny=data.get("expectedProgeny", 50),
            status="PLANNED",
            additional_info={
                "objective": data.get("objective", ""),
                "priority": data.get("priority", "medium"),
                "targetDate": data.get("targetDate", ""),
                "season": data.get("season", ""),
                "location": data.get("location", ""),
                "breeder": data.get("breeder", ""),
                "notes": data.get("notes", ""),
                "actualProgeny": 0,
            },
        )

        db.add(cross)
        await db.commit()
        await db.refresh(cross)

        return {
            "crossId": cross.planned_cross_db_id,
            "crossName": cross.planned_cross_name,
            "femaleParentId": str(cross.parent1_db_id) if cross.parent1_db_id else None,
            "femaleParentName": female_name,
            "maleParentId": str(cross.parent2_db_id) if cross.parent2_db_id else None,
            "maleParentName": male_name,
            "objective": data.get("objective", ""),
            "priority": data.get("priority", "medium"),
            "targetDate": data.get("targetDate", ""),
            "status": "planned",
            "expectedProgeny": data.get("expectedProgeny", 50),
            "actualProgeny": 0,
            "crossType": data.get("crossType", "single"),
            "season": data.get("season", ""),
            "location": data.get("location", ""),
            "breeder": data.get("breeder", ""),
            "notes": data.get("notes", ""),
            "created": datetime.now(UTC).strftime("%Y-%m-%d"),
        }

    async def update_cross(
        self,
        db: AsyncSession,
        organization_id: int,
        cross_id: str,
        data: Dict,
    ) -> Optional[Dict]:
        """Update a cross.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            cross_id: Cross ID to update
            data: Fields to update
            
        Returns:
            Updated cross data or None if not found
        """
        stmt = select(PlannedCross).where(
            and_(
                PlannedCross.organization_id == organization_id,
                or_(
                    PlannedCross.planned_cross_db_id == cross_id,
                    PlannedCross.id == int(cross_id) if cross_id.isdigit() else False,
                )
            )
        )

        result = await db.execute(stmt)
        cross = result.scalar_one_or_none()

        if not cross:
            return None

        # Update fields
        if "crossType" in data:
            cross.cross_type = data["crossType"]
        if "expectedProgeny" in data:
            cross.number_of_progeny = data["expectedProgeny"]

        # Update additional_info
        additional = cross.additional_info or {}
        for key in ["objective", "priority", "targetDate", "season", "location", "breeder", "notes"]:
            if key in data:
                additional[key] = data[key]
        cross.additional_info = additional

        await db.commit()
        await db.refresh(cross)

        return await self.get_cross(db, organization_id, cross_id)

    async def update_status(
        self,
        db: AsyncSession,
        organization_id: int,
        cross_id: str,
        status: str,
        actual_progeny: Optional[int] = None,
    ) -> Optional[Dict]:
        """Update cross status.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            cross_id: Cross ID to update
            status: New status (planned, scheduled, in_progress, completed, failed)
            actual_progeny: Actual progeny count (for completed crosses)
            
        Returns:
            Updated cross data or None if not found
        """
        stmt = select(PlannedCross).where(
            and_(
                PlannedCross.organization_id == organization_id,
                or_(
                    PlannedCross.planned_cross_db_id == cross_id,
                    PlannedCross.id == int(cross_id) if cross_id.isdigit() else False,
                )
            )
        )

        result = await db.execute(stmt)
        cross = result.scalar_one_or_none()

        if not cross:
            return None

        cross.status = status.upper()

        additional = cross.additional_info or {}
        if status.lower() == "completed":
            additional["completedDate"] = datetime.now(UTC).strftime("%Y-%m-%d")
            if actual_progeny is not None:
                additional["actualProgeny"] = actual_progeny
        cross.additional_info = additional

        await db.commit()
        await db.refresh(cross)

        return await self.get_cross(db, organization_id, cross_id)

    async def delete_cross(
        self,
        db: AsyncSession,
        organization_id: int,
        cross_id: str,
    ) -> bool:
        """Delete a cross.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            cross_id: Cross ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        stmt = select(PlannedCross).where(
            and_(
                PlannedCross.organization_id == organization_id,
                or_(
                    PlannedCross.planned_cross_db_id == cross_id,
                    PlannedCross.id == int(cross_id) if cross_id.isdigit() else False,
                )
            )
        )

        result = await db.execute(stmt)
        cross = result.scalar_one_or_none()

        if not cross:
            return False

        await db.delete(cross)
        await db.commit()
        return True

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict:
        """Get crossing statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            
        Returns:
            Statistics summary
        """
        # Get all crosses for this organization
        stmt = select(PlannedCross).where(
            PlannedCross.organization_id == organization_id
        )
        result = await db.execute(stmt)
        crosses = result.scalars().all()

        if not crosses:
            return {
                "total": 0,
                "planned": 0,
                "scheduled": 0,
                "inProgress": 0,
                "completed": 0,
                "failed": 0,
                "totalExpectedProgeny": 0,
                "totalActualProgeny": 0,
                "byPriority": {"high": 0, "medium": 0, "low": 0},
            }

        # Calculate statistics
        stats = {
            "total": len(crosses),
            "planned": 0,
            "scheduled": 0,
            "inProgress": 0,
            "completed": 0,
            "failed": 0,
            "totalExpectedProgeny": 0,
            "totalActualProgeny": 0,
            "byPriority": {"high": 0, "medium": 0, "low": 0},
        }

        for cross in crosses:
            status = (cross.status or "PLANNED").upper()
            if status == "PLANNED":
                stats["planned"] += 1
            elif status == "SCHEDULED":
                stats["scheduled"] += 1
            elif status == "IN_PROGRESS":
                stats["inProgress"] += 1
            elif status == "COMPLETED":
                stats["completed"] += 1
            elif status == "FAILED":
                stats["failed"] += 1

            stats["totalExpectedProgeny"] += cross.number_of_progeny or 0

            additional = cross.additional_info or {}
            stats["totalActualProgeny"] += additional.get("actualProgeny", 0)

            priority = additional.get("priority", "medium").lower()
            if priority in stats["byPriority"]:
                stats["byPriority"][priority] += 1

        return stats

    async def list_germplasm(
        self,
        db: AsyncSession,
        organization_id: int,
        search: Optional[str] = None,
    ) -> List[Dict]:
        """List available germplasm for crossing.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            search: Optional search term for germplasm name
            
        Returns:
            List of germplasm available for crossing
        """
        stmt = select(Germplasm).where(
            Germplasm.organization_id == organization_id
        )

        if search:
            stmt = stmt.where(
                Germplasm.germplasm_name.ilike(f"%{search}%")
            )

        stmt = stmt.limit(100)  # Limit results for performance

        result = await db.execute(stmt)
        germplasm_list = result.scalars().all()

        return [
            {
                "id": str(g.id),
                "name": g.germplasm_name,
                "type": g.germplasm_type or "unknown",
                "traits": [],  # Would need trait associations
            }
            for g in germplasm_list
        ]


# Singleton instance
crossing_planner_service = CrossingPlannerService()
