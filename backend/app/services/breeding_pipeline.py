"""
Breeding Pipeline Service

Tracks germplasm flow through breeding stages from crosses to variety release.
Uses Germplasm table with additional_info for pipeline tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.sql import cast
from sqlalchemy.types import String

from app.models.germplasm import Germplasm
from app.models.core import Program


# Pipeline stages definition
PIPELINE_STAGES = [
    {"id": "F1", "name": "F1 Crosses", "order": 1, "description": "Initial crosses between parents"},
    {"id": "F2", "name": "F2 Population", "order": 2, "description": "Segregating population"},
    {"id": "F3-F5", "name": "F3-F5 Selection", "order": 3, "description": "Pedigree selection and fixation"},
    {"id": "PYT", "name": "Preliminary Yield Trial", "order": 4, "description": "Initial yield evaluation"},
    {"id": "AYT", "name": "Advanced Yield Trial", "order": 5, "description": "Advanced yield testing"},
    {"id": "MLT", "name": "Multi-Location Trial", "order": 6, "description": "Testing across locations"},
    {"id": "RELEASE", "name": "Variety Release", "order": 7, "description": "Official variety release"},
]


class BreedingPipelineService:
    """Service for managing breeding pipeline entries backed by DB."""
    
    def __init__(self, db: AsyncSession, organization_id: int):
        self.db = db
        self.organization_id = organization_id
    
    def get_stages(self) -> List[Dict[str, Any]]:
        """Get all pipeline stages."""
        return PIPELINE_STAGES
    
    async def list_entries(
        self,
        stage: Optional[str] = None,
        crop: Optional[str] = None,
        program_id: Optional[str] = None,
        status: Optional[str] = None,
        year: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List pipeline entries with filters."""
        
        # Base query: Only Germplasm with breeding_pipeline_stage
        query = select(Germplasm).where(
            Germplasm.organization_id == self.organization_id,
            func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_stage') != None
        )

        # Apply filters
        if stage and stage != 'all':
            query = query.where(
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_stage') == stage
            )

        if crop and crop != 'all':
            # Case insensitive crop search
            query = query.where(func.lower(Germplasm.common_crop_name) == crop.lower())

        if program_id:
            query = query.where(
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_program_id') == program_id
            )

        if status:
            query = query.where(
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_status') == status
            )

        if year:
            query = query.where(
                cast(func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_year'), String) == str(year)
            )

        if search:
            search_lower = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(Germplasm.germplasm_name).like(search_lower),
                    func.lower(Germplasm.pedigree).like(search_lower),
                    func.lower(Germplasm.germplasm_db_id).like(search_lower)
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Pagination
        query = query.limit(limit).offset(offset).order_by(desc(Germplasm.id))

        result = await self.db.execute(query)
        germplasms = result.scalars().all()

        data = [self._map_to_entry(g) for g in germplasms]
        
        return {
            "data": data,
            "total": total or 0,
            "limit": limit,
            "offset": offset,
        }
    
    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a single pipeline entry by ID (germplasm_db_id)."""
        query = select(Germplasm).where(
            Germplasm.organization_id == self.organization_id,
            Germplasm.germplasm_db_id == entry_id
        )
        result = await self.db.execute(query)
        germplasm = result.scalar_one_or_none()

        if not germplasm:
            return None

        return self._map_to_entry(germplasm)
    
    async def get_statistics(
        self,
        program_id: Optional[str] = None,
        crop: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get pipeline statistics."""

        # Base conditions
        conditions = [
            Germplasm.organization_id == self.organization_id,
            func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_stage') != None
        ]
        
        if program_id:
            conditions.append(
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_program_id') == program_id
            )
        if crop:
             conditions.append(func.lower(Germplasm.common_crop_name) == crop.lower())

        base_query = select(Germplasm).where(and_(*conditions))

        # Execute query to process in python for complex stats
        # Note: In a larger scale, we should use specialized SQL queries
        result = await self.db.execute(base_query)
        germplasms = result.scalars().all()
        
        entries = [self._map_to_entry(g) for g in germplasms]

        active = len([e for e in entries if e["status"] == "active"])
        released = len([e for e in entries if e["status"] == "released"])
        dropped = len([e for e in entries if e["status"] == "dropped"])
        
        stage_counts = {}
        for stage in PIPELINE_STAGES:
            stage_counts[stage["id"]] = len([
                e for e in entries
                if e["current_stage"] == stage["id"] and e["status"] == "active"
            ])

        crop_counts = {}
        for entry in entries:
            crop_name = entry.get("crop", "Unknown")
            crop_counts[crop_name] = crop_counts.get(crop_name, 0) + 1

        # Avg years to release
        released_entries = [e for e in entries if e["status"] == "released"]
        avg_years = 0
        if released_entries:
            total_years = 0
            count = 0
            for entry in released_entries:
                history = entry.get("stage_history", [])
                if history:
                    try:
                        first_date = history[0]["date"]
                        last_date = history[-1]["date"]
                        first_year = int(first_date.split("-")[0])
                        last_year = int(last_date.split("-")[0])
                        total_years += (last_year - first_year)
                        count += 1
                    except:
                        pass
            avg_years = round(total_years / count, 1) if count else 0

        return {
            "total_entries": len(entries),
            "active": active,
            "released": released,
            "dropped": dropped,
            "stage_counts": stage_counts,
            "crop_counts": crop_counts,
            "avg_years_to_release": avg_years,
            "crops": list(crop_counts.keys()),
        }
    
    async def get_stage_summary(self) -> List[Dict[str, Any]]:
        """Get summary of entries at each stage."""
        summary = []

        for stage in PIPELINE_STAGES:
            query = select(Germplasm).where(
                Germplasm.organization_id == self.organization_id,
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_stage') == stage["id"],
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_status') == "active"
            ).limit(5)

            result = await self.db.execute(query)
            top_germplasms = result.scalars().all()

            count_query = select(func.count(Germplasm.id)).where(
                Germplasm.organization_id == self.organization_id,
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_stage') == stage["id"],
                func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_status') == "active"
            )
            count = await self.db.scalar(count_query)

            summary.append({
                "stage_id": stage["id"],
                "stage_name": stage["name"],
                "order": stage["order"],
                "count": count or 0,
                "entries": [
                    {
                        "id": g.germplasm_db_id,
                        "name": g.germplasm_name,
                        "crop": g.common_crop_name
                    }
                    for g in top_germplasms
                ],
            })

        return summary
    
    async def get_crops(self) -> List[str]:
        """Get list of unique crops in the pipeline."""
        query = select(Germplasm.common_crop_name).where(
            Germplasm.organization_id == self.organization_id,
            func.json_extract(Germplasm.additional_info, '$.breeding_pipeline_stage') != None
        ).distinct()

        result = await self.db.execute(query)
        crops = [c for c in result.scalars().all() if c]
        return sorted(crops)

    async def get_programs(self) -> List[Dict[str, Any]]:
        """Get list of unique programs."""
        # Query programs table directly
        query = select(Program).where(Program.organization_id == self.organization_id)
        result = await self.db.execute(query)
        programs = result.scalars().all()
        return [
            {"id": p.program_db_id, "name": p.program_name}
            for p in programs
        ]

    async def create_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pipeline entry (Germplasm)."""

        # Generate ID
        # In real app, we might check sequence or UUID
        import uuid
        entry_id = f"BM-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
        
        info = {
            "breeding_pipeline_stage": data.get("current_stage", "F1"),
            "breeding_pipeline_status": "active",
            "breeding_pipeline_program_id": data.get("program_id"),
            "breeding_pipeline_program_name": data.get("program_name"),
            "breeding_pipeline_year": data.get("year", datetime.now().year),
            "breeding_pipeline_traits": data.get("traits", []),
            "breeding_pipeline_notes": data.get("notes", ""),
            "breeding_pipeline_history": [
                {
                    "stage": data.get("current_stage", "F1"),
                    "date": datetime.now().strftime("%Y-%m"),
                    "decision": "In Progress",
                    "notes": data.get("notes", "Entry created"),
                }
            ]
        }
        
        germplasm = Germplasm(
            organization_id=self.organization_id,
            germplasm_db_id=entry_id,
            germplasm_name=data["name"],
            default_display_name=data["name"],
            pedigree=data["pedigree"],
            common_crop_name=data["crop"],
            additional_info=info,
            # Defaults
            acquisition_date=datetime.now().date(),
        )

        self.db.add(germplasm)
        await self.db.commit()
        await self.db.refresh(germplasm)

        return self._map_to_entry(germplasm)

    async def advance_stage(self, entry_id: str, decision: str, notes: str = "") -> Optional[Dict[str, Any]]:
        """Advance an entry to the next stage."""

        query = select(Germplasm).where(
            Germplasm.organization_id == self.organization_id,
            Germplasm.germplasm_db_id == entry_id
        )
        result = await self.db.execute(query)
        germplasm = result.scalar_one_or_none()

        if not germplasm:
            return None

        info = germplasm.additional_info.copy() if germplasm.additional_info else {}
        current_stage_id = info.get("breeding_pipeline_stage")
        history = info.get("breeding_pipeline_history", [])
        
        current_stage_idx = next(
            (i for i, s in enumerate(PIPELINE_STAGES) if s["id"] == current_stage_id),
            -1
        )
        
        if current_stage_idx < 0:
            return None # Invalid stage

        # Update current stage history
        if history:
            history[-1]["decision"] = decision
            if notes:
                history[-1]["notes"] = notes
        
        if decision == "Advanced":
             if current_stage_idx >= len(PIPELINE_STAGES) - 1:
                 # Already at last stage
                 return None

             next_stage = PIPELINE_STAGES[current_stage_idx + 1]
             info["breeding_pipeline_stage"] = next_stage["id"]
             history.append({
                "stage": next_stage["id"],
                "date": datetime.now().strftime("%Y-%m"),
                "decision": "In Progress",
                "notes": "",
            })

             if next_stage["id"] == "RELEASE":
                 info["breeding_pipeline_status"] = "released"

        elif decision == "Dropped":
            info["breeding_pipeline_status"] = "dropped"

        info["breeding_pipeline_history"] = history
        germplasm.additional_info = info
        
        await self.db.commit()
        await self.db.refresh(germplasm)

        return self._map_to_entry(germplasm)

    def _map_to_entry(self, germplasm: Germplasm) -> Dict[str, Any]:
        """Map Germplasm model to pipeline entry dict."""
        info = germplasm.additional_info or {}
        return {
            "id": germplasm.germplasm_db_id,
            "name": germplasm.germplasm_name,
            "pedigree": germplasm.pedigree,
            "current_stage": info.get("breeding_pipeline_stage"),
            "program_id": info.get("breeding_pipeline_program_id"),
            "program_name": info.get("breeding_pipeline_program_name"),
            "crop": germplasm.common_crop_name,
            "year": info.get("breeding_pipeline_year"),
            "status": info.get("breeding_pipeline_status", "active"),
            "traits": info.get("breeding_pipeline_traits", []),
            "notes": info.get("breeding_pipeline_notes", ""),
            "stage_history": info.get("breeding_pipeline_history", []),
            "created_at": str(germplasm.acquisition_date) if germplasm.acquisition_date else None,
        }
