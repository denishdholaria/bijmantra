"""
Quick Entry Service
Rapid data entry for common breeding tasks - germplasm, observations, crosses, trials
"""
from datetime import datetime, UTC, timedelta
from typing import Optional
from uuid import uuid4


class QuickEntryService:
    """Service for quick data entry operations."""

    def __init__(self):
        self._entries: dict[str, dict] = {}
        self._session_stats: dict[str, int] = {
            "germplasm": 0,
            "observation": 0,
            "cross": 0,
            "trial": 0,
        }
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize demo entries."""
        base_time = datetime.now(UTC) - timedelta(hours=2)
        
        demo_entries = [
            {
                "id": "qe-001",
                "type": "germplasm",
                "data": {
                    "germplasm_name": "IR64-Sub1",
                    "accession_number": "ACC-2025-001",
                    "species": "Oryza sativa",
                    "country_of_origin": "Philippines",
                    "pedigree": "IR5657-33-2-1/IR2061-465-1-5-5",
                },
                "created_at": (base_time + timedelta(minutes=5)).isoformat(),
                "created_by": "demo@bijmantra.org",
            },
            {
                "id": "qe-002",
                "type": "observation",
                "data": {
                    "study_id": "study-001",
                    "observation_unit_id": "ou-001",
                    "trait": "Grain Yield",
                    "value": 6.5,
                    "unit": "t/ha",
                },
                "created_at": (base_time + timedelta(minutes=10)).isoformat(),
                "created_by": "demo@bijmantra.org",
            },
            {
                "id": "qe-003",
                "type": "cross",
                "data": {
                    "female_parent": "IR64",
                    "male_parent": "FR13A",
                    "cross_date": "2025-12-20",
                    "seeds_obtained": 45,
                },
                "created_at": (base_time + timedelta(minutes=30)).isoformat(),
                "created_by": "demo@bijmantra.org",
            },
        ]
        
        for entry in demo_entries:
            self._entries[entry["id"]] = entry
            self._session_stats[entry["type"]] += 1

    def create_entry(self, entry_type: str, data: dict, created_by: str = "system") -> dict:
        """Create a new quick entry."""
        entry_id = f"qe-{uuid4().hex[:8]}"
        
        entry = {
            "id": entry_id,
            "type": entry_type,
            "data": data,
            "created_at": datetime.now(UTC).isoformat(),
            "created_by": created_by,
            "status": "saved",
        }
        
        self._entries[entry_id] = entry
        self._session_stats[entry_type] = self._session_stats.get(entry_type, 0) + 1
        
        return entry

    def get_entries(
        self,
        entry_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get quick entries with optional type filter."""
        entries = list(self._entries.values())
        
        if entry_type:
            entries = [e for e in entries if e["type"] == entry_type]
        
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        total = len(entries)
        entries = entries[offset:offset + limit]
        
        return {
            "entries": entries,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_entry(self, entry_id: str) -> Optional[dict]:
        """Get a single entry by ID."""
        return self._entries.get(entry_id)

    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry."""
        if entry_id in self._entries:
            entry = self._entries[entry_id]
            entry_type = entry.get("type")
            if entry_type in self._session_stats:
                self._session_stats[entry_type] = max(0, self._session_stats[entry_type] - 1)
            del self._entries[entry_id]
            return True
        return False

    def get_session_stats(self) -> dict:
        """Get session statistics."""
        entries = list(self._entries.values())
        
        # Calculate recent activity
        now = datetime.now(UTC)
        recent_cutoff = (now - timedelta(hours=1)).isoformat()
        
        recent_by_type = {}
        for entry in entries:
            entry_type = entry.get("type")
            if entry.get("created_at", "") >= recent_cutoff:
                recent_by_type[entry_type] = recent_by_type.get(entry_type, 0) + 1
        
        # Get last entry time per type
        last_entry_by_type = {}
        for entry in entries:
            entry_type = entry.get("type")
            created_at = entry.get("created_at", "")
            if entry_type not in last_entry_by_type or created_at > last_entry_by_type[entry_type]:
                last_entry_by_type[entry_type] = created_at
        
        return {
            "total_entries": len(entries),
            "by_type": self._session_stats,
            "recent_by_type": recent_by_type,
            "last_entry_by_type": last_entry_by_type,
        }

    def get_recent_activity(self) -> list[dict]:
        """Get recent activity summary for dashboard."""
        entries = list(self._entries.values())
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Group by type
        type_summary = {}
        for entry in entries:
            entry_type = entry.get("type")
            if entry_type not in type_summary:
                type_summary[entry_type] = {
                    "type": entry_type,
                    "count": 0,
                    "last_entry": None,
                }
            type_summary[entry_type]["count"] += 1
            if type_summary[entry_type]["last_entry"] is None:
                type_summary[entry_type]["last_entry"] = entry.get("created_at")
        
        return list(type_summary.values())

    def get_dropdown_options(self, option_type: str) -> list[dict]:
        """Get dropdown options for quick entry forms."""
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
            "germplasm": [
                {"value": "IR64", "label": "IR64"},
                {"value": "Swarna", "label": "Swarna"},
                {"value": "FR13A", "label": "FR13A"},
                {"value": "Pokkali", "label": "Pokkali"},
                {"value": "Nipponbare", "label": "Nipponbare"},
                {"value": "Kasalath", "label": "Kasalath"},
                {"value": "N22", "label": "N22"},
            ],
        }
        return options.get(option_type, [])


# Singleton instance
quick_entry_service = QuickEntryService()
