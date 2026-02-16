"""
Trait/Observation Variable Search Service

Advanced trait search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload


class TraitSearchService:
    """Service for advanced trait/observation variable search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self,
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        trait_class: Optional[str] = None,
        data_type: Optional[str] = None,
        crop: Optional[str] = None,
        ontology: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search traits/observation variables with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query (name, description, synonyms)
            trait_class: Filter by trait class (morphological, physiological, etc.)
            data_type: Filter by data type (Numerical, Categorical, etc.)
            crop: Filter by common crop name
            ontology: Filter by ontology name
            limit: Maximum results to return
            
        Returns:
            List of trait dictionaries, empty if no data
        """
        from app.models.phenotyping import ObservationVariable

        stmt = (
            select(ObservationVariable)
            .where(ObservationVariable.organization_id == organization_id)
            .limit(limit)
        )

        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(ObservationVariable.observation_variable_name).like(q),
                    func.lower(ObservationVariable.trait_name).like(q),
                    func.lower(ObservationVariable.trait_description).like(q),
                    func.lower(ObservationVariable.method_name).like(q),
                    func.lower(ObservationVariable.scale_name).like(q),
                )
            )

        if trait_class:
            stmt = stmt.where(func.lower(ObservationVariable.trait_class) == trait_class.lower())

        if data_type:
            stmt = stmt.where(func.lower(ObservationVariable.data_type) == data_type.lower())

        if crop:
            stmt = stmt.where(func.lower(ObservationVariable.common_crop_name) == crop.lower())

        if ontology:
            stmt = stmt.where(func.lower(ObservationVariable.ontology_name).like(f"%{ontology.lower()}%"))

        result = await db.execute(stmt)
        variables = result.scalars().all()

        results = []
        for v in variables:
            results.append({
                "id": str(v.id),
                "variable_db_id": v.observation_variable_db_id,
                "name": v.observation_variable_name,
                "trait_name": v.trait_name,
                "trait_description": v.trait_description or "",
                "trait_class": v.trait_class,
                "method_name": v.method_name,
                "method_description": v.method_description or "",
                "scale_name": v.scale_name,
                "data_type": v.data_type,
                "crop": v.common_crop_name,
                "ontology": v.ontology_name,
                "growth_stage": v.growth_stage,
                "synonyms": v.synonyms or [],
                "valid_values": v.valid_values,
            })

        return results

    async def get_by_id(
        self,
        db: AsyncSession,
        organization_id: int,
        trait_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get trait by ID with full details.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trait_id: Trait/ObservationVariable ID
            
        Returns:
            Trait dictionary or None if not found
        """
        from app.models.phenotyping import ObservationVariable

        stmt = (
            select(ObservationVariable)
            .options(selectinload(ObservationVariable.observations))
            .where(ObservationVariable.organization_id == organization_id)
            .where(ObservationVariable.id == int(trait_id))
        )

        result = await db.execute(stmt)
        v = result.scalar_one_or_none()

        if not v:
            return None

        return {
            "id": str(v.id),
            "variable_db_id": v.observation_variable_db_id,
            "name": v.observation_variable_name,
            "trait_name": v.trait_name,
            "trait_description": v.trait_description or "",
            "trait_class": v.trait_class,
            "method": {
                "db_id": v.method_db_id,
                "name": v.method_name,
                "description": v.method_description,
                "class": v.method_class,
                "formula": v.formula,
            },
            "scale": {
                "db_id": v.scale_db_id,
                "name": v.scale_name,
                "data_type": v.data_type,
                "decimal_places": v.decimal_places,
                "valid_values": v.valid_values,
            },
            "ontology": {
                "db_id": v.ontology_db_id,
                "name": v.ontology_name,
            },
            "crop": v.common_crop_name,
            "growth_stage": v.growth_stage,
            "synonyms": v.synonyms or [],
            "observation_count": len(v.observations) if v.observations else 0,
            "additional_info": v.additional_info or {},
        }

    async def get_by_crop(
        self,
        db: AsyncSession,
        organization_id: int,
        crop: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all traits for a specific crop.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            crop: Common crop name
            limit: Maximum results
            
        Returns:
            List of trait dictionaries
        """
        return await self.search(
            db=db,
            organization_id=organization_id,
            crop=crop,
            limit=limit
        )

    async def get_trait_classes(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> List[str]:
        """Get distinct trait classes.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            List of trait class names
        """
        from app.models.phenotyping import ObservationVariable

        stmt = (
            select(func.distinct(ObservationVariable.trait_class))
            .where(ObservationVariable.organization_id == organization_id)
            .where(ObservationVariable.trait_class.isnot(None))
        )

        result = await db.execute(stmt)
        return [r[0] for r in result.all() if r[0]]

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get trait statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.phenotyping import ObservationVariable

        # Total traits
        total_stmt = (
            select(func.count(ObservationVariable.id))
            .where(ObservationVariable.organization_id == organization_id)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # Trait class count
        class_stmt = (
            select(func.count(func.distinct(ObservationVariable.trait_class)))
            .where(ObservationVariable.organization_id == organization_id)
        )
        class_result = await db.execute(class_stmt)
        class_count = class_result.scalar() or 0

        # Ontology count
        ontology_stmt = (
            select(func.count(func.distinct(ObservationVariable.ontology_name)))
            .where(ObservationVariable.organization_id == organization_id)
        )
        ontology_result = await db.execute(ontology_stmt)
        ontology_count = ontology_result.scalar() or 0

        # Crop count
        crop_stmt = (
            select(func.count(func.distinct(ObservationVariable.common_crop_name)))
            .where(ObservationVariable.organization_id == organization_id)
        )
        crop_result = await db.execute(crop_stmt)
        crop_count = crop_result.scalar() or 0

        return {
            "total_traits": total,
            "trait_class_count": class_count,
            "ontology_count": ontology_count,
            "crop_count": crop_count,
        }


# Singleton instance
trait_search_service = TraitSearchService()
