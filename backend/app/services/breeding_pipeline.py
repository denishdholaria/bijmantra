"""
Breeding Pipeline Service

Tracks germplasm flow through breeding stages from crosses to variety release.
"""

from typing import Optional
from datetime import datetime, date


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

# Demo pipeline entries
DEMO_ENTRIES = [
    {
        "id": "BM-2024-001",
        "name": "IR-HYB-2024-A",
        "pedigree": "IR64 / Swarna",
        "current_stage": "AYT",
        "program_id": "prog-001",
        "program_name": "Rice Improvement",
        "crop": "Rice",
        "year": 2024,
        "status": "active",
        "traits": ["High Yield", "Blast Resistant", "Short Duration"],
        "notes": "Promising line with 15% yield advantage",
        "created_at": "2021-06-01",
        "updated_at": "2024-06-15",
        "stage_history": [
            {"stage": "F1", "date": "2021-06", "decision": "Advanced", "notes": "Good seed set"},
            {"stage": "F2", "date": "2021-11", "decision": "Advanced", "notes": "Selected 50 plants"},
            {"stage": "F3-F5", "date": "2022-06", "decision": "Advanced", "notes": "Fixed for target traits"},
            {"stage": "PYT", "date": "2023-06", "decision": "Advanced", "notes": "Top 10% yield"},
            {"stage": "AYT", "date": "2024-06", "decision": "In Progress", "notes": "Testing in 3 locations"},
        ],
    },
    {
        "id": "BM-2024-002",
        "name": "WH-DUR-2024-B",
        "pedigree": "HD2967 / PBW343",
        "current_stage": "MLT",
        "program_id": "prog-002",
        "program_name": "Wheat Improvement",
        "crop": "Wheat",
        "year": 2024,
        "status": "active",
        "traits": ["Rust Resistant", "Heat Tolerant", "High Protein"],
        "notes": "Excellent rust resistance, testing in 5 locations",
        "created_at": "2020-11-01",
        "updated_at": "2024-11-10",
        "stage_history": [
            {"stage": "F1", "date": "2020-11", "decision": "Advanced", "notes": "Cross successful"},
            {"stage": "F2", "date": "2021-04", "decision": "Advanced", "notes": "Good segregation"},
            {"stage": "F3-F5", "date": "2021-11", "decision": "Advanced", "notes": "Rust screening done"},
            {"stage": "PYT", "date": "2022-11", "decision": "Advanced", "notes": "12% yield advantage"},
            {"stage": "AYT", "date": "2023-11", "decision": "Advanced", "notes": "Consistent performance"},
            {"stage": "MLT", "date": "2024-11", "decision": "In Progress", "notes": "5 locations"},
        ],
    },
    {
        "id": "BM-2024-003",
        "name": "MZ-QPM-2024-C",
        "pedigree": "CML144 / CML159",
        "current_stage": "PYT",
        "program_id": "prog-003",
        "program_name": "Maize Improvement",
        "crop": "Maize",
        "year": 2024,
        "status": "active",
        "traits": ["QPM", "Drought Tolerant", "Early Maturity"],
        "notes": "Quality Protein Maize with good combining ability",
        "created_at": "2022-06-01",
        "updated_at": "2024-06-20",
        "stage_history": [
            {"stage": "F1", "date": "2022-06", "decision": "Advanced", "notes": "Hybrid made"},
            {"stage": "F2", "date": "2022-11", "decision": "Advanced", "notes": "Inbred development"},
            {"stage": "F3-F5", "date": "2023-06", "decision": "Advanced", "notes": "QPM confirmed"},
            {"stage": "PYT", "date": "2024-06", "decision": "In Progress", "notes": "First yield trial"},
        ],
    },
    {
        "id": "BM-2023-015",
        "name": "IR-SUB-2023-D",
        "pedigree": "Swarna-Sub1 / FR13A",
        "current_stage": "RELEASE",
        "program_id": "prog-001",
        "program_name": "Rice Improvement",
        "crop": "Rice",
        "year": 2023,
        "status": "released",
        "traits": ["Submergence Tolerant", "High Yield", "Good Grain Quality"],
        "notes": "Released as 'Bijmantra Sub-1' in 2024",
        "created_at": "2018-06-01",
        "updated_at": "2024-01-15",
        "stage_history": [
            {"stage": "F1", "date": "2018-06", "decision": "Advanced", "notes": "Sub1 introgression"},
            {"stage": "F2", "date": "2018-11", "decision": "Advanced", "notes": "MAS for Sub1A"},
            {"stage": "F3-F5", "date": "2019-06", "decision": "Advanced", "notes": "BC2F4 selected"},
            {"stage": "PYT", "date": "2020-06", "decision": "Advanced", "notes": "Submergence tested"},
            {"stage": "AYT", "date": "2021-06", "decision": "Advanced", "notes": "14 days submergence"},
            {"stage": "MLT", "date": "2022-06", "decision": "Advanced", "notes": "8 locations"},
            {"stage": "RELEASE", "date": "2024-01", "decision": "Released", "notes": "Official release"},
        ],
    },
    {
        "id": "BM-2024-004",
        "name": "SB-OIL-2024-E",
        "pedigree": "JS335 / NRC37",
        "current_stage": "F3-F5",
        "program_id": "prog-004",
        "program_name": "Soybean Improvement",
        "crop": "Soybean",
        "year": 2024,
        "status": "active",
        "traits": ["High Oil", "Pod Shattering Resistant"],
        "notes": "Selection for oil content ongoing",
        "created_at": "2023-06-01",
        "updated_at": "2024-06-10",
        "stage_history": [
            {"stage": "F1", "date": "2023-06", "decision": "Advanced", "notes": "Cross made"},
            {"stage": "F2", "date": "2023-11", "decision": "Advanced", "notes": "200 plants selected"},
            {"stage": "F3-F5", "date": "2024-06", "decision": "In Progress", "notes": "Oil analysis ongoing"},
        ],
    },
    {
        "id": "BM-2024-005",
        "name": "IR-SALT-2024-F",
        "pedigree": "FL478 / IR64",
        "current_stage": "F2",
        "program_id": "prog-001",
        "program_name": "Rice Improvement",
        "crop": "Rice",
        "year": 2024,
        "status": "active",
        "traits": ["Salt Tolerant", "High Yield"],
        "notes": "Saltol introgression into IR64 background",
        "created_at": "2024-01-01",
        "updated_at": "2024-06-01",
        "stage_history": [
            {"stage": "F1", "date": "2024-01", "decision": "Advanced", "notes": "Cross successful"},
            {"stage": "F2", "date": "2024-06", "decision": "In Progress", "notes": "MAS screening"},
        ],
    },
    {
        "id": "BM-2024-006",
        "name": "WH-HEAT-2024-G",
        "pedigree": "DBW187 / HD3086",
        "current_stage": "F1",
        "program_id": "prog-002",
        "program_name": "Wheat Improvement",
        "crop": "Wheat",
        "year": 2024,
        "status": "active",
        "traits": ["Heat Tolerant", "Terminal Heat Escape"],
        "notes": "New cross for heat tolerance",
        "created_at": "2024-11-01",
        "updated_at": "2024-11-15",
        "stage_history": [
            {"stage": "F1", "date": "2024-11", "decision": "In Progress", "notes": "F1 seeds harvested"},
        ],
    },
    {
        "id": "BM-2023-020",
        "name": "MZ-MLN-2023-H",
        "pedigree": "CML442 / CML312",
        "current_stage": "AYT",
        "program_id": "prog-003",
        "program_name": "Maize Improvement",
        "crop": "Maize",
        "year": 2023,
        "status": "dropped",
        "traits": ["MLN Resistant", "High Yield"],
        "notes": "Dropped due to susceptibility to fall armyworm",
        "created_at": "2020-06-01",
        "updated_at": "2024-03-15",
        "stage_history": [
            {"stage": "F1", "date": "2020-06", "decision": "Advanced", "notes": "Cross made"},
            {"stage": "F2", "date": "2020-11", "decision": "Advanced", "notes": "MLN screening"},
            {"stage": "F3-F5", "date": "2021-06", "decision": "Advanced", "notes": "MLN resistant"},
            {"stage": "PYT", "date": "2022-06", "decision": "Advanced", "notes": "Good yield"},
            {"stage": "AYT", "date": "2023-06", "decision": "Dropped", "notes": "FAW susceptible"},
        ],
    },
]


class BreedingPipelineService:
    """Service for managing breeding pipeline entries."""
    
    def __init__(self):
        self.entries = DEMO_ENTRIES.copy()
    
    def get_stages(self) -> list[dict]:
        """Get all pipeline stages."""
        return PIPELINE_STAGES
    
    def list_entries(
        self,
        stage: Optional[str] = None,
        crop: Optional[str] = None,
        program_id: Optional[str] = None,
        status: Optional[str] = None,
        year: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List pipeline entries with filters."""
        filtered = self.entries.copy()
        
        if stage:
            filtered = [e for e in filtered if e["current_stage"] == stage]
        if crop:
            filtered = [e for e in filtered if e["crop"].lower() == crop.lower()]
        if program_id:
            filtered = [e for e in filtered if e["program_id"] == program_id]
        if status:
            filtered = [e for e in filtered if e["status"] == status]
        if year:
            filtered = [e for e in filtered if e["year"] == year]
        if search:
            search_lower = search.lower()
            filtered = [
                e for e in filtered
                if search_lower in e["name"].lower()
                or search_lower in e["pedigree"].lower()
                or search_lower in e["id"].lower()
            ]
        
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        
        return {
            "data": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    def get_entry(self, entry_id: str) -> Optional[dict]:
        """Get a single pipeline entry by ID."""
        for entry in self.entries:
            if entry["id"] == entry_id:
                return entry
        return None
    
    def get_statistics(
        self,
        program_id: Optional[str] = None,
        crop: Optional[str] = None,
    ) -> dict:
        """Get pipeline statistics."""
        filtered = self.entries.copy()
        
        if program_id:
            filtered = [e for e in filtered if e["program_id"] == program_id]
        if crop:
            filtered = [e for e in filtered if e["crop"].lower() == crop.lower()]
        
        # Count by status
        active = len([e for e in filtered if e["status"] == "active"])
        released = len([e for e in filtered if e["status"] == "released"])
        dropped = len([e for e in filtered if e["status"] == "dropped"])
        
        # Count by stage
        stage_counts = {}
        for stage in PIPELINE_STAGES:
            stage_counts[stage["id"]] = len([
                e for e in filtered 
                if e["current_stage"] == stage["id"] and e["status"] == "active"
            ])
        
        # Count by crop
        crop_counts = {}
        for entry in filtered:
            crop_name = entry["crop"]
            crop_counts[crop_name] = crop_counts.get(crop_name, 0) + 1
        
        # Calculate average pipeline time for released varieties
        released_entries = [e for e in filtered if e["status"] == "released"]
        avg_years = 0
        if released_entries:
            total_years = 0
            for entry in released_entries:
                if entry["stage_history"]:
                    first_date = entry["stage_history"][0]["date"]
                    last_date = entry["stage_history"][-1]["date"]
                    # Parse year-month format
                    first_year = int(first_date.split("-")[0])
                    last_year = int(last_date.split("-")[0])
                    total_years += (last_year - first_year)
            avg_years = round(total_years / len(released_entries), 1) if released_entries else 0
        
        return {
            "total_entries": len(filtered),
            "active": active,
            "released": released,
            "dropped": dropped,
            "stage_counts": stage_counts,
            "crop_counts": crop_counts,
            "avg_years_to_release": avg_years,
            "crops": list(crop_counts.keys()),
        }
    
    def get_stage_summary(self) -> list[dict]:
        """Get summary of entries at each stage."""
        summary = []
        for stage in PIPELINE_STAGES:
            entries_at_stage = [
                e for e in self.entries 
                if e["current_stage"] == stage["id"] and e["status"] == "active"
            ]
            summary.append({
                "stage_id": stage["id"],
                "stage_name": stage["name"],
                "order": stage["order"],
                "count": len(entries_at_stage),
                "entries": [
                    {"id": e["id"], "name": e["name"], "crop": e["crop"]}
                    for e in entries_at_stage[:5]  # Top 5 entries
                ],
            })
        return summary
    
    def create_entry(self, data: dict) -> dict:
        """Create a new pipeline entry."""
        entry_id = f"BM-{datetime.now().year}-{len(self.entries) + 1:03d}"
        
        new_entry = {
            "id": entry_id,
            "name": data["name"],
            "pedigree": data["pedigree"],
            "current_stage": data.get("current_stage", "F1"),
            "program_id": data.get("program_id", "prog-001"),
            "program_name": data.get("program_name", "Unknown Program"),
            "crop": data["crop"],
            "year": data.get("year", datetime.now().year),
            "status": "active",
            "traits": data.get("traits", []),
            "notes": data.get("notes", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stage_history": [
                {
                    "stage": data.get("current_stage", "F1"),
                    "date": datetime.now().strftime("%Y-%m"),
                    "decision": "In Progress",
                    "notes": data.get("notes", "Entry created"),
                }
            ],
        }
        
        self.entries.append(new_entry)
        return new_entry
    
    def advance_stage(self, entry_id: str, decision: str, notes: str = "") -> Optional[dict]:
        """Advance an entry to the next stage."""
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        
        current_stage_idx = next(
            (i for i, s in enumerate(PIPELINE_STAGES) if s["id"] == entry["current_stage"]),
            -1
        )
        
        if current_stage_idx < 0 or current_stage_idx >= len(PIPELINE_STAGES) - 1:
            return None  # Already at last stage or invalid
        
        # Update current stage history
        if entry["stage_history"]:
            entry["stage_history"][-1]["decision"] = decision
            if notes:
                entry["stage_history"][-1]["notes"] = notes
        
        if decision == "Advanced":
            # Move to next stage
            next_stage = PIPELINE_STAGES[current_stage_idx + 1]
            entry["current_stage"] = next_stage["id"]
            entry["stage_history"].append({
                "stage": next_stage["id"],
                "date": datetime.now().strftime("%Y-%m"),
                "decision": "In Progress",
                "notes": "",
            })
            
            # Check if released
            if next_stage["id"] == "RELEASE":
                entry["status"] = "released"
        elif decision == "Dropped":
            entry["status"] = "dropped"
        
        entry["updated_at"] = datetime.now().isoformat()
        return entry
    
    def get_crops(self) -> list[str]:
        """Get list of unique crops in the pipeline."""
        return list(set(e["crop"] for e in self.entries))
    
    def get_programs(self) -> list[dict]:
        """Get list of unique programs."""
        programs = {}
        for entry in self.entries:
            if entry["program_id"] not in programs:
                programs[entry["program_id"]] = {
                    "id": entry["program_id"],
                    "name": entry["program_name"],
                }
        return list(programs.values())


# Singleton instance
_service = None

def get_breeding_pipeline_service() -> BreedingPipelineService:
    """Get the breeding pipeline service singleton."""
    global _service
    if _service is None:
        _service = BreedingPipelineService()
    return _service
