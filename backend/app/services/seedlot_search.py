"""
Seedlot Search Service

Advanced seedlot search and discovery.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload


class SeedlotSearchService:
    """Service for advanced seedlot search.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """

    async def search(
        self, 
        db: AsyncSession,
        organization_id: int,
        query: Optional[str] = None,
        germplasm_id: Optional[int] = None,
        location_id: Optional[int] = None,
        program_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search seedlots with filters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            query: Text search query (name, description)
            germplasm_id: Filter by germplasm
            location_id: Filter by storage location
            program_id: Filter by program
            limit: Maximum results to return
            
        Returns:
            List of seedlot dictionaries, empty if no data
        """
        from app.models.germplasm import Seedlot
        
        stmt = (
            select(Seedlot)
            .options(
                selectinload(Seedlot.germplasm),
                selectinload(Seedlot.location),
                selectinload(Seedlot.program)
            )
            .where(Seedlot.organization_id == organization_id)
            .limit(limit)
        )
        
        if query:
            q = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Seedlot.seedlot_name).like(q),
                    func.lower(Seedlot.seedlot_db_id).like(q),
                    func.lower(Seedlot.seedlot_description).like(q),
                    func.lower(Seedlot.storage_location).like(q),
                )
            )
        
        if germplasm_id:
            stmt = stmt.where(Seedlot.germplasm_id == germplasm_id)
        
        if location_id:
            stmt = stmt.where(Seedlot.location_id == location_id)
        
        if program_id:
            stmt = stmt.where(Seedlot.program_id == program_id)
        
        result = await db.execute(stmt)
        seedlots = result.scalars().all()
        
        results = []
        for s in seedlots:
            results.append({
                "id": str(s.id),
                "seedlot_db_id": s.seedlot_db_id,
                "name": s.seedlot_name,
                "description": s.seedlot_description or "",
                "count": s.count,
                "units": s.units,
                "storage_location": s.storage_location,
                "source_collection": s.source_collection,
                "creation_date": str(s.creation_date) if s.creation_date else None,
                "germplasm": {
                    "id": str(s.germplasm.id),
                    "name": s.germplasm.germplasm_name,
                    "accession": s.germplasm.accession_number,
                } if s.germplasm else None,
                "location": {
                    "id": str(s.location.id),
                    "name": s.location.location_name,
                } if s.location else None,
                "program": {
                    "id": str(s.program.id),
                    "name": s.program.program_name,
                } if s.program else None,
            })
        
        return results
    
    async def get_by_id(
        self, 
        db: AsyncSession,
        organization_id: int,
        seedlot_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get seedlot by ID with full details.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            seedlot_id: Seedlot ID
            
        Returns:
            Seedlot dictionary or None if not found
        """
        from app.models.germplasm import Seedlot
        
        stmt = (
            select(Seedlot)
            .options(
                selectinload(Seedlot.germplasm),
                selectinload(Seedlot.location),
                selectinload(Seedlot.program),
                selectinload(Seedlot.transactions)
            )
            .where(Seedlot.organization_id == organization_id)
            .where(Seedlot.id == int(seedlot_id))
        )
        
        result = await db.execute(stmt)
        s = result.scalar_one_or_none()
        
        if not s:
            return None
        
        return {
            "id": str(s.id),
            "seedlot_db_id": s.seedlot_db_id,
            "name": s.seedlot_name,
            "description": s.seedlot_description or "",
            "count": s.count,
            "units": s.units,
            "storage_location": s.storage_location,
            "source_collection": s.source_collection,
            "creation_date": str(s.creation_date) if s.creation_date else None,
            "last_updated": str(s.last_updated) if s.last_updated else None,
            "germplasm": {
                "id": str(s.germplasm.id),
                "name": s.germplasm.germplasm_name,
                "accession": s.germplasm.accession_number,
                "species": s.germplasm.species,
            } if s.germplasm else None,
            "location": {
                "id": str(s.location.id),
                "name": s.location.location_name,
                "country": s.location.country_name,
            } if s.location else None,
            "program": {
                "id": str(s.program.id),
                "name": s.program.program_name,
            } if s.program else None,
            "transactions": [
                {
                    "id": str(t.id),
                    "description": t.transaction_description,
                    "amount": t.amount,
                    "units": t.units,
                    "timestamp": t.transaction_timestamp,
                }
                for t in (s.transactions or [])
            ],
            "additional_info": s.additional_info or {},
        }
    
    async def get_by_germplasm(
        self, 
        db: AsyncSession,
        organization_id: int,
        germplasm_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get all seedlots for a germplasm.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            germplasm_id: Germplasm ID
            limit: Maximum results
            
        Returns:
            List of seedlot dictionaries
        """
        return await self.search(
            db=db,
            organization_id=organization_id,
            germplasm_id=germplasm_id,
            limit=limit
        )
    
    async def check_viability(
        self, 
        db: AsyncSession,
        organization_id: int,
        seedlot_id: str
    ) -> Dict[str, Any]:
        """Check seed viability for a seedlot.
        
        This checks the seedlot's additional_info for viability data
        and calculates estimated viability based on age and storage conditions.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            seedlot_id: Seedlot ID
            
        Returns:
            Viability assessment dictionary
        """
        from datetime import date
        
        seedlot = await self.get_by_id(db, organization_id, seedlot_id)
        
        if not seedlot:
            return {
                "seedlot_id": seedlot_id,
                "found": False,
                "viability": None,
                "message": "Seedlot not found"
            }
        
        # Check for viability data in additional_info
        additional_info = seedlot.get("additional_info", {})
        last_viability_test = additional_info.get("last_viability_test")
        viability_percent = additional_info.get("viability_percent")
        
        # Calculate age-based estimate if no test data
        creation_date = seedlot.get("creation_date")
        age_years = None
        estimated_viability = None
        
        if creation_date:
            try:
                created = date.fromisoformat(creation_date)
                age_years = (date.today() - created).days / 365.25
                # Simple viability decay model (species-dependent in reality)
                # Assumes ~95% initial viability, ~3% loss per year
                estimated_viability = max(0, 95 - (age_years * 3))
            except (ValueError, TypeError):
                pass
        
        return {
            "seedlot_id": seedlot_id,
            "found": True,
            "seedlot_name": seedlot.get("name"),
            "germplasm": seedlot.get("germplasm"),
            "count": seedlot.get("count"),
            "units": seedlot.get("units"),
            "storage_location": seedlot.get("storage_location"),
            "creation_date": creation_date,
            "age_years": round(age_years, 1) if age_years else None,
            "last_viability_test": last_viability_test,
            "tested_viability_percent": viability_percent,
            "estimated_viability_percent": round(estimated_viability, 1) if estimated_viability else None,
            "viability_status": self._get_viability_status(viability_percent or estimated_viability),
            "recommendation": self._get_viability_recommendation(viability_percent or estimated_viability, age_years),
            "message": f"Seedlot '{seedlot.get('name')}' viability assessment"
        }
    
    def _get_viability_status(self, viability: Optional[float]) -> str:
        """Get viability status label."""
        if viability is None:
            return "UNKNOWN"
        if viability >= 85:
            return "EXCELLENT"
        if viability >= 70:
            return "GOOD"
        if viability >= 50:
            return "FAIR"
        if viability >= 30:
            return "POOR"
        return "CRITICAL"
    
    def _get_viability_recommendation(self, viability: Optional[float], age_years: Optional[float]) -> str:
        """Get recommendation based on viability."""
        if viability is None:
            return "Viability test recommended - no data available"
        if viability >= 85:
            return "Seeds in excellent condition for planting or distribution"
        if viability >= 70:
            return "Seeds suitable for planting; consider regeneration within 2-3 years"
        if viability >= 50:
            return "Regeneration recommended soon to maintain genetic integrity"
        if viability >= 30:
            return "Urgent regeneration required - viability declining"
        return "Critical: Immediate regeneration or rescue crossing recommended"
    
    async def get_statistics(
        self, 
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, int]:
        """Get seedlot statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        from app.models.germplasm import Seedlot, SeedlotTransaction
        
        # Total seedlots
        total_stmt = (
            select(func.count(Seedlot.id))
            .where(Seedlot.organization_id == organization_id)
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # Total seed count
        count_stmt = (
            select(func.sum(Seedlot.count))
            .where(Seedlot.organization_id == organization_id)
        )
        count_result = await db.execute(count_stmt)
        total_seeds = count_result.scalar() or 0
        
        # Unique germplasm in seedlots
        germplasm_stmt = (
            select(func.count(func.distinct(Seedlot.germplasm_id)))
            .where(Seedlot.organization_id == organization_id)
        )
        germplasm_result = await db.execute(germplasm_stmt)
        germplasm_count = germplasm_result.scalar() or 0
        
        # Transaction count
        transaction_stmt = (
            select(func.count(SeedlotTransaction.id))
            .where(SeedlotTransaction.organization_id == organization_id)
        )
        transaction_result = await db.execute(transaction_stmt)
        transaction_count = transaction_result.scalar() or 0
        
        return {
            "total_seedlots": total,
            "total_seeds": int(total_seeds) if total_seeds else 0,
            "germplasm_in_storage": germplasm_count,
            "transaction_count": transaction_count,
        }


# Singleton instance
seedlot_search_service = SeedlotSearchService()
