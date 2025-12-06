"""
Nursery Management Service for Plant Breeding
Breeding nursery planning, tracking, and management

Features:
- Nursery registration and planning
- Entry management
- Advancement decisions
- Selection tracking
- Nursery summary reports
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import date
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NurseryType(str, Enum):
    OBSERVATION = "observation"  # OYT
    PRELIMINARY = "preliminary"  # PYT
    ADVANCED = "advanced"  # AYT
    ELITE = "elite"
    CROSSING_BLOCK = "crossing_block"
    SEED_INCREASE = "seed_increase"


class SelectionDecision(str, Enum):
    ADVANCE = "advance"
    REJECT = "reject"
    HOLD = "hold"
    RELEASE = "release"


@dataclass
class NurseryEntry:
    """Entry in a nursery"""
    entry_id: str
    nursery_id: str
    genotype_id: str
    genotype_name: str
    pedigree: str
    entry_number: int
    source_nursery: str = ""
    selection_decision: Optional[SelectionDecision] = None
    selection_notes: str = ""
    seed_harvested_g: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "nursery_id": self.nursery_id,
            "genotype_id": self.genotype_id,
            "genotype_name": self.genotype_name,
            "pedigree": self.pedigree,
            "entry_number": self.entry_number,
            "source_nursery": self.source_nursery,
            "selection_decision": self.selection_decision.value if self.selection_decision else None,
            "selection_notes": self.selection_notes,
            "seed_harvested_g": self.seed_harvested_g,
        }


@dataclass
class Nursery:
    """Breeding nursery"""
    nursery_id: str
    name: str
    nursery_type: NurseryType
    season: str
    year: int
    location: str
    sowing_date: Optional[date] = None
    harvest_date: Optional[date] = None
    entries: List[str] = None  # entry_ids
    status: str = "planned"  # planned, active, completed
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nursery_id": self.nursery_id,
            "name": self.name,
            "nursery_type": self.nursery_type.value,
            "season": self.season,
            "year": self.year,
            "location": self.location,
            "sowing_date": self.sowing_date.isoformat() if self.sowing_date else None,
            "harvest_date": self.harvest_date.isoformat() if self.harvest_date else None,
            "entry_count": len(self.entries) if self.entries else 0,
            "status": self.status,
            "notes": self.notes,
        }


class NurseryService:
    """
    Nursery management for plant breeding
    """
    
    def __init__(self):
        self.nurseries: Dict[str, Nursery] = {}
        self.entries: Dict[str, NurseryEntry] = {}
        self._nursery_counter = 0
        self._entry_counter = 0
    
    def create_nursery(
        self,
        name: str,
        nursery_type: str,
        season: str,
        year: int,
        location: str,
        sowing_date: Optional[str] = None,
        notes: str = ""
    ) -> Nursery:
        """Create a new nursery"""
        self._nursery_counter += 1
        nursery_id = f"NUR-{year}-{self._nursery_counter:04d}"
        
        nursery = Nursery(
            nursery_id=nursery_id,
            name=name,
            nursery_type=NurseryType(nursery_type),
            season=season,
            year=year,
            location=location,
            sowing_date=date.fromisoformat(sowing_date) if sowing_date else None,
            entries=[],
            notes=notes,
        )
        
        self.nurseries[nursery_id] = nursery
        return nursery
    
    def add_entry(
        self,
        nursery_id: str,
        genotype_id: str,
        genotype_name: str,
        pedigree: str = "",
        source_nursery: str = ""
    ) -> NurseryEntry:
        """Add an entry to a nursery"""
        if nursery_id not in self.nurseries:
            raise ValueError(f"Nursery {nursery_id} not found")
        
        nursery = self.nurseries[nursery_id]
        
        self._entry_counter += 1
        entry_id = f"ENT-{self._entry_counter:06d}"
        entry_number = len(nursery.entries) + 1
        
        entry = NurseryEntry(
            entry_id=entry_id,
            nursery_id=nursery_id,
            genotype_id=genotype_id,
            genotype_name=genotype_name,
            pedigree=pedigree,
            entry_number=entry_number,
            source_nursery=source_nursery,
        )
        
        self.entries[entry_id] = entry
        nursery.entries.append(entry_id)
        
        return entry
    
    def bulk_add_entries(
        self,
        nursery_id: str,
        entries_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add multiple entries to a nursery"""
        added = 0
        errors = []
        
        for data in entries_data:
            try:
                self.add_entry(
                    nursery_id=nursery_id,
                    genotype_id=data.get("genotype_id", ""),
                    genotype_name=data.get("genotype_name", ""),
                    pedigree=data.get("pedigree", ""),
                    source_nursery=data.get("source_nursery", ""),
                )
                added += 1
            except Exception as e:
                errors.append({"data": data, "error": str(e)})
        
        return {
            "added": added,
            "errors": len(errors),
            "error_details": errors[:10],
        }
    
    def record_selection(
        self,
        entry_id: str,
        decision: str,
        notes: str = "",
        seed_harvested: float = 0.0
    ) -> NurseryEntry:
        """Record selection decision for an entry"""
        if entry_id not in self.entries:
            raise ValueError(f"Entry {entry_id} not found")
        
        entry = self.entries[entry_id]
        entry.selection_decision = SelectionDecision(decision)
        entry.selection_notes = notes
        entry.seed_harvested_g = seed_harvested
        
        return entry
    
    def advance_selections(
        self,
        source_nursery_id: str,
        target_nursery_id: str
    ) -> Dict[str, Any]:
        """Advance selected entries to next nursery"""
        if source_nursery_id not in self.nurseries:
            raise ValueError(f"Source nursery {source_nursery_id} not found")
        if target_nursery_id not in self.nurseries:
            raise ValueError(f"Target nursery {target_nursery_id} not found")
        
        source = self.nurseries[source_nursery_id]
        advanced = 0
        
        for entry_id in source.entries:
            entry = self.entries[entry_id]
            if entry.selection_decision == SelectionDecision.ADVANCE:
                self.add_entry(
                    nursery_id=target_nursery_id,
                    genotype_id=entry.genotype_id,
                    genotype_name=entry.genotype_name,
                    pedigree=entry.pedigree,
                    source_nursery=source_nursery_id,
                )
                advanced += 1
        
        return {
            "source_nursery": source_nursery_id,
            "target_nursery": target_nursery_id,
            "entries_advanced": advanced,
        }
    
    def update_nursery_status(
        self,
        nursery_id: str,
        status: str,
        harvest_date: Optional[str] = None
    ) -> Nursery:
        """Update nursery status"""
        if nursery_id not in self.nurseries:
            raise ValueError(f"Nursery {nursery_id} not found")
        
        nursery = self.nurseries[nursery_id]
        nursery.status = status
        
        if harvest_date:
            nursery.harvest_date = date.fromisoformat(harvest_date)
        
        return nursery
    
    def get_nursery(self, nursery_id: str) -> Optional[Dict[str, Any]]:
        """Get nursery details with entries"""
        if nursery_id not in self.nurseries:
            return None
        
        nursery = self.nurseries[nursery_id]
        entries = [self.entries[eid].to_dict() for eid in nursery.entries]
        
        return {
            **nursery.to_dict(),
            "entries": entries,
        }
    
    def list_nurseries(
        self,
        year: Optional[int] = None,
        nursery_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List nurseries with optional filters"""
        result = []
        for nursery in self.nurseries.values():
            if year and nursery.year != year:
                continue
            if nursery_type and nursery.nursery_type.value != nursery_type:
                continue
            if status and nursery.status != status:
                continue
            result.append(nursery.to_dict())
        return result
    
    def get_nursery_summary(self, nursery_id: str) -> Dict[str, Any]:
        """Get selection summary for a nursery"""
        if nursery_id not in self.nurseries:
            raise ValueError(f"Nursery {nursery_id} not found")
        
        nursery = self.nurseries[nursery_id]
        
        decisions = {"advance": 0, "reject": 0, "hold": 0, "release": 0, "pending": 0}
        total_seed = 0.0
        
        for entry_id in nursery.entries:
            entry = self.entries[entry_id]
            if entry.selection_decision:
                decisions[entry.selection_decision.value] += 1
            else:
                decisions["pending"] += 1
            total_seed += entry.seed_harvested_g
        
        return {
            "nursery_id": nursery_id,
            "name": nursery.name,
            "total_entries": len(nursery.entries),
            "selection_summary": decisions,
            "selection_rate_percent": round(decisions["advance"] / len(nursery.entries) * 100, 1) if nursery.entries else 0,
            "total_seed_harvested_g": round(total_seed, 1),
        }


# Singleton
_nursery_service: Optional[NurseryService] = None


def get_nursery_service() -> NurseryService:
    """Get or create nursery service singleton"""
    global _nursery_service
    if _nursery_service is None:
        _nursery_service = NurseryService()
    return _nursery_service
