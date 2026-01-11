"""
Performance Ranking Service
Rank breeding entries by performance metrics
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random


class PerformanceRankingService:
    """Service for ranking breeding entries by performance"""

    def __init__(self):
        # In-memory storage (would be database in production)
        self.entries: Dict[str, Dict[str, Any]] = {}
        self.ranking_history: List[Dict[str, Any]] = []
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize with demo ranking data"""
        demo_entries = [
            {
                "id": "entry-001",
                "entry_id": "BM-2025-045",
                "name": "Elite Line 45",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F7",
                "yield": 7.2,
                "yield_rank": 1,
                "gebv": 2.45,
                "gebv_rank": 1,
                "traits": ["High yield", "Disease resistant", "Lodging tolerant"],
                "score": 95,
                "previous_score": 92,
                "previous_rank": 2,
                "observations": {
                    "plant_height": 98,
                    "days_to_maturity": 115,
                    "grain_quality": "Premium",
                    "disease_score": 1
                }
            },
            {
                "id": "entry-002",
                "entry_id": "BM-2025-023",
                "name": "Elite Line 23",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F6",
                "yield": 6.9,
                "yield_rank": 2,
                "gebv": 2.38,
                "gebv_rank": 2,
                "traits": ["Drought tolerant", "Early maturity"],
                "score": 92,
                "previous_score": 94,
                "previous_rank": 1,
                "observations": {
                    "plant_height": 95,
                    "days_to_maturity": 105,
                    "grain_quality": "Good",
                    "disease_score": 2
                }
            },
            {
                "id": "entry-003",
                "entry_id": "BM-2025-089",
                "name": "Elite Line 89",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F7",
                "yield": 6.7,
                "yield_rank": 3,
                "gebv": 2.31,
                "gebv_rank": 3,
                "traits": ["Quality", "High yield", "Wide adaptation"],
                "score": 89,
                "previous_score": 89,
                "previous_rank": 3,
                "observations": {
                    "plant_height": 102,
                    "days_to_maturity": 120,
                    "grain_quality": "Premium",
                    "disease_score": 2
                }
            },
            {
                "id": "entry-004",
                "entry_id": "BM-2025-012",
                "name": "Elite Line 12",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F6",
                "yield": 6.5,
                "yield_rank": 4,
                "gebv": 2.28,
                "gebv_rank": 4,
                "traits": ["Disease resistant", "Good tillering"],
                "score": 86,
                "previous_score": 82,
                "previous_rank": 6,
                "observations": {
                    "plant_height": 100,
                    "days_to_maturity": 118,
                    "grain_quality": "Good",
                    "disease_score": 1
                }
            },
            {
                "id": "entry-005",
                "entry_id": "BM-2025-067",
                "name": "Elite Line 67",
                "program_id": "prog-002",
                "program_name": "Wheat Breeding Program",
                "trial_id": "trial-2025-002",
                "trial_name": "Multi-Location Trial 2025",
                "generation": "F8",
                "yield": 5.8,
                "yield_rank": 1,
                "gebv": 2.15,
                "gebv_rank": 1,
                "traits": ["Wide adaptation", "Heat tolerant"],
                "score": 84,
                "previous_score": 85,
                "previous_rank": 4,
                "observations": {
                    "plant_height": 85,
                    "days_to_maturity": 125,
                    "grain_quality": "Good",
                    "disease_score": 2
                }
            },
            {
                "id": "entry-006",
                "entry_id": "BM-2025-034",
                "name": "Elite Line 34",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F5",
                "yield": 6.3,
                "yield_rank": 5,
                "gebv": 2.08,
                "gebv_rank": 5,
                "traits": ["Early maturity", "Short duration"],
                "score": 82,
                "previous_score": 83,
                "previous_rank": 5,
                "observations": {
                    "plant_height": 90,
                    "days_to_maturity": 100,
                    "grain_quality": "Medium",
                    "disease_score": 3
                }
            },
            {
                "id": "entry-007",
                "entry_id": "BM-2025-078",
                "name": "Elite Line 78",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F6",
                "yield": 6.2,
                "yield_rank": 6,
                "gebv": 1.95,
                "gebv_rank": 6,
                "traits": ["Stress tolerant", "Submergence tolerant"],
                "score": 80,
                "previous_score": 78,
                "previous_rank": 8,
                "observations": {
                    "plant_height": 105,
                    "days_to_maturity": 130,
                    "grain_quality": "Good",
                    "disease_score": 2
                }
            },
            {
                "id": "entry-008",
                "entry_id": "BM-2025-056",
                "name": "Elite Line 56",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F5",
                "yield": 6.1,
                "yield_rank": 7,
                "gebv": 1.82,
                "gebv_rank": 7,
                "traits": ["Quality", "Aromatic"],
                "score": 78,
                "previous_score": 79,
                "previous_rank": 7,
                "observations": {
                    "plant_height": 110,
                    "days_to_maturity": 135,
                    "grain_quality": "Premium",
                    "disease_score": 3
                }
            },
            {
                "id": "entry-009",
                "entry_id": "BM-2025-091",
                "name": "Elite Line 91",
                "program_id": "prog-002",
                "program_name": "Wheat Breeding Program",
                "trial_id": "trial-2025-002",
                "trial_name": "Multi-Location Trial 2025",
                "generation": "F7",
                "yield": 5.5,
                "yield_rank": 2,
                "gebv": 2.02,
                "gebv_rank": 2,
                "traits": ["Rust resistant", "High protein"],
                "score": 76,
                "previous_score": 74,
                "previous_rank": 10,
                "observations": {
                    "plant_height": 80,
                    "days_to_maturity": 120,
                    "grain_quality": "Good",
                    "disease_score": 1
                }
            },
            {
                "id": "entry-010",
                "entry_id": "BM-2025-103",
                "name": "Elite Line 103",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "generation": "F4",
                "yield": 5.9,
                "yield_rank": 8,
                "gebv": 1.75,
                "gebv_rank": 8,
                "traits": ["Salt tolerant", "Coastal adaptation"],
                "score": 74,
                "previous_score": 75,
                "previous_rank": 9,
                "observations": {
                    "plant_height": 115,
                    "days_to_maturity": 140,
                    "grain_quality": "Medium",
                    "disease_score": 2
                }
            }
        ]

        for entry in demo_entries:
            self.entries[entry["id"]] = entry

    def get_rankings(
        self,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        sort_by: str = "score",
        limit: int = 50,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get ranked entries with optional filters"""
        results = list(self.entries.values())

        # Apply filters
        if program_id:
            results = [e for e in results if e.get("program_id") == program_id]
        if trial_id:
            results = [e for e in results if e.get("trial_id") == trial_id]
        if search:
            search_lower = search.lower()
            results = [e for e in results if 
                search_lower in e.get("name", "").lower() or
                search_lower in e.get("entry_id", "").lower() or
                any(search_lower in t.lower() for t in e.get("traits", []))
            ]

        # Sort
        sort_key = {
            "score": lambda x: x.get("score", 0),
            "yield": lambda x: x.get("yield", 0),
            "gebv": lambda x: x.get("gebv", 0),
            "name": lambda x: x.get("name", ""),
        }.get(sort_by, lambda x: x.get("score", 0))

        results.sort(key=sort_key, reverse=(sort_by != "name"))

        # Assign ranks
        for i, entry in enumerate(results):
            entry["rank"] = i + 1

        return results[:limit]

    def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a single entry by ID"""
        return self.entries.get(entry_id)

    def get_top_performers(
        self,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get top performing entries (podium)"""
        return self.get_rankings(
            program_id=program_id,
            trial_id=trial_id,
            sort_by="score",
            limit=limit,
        )

    def get_statistics(
        self,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get ranking statistics"""
        entries = self.get_rankings(program_id=program_id, trial_id=trial_id, limit=1000)

        if not entries:
            return {
                "total_entries": 0,
                "avg_score": 0,
                "avg_yield": 0,
                "avg_gebv": 0,
                "top_performer": None,
                "most_improved": None
            }

        # Calculate averages
        avg_score = sum(e["score"] for e in entries) / len(entries)
        avg_yield = sum(e["yield"] for e in entries) / len(entries)
        avg_gebv = sum(e["gebv"] for e in entries) / len(entries)

        # Find most improved (biggest rank improvement)
        most_improved = max(entries, key=lambda x: x.get("previous_rank", x["rank"]) - x["rank"])

        return {
            "total_entries": len(entries),
            "avg_score": round(avg_score, 1),
            "avg_yield": round(avg_yield, 2),
            "avg_gebv": round(avg_gebv, 2),
            "top_performer": entries[0]["name"] if entries else None,
            "most_improved": {
                "name": most_improved["name"],
                "improvement": most_improved.get("previous_rank", most_improved["rank"]) - most_improved["rank"]
            } if most_improved else None
        }

    def get_programs(self) -> List[Dict[str, str]]:
        """Get unique programs from entries"""
        programs = {}
        for e in self.entries.values():
            pid = e.get("program_id")
            if pid and pid not in programs:
                programs[pid] = {
                    "id": pid,
                    "name": e.get("program_name", pid),
                }
        return list(programs.values())

    def get_trials(self, program_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Get unique trials from entries"""
        trials = {}
        for e in self.entries.values():
            if program_id and e.get("program_id") != program_id:
                continue
            tid = e.get("trial_id")
            if tid and tid not in trials:
                trials[tid] = {
                    "id": tid,
                    "name": e.get("trial_name", tid),
                    "program_id": e.get("program_id"),
                }
        return list(trials.values())

    def compare_entries(self, entry_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple entries side by side"""
        entries = [self.entries.get(eid) for eid in entry_ids if eid in self.entries]

        if len(entries) < 2:
            return {"error": "Need at least 2 entries to compare"}

        # Find best values for each metric
        best_yield = max(e["yield"] for e in entries)
        best_gebv = max(e["gebv"] for e in entries)
        best_score = max(e["score"] for e in entries)

        comparison = []
        for entry in entries:
            comparison.append({
                "id": entry["id"],
                "entry_id": entry["entry_id"],
                "name": entry["name"],
                "rank": entry.get("rank", 0),
                "yield": entry["yield"],
                "yield_is_best": entry["yield"] == best_yield,
                "gebv": entry["gebv"],
                "gebv_is_best": entry["gebv"] == best_gebv,
                "score": entry["score"],
                "score_is_best": entry["score"] == best_score,
                "traits": entry["traits"],
                "observations": entry.get("observations", {})
            })

        return {
            "entries": comparison,
            "best_yield": best_yield,
            "best_gebv": best_gebv,
            "best_score": best_score
        }


# Singleton instance
performance_ranking_service = PerformanceRankingService()
