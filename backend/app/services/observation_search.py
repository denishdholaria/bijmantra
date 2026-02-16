"""
Observation Search Service

Advanced observation search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload


class ObservationSearchService:
    """Service for advanced observation search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        trait: Optional[str] = None,
        study_id: Optional[int] = None,
        germplasm_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search observations with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query
            trait: Filter by trait/variable name
            study_id: Filter by study
            germplasm_id: Filter by germplasm
            date_from: Filter observations after this date
            date_to: Filter observations before this date
            limit: Maximum results to return
            
        Returns:
            List of observation dictionaries, empty if no data
        """
        from app.models.phenotyping import Observation, ObservationVariable, ObservationUnit
        from app.models.germplasm import Germplasm
        from app.models.core import Study

        stmt = (
            select(Observation)
            .options(
                selectinload(Observation.observation_variable),
                selectinload(Observation.observation_unit),
                selectinload(Observation.germplasm),
                selectinload(Observation.study)
            )
            .where(Observation.organization_id == organization_id)
            .order_by(Observation.observation_time_stamp.desc())
            .limit(limit)
        )

        if study_id:
            stmt = stmt.where(Observation.study_id == study_id)

        if germplasm_id:
            stmt = stmt.where(Observation.germplasm_id == germplasm_id)

        if date_from:
            stmt = stmt.where(Observation.observation_time_stamp >= date_from)

        if date_to:
            stmt = stmt.where(Observation.observation_time_stamp <= date_to)

        result = await db.execute(stmt)
        observations = result.scalars().all()

        results = []
        for o in observations:
            # Filter by trait name if specified
            if trait and o.observation_variable:
                var_name = o.observation_variable.observation_variable_name or ""
                trait_name = o.observation_variable.trait_name or ""
                if trait.lower() not in var_name.lower() and trait.lower() not in trait_name.lower():
                    continue

            # Filter by query if specified
            if query:
                q = query.lower()
                match = False
                if o.observation_variable:
                    if q in (o.observation_variable.observation_variable_name or "").lower():
                        match = True
                if o.germplasm:
                    if q in (o.germplasm.germplasm_name or "").lower():
                        match = True
                if o.value and q in o.value.lower():
                    match = True
                if not match:
                    continue

            results.append({
                "id": str(o.id),
                "observation_db_id": o.observation_db_id,
                "value": o.value,
                "timestamp": o.observation_time_stamp,
                "collector": o.collector,
                "trait": {
                    "id": str(o.observation_variable.id),
                    "name": o.observation_variable.observation_variable_name,
                    "trait_name": o.observation_variable.trait_name,
                    "data_type": o.observation_variable.data_type,
                    "scale": o.observation_variable.scale_name,
                } if o.observation_variable else None,
                "germplasm": {
                    "id": str(o.germplasm.id),
                    "name": o.germplasm.germplasm_name,
                    "accession": o.germplasm.accession_number,
                } if o.germplasm else None,
                "study": {
                    "id": str(o.study.id),
                    "name": o.study.study_name,
                } if o.study else None,
                "observation_unit": {
                    "id": str(o.observation_unit.id),
                    "name": o.observation_unit.observation_unit_name,
                    "level": o.observation_unit.observation_level,
                } if o.observation_unit else None,
            })

        return results

    async def get_by_study(
        self,
        db: AsyncSession,
        organization_id: int,
        study_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all observations for a study.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            study_id: Study ID
            limit: Maximum results
            
        Returns:
            List of observation dictionaries
        """
        return await self.search(
            db=db,
            organization_id=organization_id,
            study_id=study_id,
            limit=limit
        )

    async def get_by_germplasm(
        self,
        db: AsyncSession,
        organization_id: int,
        germplasm_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all observations for a germplasm.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            germplasm_id: Germplasm ID
            limit: Maximum results
            
        Returns:
            List of observation dictionaries
        """
        return await self.search(
            db=db,
            organization_id=organization_id,
            germplasm_id=germplasm_id,
            limit=limit
        )

    async def get_trait_summary(
        self,
        db: AsyncSession,
        organization_id: int,
        trait_id: int
    ) -> Dict[str, Any]:
        """Get summary statistics for a trait across all observations.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trait_id: Observation variable ID
            
        Returns:
            Summary statistics dictionary
        """
        from app.models.phenotyping import Observation, ObservationVariable

        # Get trait info
        var_stmt = (
            select(ObservationVariable)
            .where(ObservationVariable.organization_id == organization_id)
            .where(ObservationVariable.id == trait_id)
        )
        var_result = await db.execute(var_stmt)
        variable = var_result.scalar_one_or_none()

        if not variable:
            return {"error": "Trait not found"}

        # Count observations
        count_stmt = (
            select(func.count(Observation.id))
            .where(Observation.organization_id == organization_id)
            .where(Observation.observation_variable_id == trait_id)
        )
        count_result = await db.execute(count_stmt)
        count = count_result.scalar() or 0

        # Get distinct germplasm count
        germplasm_stmt = (
            select(func.count(func.distinct(Observation.germplasm_id)))
            .where(Observation.organization_id == organization_id)
            .where(Observation.observation_variable_id == trait_id)
        )
        germplasm_result = await db.execute(germplasm_stmt)
        germplasm_count = germplasm_result.scalar() or 0

        return {
            "trait_id": str(trait_id),
            "trait_name": variable.observation_variable_name,
            "data_type": variable.data_type,
            "observation_count": count,
            "germplasm_count": germplasm_count,
        }

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get observation statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.phenotyping import Observation, ObservationVariable

        # Total observations
        total_stmt = (
            select(func.count(Observation.id))
            .where(Observation.organization_id == organization_id)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # Trait count
        trait_stmt = (
            select(func.count(ObservationVariable.id))
            .where(ObservationVariable.organization_id == organization_id)
        )
        trait_result = await db.execute(trait_stmt)
        trait_count = trait_result.scalar() or 0

        return {
            "total_observations": total,
            "trait_count": trait_count,
        }


# Singleton instance
observation_search_service = ObservationSearchService()
