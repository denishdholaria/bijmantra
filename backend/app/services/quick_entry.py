"""
Quick Entry Service
Rapid data entry for common breeding tasks - germplasm, observations, crosses, trials

Converted to database queries per Zero Mock Data Policy (Session 77).
Returns empty results when no data exists.
"""
from datetime import datetime, UTC, timedelta
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.germplasm import Germplasm, PlannedCross
from app.models.phenotyping import Observation
from app.models.core import Trial


class QuickEntryService:
    """Service for quick data entry operations.
    
    All methods are async and require database session.
    Queries actual database tables for real data.
    """

    async def create_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        entry_type: str,
        data: dict,
        created_by: str = "system",
    ) -> dict:
        """Create a new quick entry.
        
        Quick Entry Types:
        - germplasm: Create new germplasm accession
        - observation: Record phenotypic observation
        - cross: Plan a new cross
        - trial: Create a new trial
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            entry_type: Type of entry (germplasm, observation, cross, trial)
            data: Entry data specific to the type
            created_by: User who created the entry
            
        Returns:
            Created entry record
        """
        if entry_type == "germplasm":
            return await self._create_germplasm_entry(db, organization_id, data, created_by)
        elif entry_type == "observation":
            return await self._create_observation_entry(db, organization_id, data, created_by)
        elif entry_type == "cross":
            return await self._create_cross_entry(db, organization_id, data, created_by)
        elif entry_type == "trial":
            return await self._create_trial_entry(db, organization_id, data, created_by)
        else:
            return {
                "id": None,
                "type": entry_type,
                "data": data,
                "created_at": datetime.now(UTC).isoformat(),
                "created_by": created_by,
                "status": "error",
                "message": f"Unknown entry type: {entry_type}",
            }
    
    async def _create_germplasm_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        data: dict,
        created_by: str,
    ) -> dict:
        """Create germplasm entry."""
        germplasm = Germplasm(
            organization_id=organization_id,
            germplasm_name=data.get("germplasm_name", ""),
            accession_number=data.get("accession_number"),
            species=data.get("species"),
            country_of_origin_code=data.get("country_of_origin"),
            pedigree=data.get("pedigree"),
            additional_info={"created_via": "quick_entry", "created_by": created_by},
        )
        
        db.add(germplasm)
        await db.commit()
        await db.refresh(germplasm)
        
        return {
            "id": str(germplasm.id),
            "type": "germplasm",
            "data": data,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": created_by,
            "status": "saved",
        }
    
    async def _create_observation_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        data: dict,
        created_by: str,
    ) -> dict:
        """Create observation entry."""
        observation = Observation(
            organization_id=organization_id,
            observation_unit_db_id=data.get("observation_unit_id"),
            observation_variable_db_id=data.get("trait"),
            value=str(data.get("value", "")),
            observation_time_stamp=datetime.now(UTC),
            additional_info={"created_via": "quick_entry", "created_by": created_by, "unit": data.get("unit")},
        )
        
        db.add(observation)
        await db.commit()
        await db.refresh(observation)
        
        return {
            "id": str(observation.id),
            "type": "observation",
            "data": data,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": created_by,
            "status": "saved",
        }
    
    async def _create_cross_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        data: dict,
        created_by: str,
    ) -> dict:
        """Create cross entry."""
        # Generate cross ID
        count_result = await db.execute(
            select(func.count()).select_from(PlannedCross).where(
                PlannedCross.organization_id == organization_id
            )
        )
        count = count_result.scalar() or 0
        
        cross = PlannedCross(
            organization_id=organization_id,
            planned_cross_db_id=f"QE-CX{count + 1:04d}",
            planned_cross_name=f"{data.get('female_parent', 'Unknown')} × {data.get('male_parent', 'Unknown')}",
            status="PLANNED",
            number_of_progeny=data.get("seeds_obtained", 0),
            additional_info={
                "created_via": "quick_entry",
                "created_by": created_by,
                "cross_date": data.get("cross_date"),
                "female_parent": data.get("female_parent"),
                "male_parent": data.get("male_parent"),
            },
        )
        
        db.add(cross)
        await db.commit()
        await db.refresh(cross)
        
        return {
            "id": str(cross.id),
            "type": "cross",
            "data": data,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": created_by,
            "status": "saved",
        }
    
    async def _create_trial_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        data: dict,
        created_by: str,
    ) -> dict:
        """Create trial entry."""
        trial = Trial(
            organization_id=organization_id,
            trial_name=data.get("trial_name", "Quick Entry Trial"),
            trial_description=data.get("description"),
            additional_info={"created_via": "quick_entry", "created_by": created_by},
        )
        
        db.add(trial)
        await db.commit()
        await db.refresh(trial)
        
        return {
            "id": str(trial.id),
            "type": "trial",
            "data": data,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": created_by,
            "status": "saved",
        }

    async def get_entries(
        self,
        db: AsyncSession,
        organization_id: int,
        entry_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get quick entries with optional type filter.
        
        Note: Quick entries are stored in their respective tables
        (germplasm, observations, crosses, trials) with additional_info
        containing {"created_via": "quick_entry"}.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            entry_type: Optional filter by entry type
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Paginated list of entries
        """
        entries = []
        total = 0
        
        # Query germplasm entries
        if entry_type is None or entry_type == "germplasm":
            stmt = select(Germplasm).where(
                and_(
                    Germplasm.organization_id == organization_id,
                    Germplasm.additional_info.contains({"created_via": "quick_entry"})
                )
            ).order_by(Germplasm.created_at.desc()).limit(limit)
            
            result = await db.execute(stmt)
            for g in result.scalars().all():
                entries.append({
                    "id": str(g.id),
                    "type": "germplasm",
                    "data": {
                        "germplasm_name": g.germplasm_name,
                        "accession_number": g.accession_number,
                        "species": g.species,
                    },
                    "created_at": g.created_at.isoformat() if g.created_at else None,
                    "created_by": (g.additional_info or {}).get("created_by", "unknown"),
                })
        
        # Query observation entries
        if entry_type is None or entry_type == "observation":
            stmt = select(Observation).where(
                and_(
                    Observation.organization_id == organization_id,
                    Observation.additional_info.contains({"created_via": "quick_entry"})
                )
            ).order_by(Observation.created_at.desc()).limit(limit)
            
            result = await db.execute(stmt)
            for o in result.scalars().all():
                entries.append({
                    "id": str(o.id),
                    "type": "observation",
                    "data": {
                        "observation_unit_id": o.observation_unit_db_id,
                        "trait": o.observation_variable_db_id,
                        "value": o.value,
                    },
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                    "created_by": (o.additional_info or {}).get("created_by", "unknown"),
                })
        
        # Query cross entries
        if entry_type is None or entry_type == "cross":
            stmt = select(PlannedCross).where(
                and_(
                    PlannedCross.organization_id == organization_id,
                    PlannedCross.additional_info.contains({"created_via": "quick_entry"})
                )
            ).order_by(PlannedCross.created_at.desc()).limit(limit)
            
            result = await db.execute(stmt)
            for c in result.scalars().all():
                additional = c.additional_info or {}
                entries.append({
                    "id": str(c.id),
                    "type": "cross",
                    "data": {
                        "female_parent": additional.get("female_parent"),
                        "male_parent": additional.get("male_parent"),
                        "cross_date": additional.get("cross_date"),
                        "seeds_obtained": c.number_of_progeny,
                    },
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "created_by": additional.get("created_by", "unknown"),
                })
        
        # Sort by created_at descending
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Apply pagination
        total = len(entries)
        entries = entries[offset:offset + limit]
        
        return {
            "entries": entries,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def get_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        entry_id: str,
    ) -> Optional[dict]:
        """Get a single entry by ID.
        
        Note: Entry ID format determines the table to query.
        """
        # This would require knowing which table the entry is in
        # For now, return None - entries should be queried via get_entries
        return None

    async def delete_entry(
        self,
        db: AsyncSession,
        organization_id: int,
        entry_id: str,
        entry_type: str,
    ) -> bool:
        """Delete an entry.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            entry_id: Entry ID to delete
            entry_type: Type of entry (germplasm, observation, cross, trial)
            
        Returns:
            True if deleted, False if not found
        """
        if entry_type == "germplasm":
            stmt = select(Germplasm).where(
                and_(
                    Germplasm.id == int(entry_id),
                    Germplasm.organization_id == organization_id,
                )
            )
            result = await db.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry:
                await db.delete(entry)
                await db.commit()
                return True
        
        elif entry_type == "observation":
            stmt = select(Observation).where(
                and_(
                    Observation.id == int(entry_id),
                    Observation.organization_id == organization_id,
                )
            )
            result = await db.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry:
                await db.delete(entry)
                await db.commit()
                return True
        
        elif entry_type == "cross":
            stmt = select(PlannedCross).where(
                and_(
                    PlannedCross.id == int(entry_id),
                    PlannedCross.organization_id == organization_id,
                )
            )
            result = await db.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry:
                await db.delete(entry)
                await db.commit()
                return True
        
        return False

    async def get_session_stats(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> dict:
        """Get session statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            
        Returns:
            Statistics about quick entries
        """
        stats = {
            "total_entries": 0,
            "by_type": {
                "germplasm": 0,
                "observation": 0,
                "cross": 0,
                "trial": 0,
            },
            "recent_by_type": {},
            "last_entry_by_type": {},
        }
        
        # Count germplasm entries
        result = await db.execute(
            select(func.count()).select_from(Germplasm).where(
                and_(
                    Germplasm.organization_id == organization_id,
                    Germplasm.additional_info.contains({"created_via": "quick_entry"})
                )
            )
        )
        stats["by_type"]["germplasm"] = result.scalar() or 0
        
        # Count observation entries
        result = await db.execute(
            select(func.count()).select_from(Observation).where(
                and_(
                    Observation.organization_id == organization_id,
                    Observation.additional_info.contains({"created_via": "quick_entry"})
                )
            )
        )
        stats["by_type"]["observation"] = result.scalar() or 0
        
        # Count cross entries
        result = await db.execute(
            select(func.count()).select_from(PlannedCross).where(
                and_(
                    PlannedCross.organization_id == organization_id,
                    PlannedCross.additional_info.contains({"created_via": "quick_entry"})
                )
            )
        )
        stats["by_type"]["cross"] = result.scalar() or 0
        
        stats["total_entries"] = sum(stats["by_type"].values())
        
        return stats

    async def get_recent_activity(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> list[dict]:
        """Get recent activity summary for dashboard.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            
        Returns:
            Summary of recent quick entry activity by type
        """
        stats = await self.get_session_stats(db, organization_id)
        
        return [
            {
                "type": entry_type,
                "count": count,
                "last_entry": None,  # Would need additional query
            }
            for entry_type, count in stats["by_type"].items()
            if count > 0
        ]

    def get_dropdown_options(self, option_type: str) -> list[dict]:
        """Get dropdown options for quick entry forms.
        
        Returns static reference data for form dropdowns.
        
        Args:
            option_type: Type of options (species, countries, traits, programs, germplasm)
            
        Returns:
            List of dropdown options
        """
        options = {
            "species": [
                {"value": "Oryza sativa", "label": "Oryza sativa (Rice)"},
                {"value": "Triticum aestivum", "label": "Triticum aestivum (Wheat)"},
                {"value": "Zea mays", "label": "Zea mays (Maize)"},
                {"value": "Glycine max", "label": "Glycine max (Soybean)"},
                {"value": "Sorghum bicolor", "label": "Sorghum bicolor (Sorghum)"},
            ],
            "countries": [
                {"value": "IND", "label": "India"},
                {"value": "PHL", "label": "Philippines"},
                {"value": "CHN", "label": "China"},
                {"value": "BGD", "label": "Bangladesh"},
                {"value": "VNM", "label": "Vietnam"},
                {"value": "THA", "label": "Thailand"},
                {"value": "IDN", "label": "Indonesia"},
                {"value": "USA", "label": "United States"},
            ],
            "traits": [
                {"value": "grain_yield", "label": "Grain Yield (t/ha)", "unit": "t/ha"},
                {"value": "plant_height", "label": "Plant Height (cm)", "unit": "cm"},
                {"value": "days_to_maturity", "label": "Days to Maturity", "unit": "days"},
                {"value": "days_to_flowering", "label": "Days to Flowering", "unit": "days"},
                {"value": "1000_grain_weight", "label": "1000 Grain Weight (g)", "unit": "g"},
                {"value": "tiller_count", "label": "Tiller Count", "unit": "count"},
                {"value": "panicle_length", "label": "Panicle Length (cm)", "unit": "cm"},
            ],
            "programs": [
                {"value": "rice-breeding", "label": "Rice Breeding Program"},
                {"value": "wheat-breeding", "label": "Wheat Breeding Program"},
                {"value": "maize-breeding", "label": "Maize Breeding Program"},
                {"value": "disease-resistance", "label": "Disease Resistance Program"},
            ],
            "germplasm": [],  # Should be fetched from database
        }
        return options.get(option_type, [])


# Singleton instance
quick_entry_service = QuickEntryService()
