"""
Selection Decisions Service
Manage breeding candidate selection decisions (advance/reject/hold)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class SelectionDecisionsService:
    """Service for managing selection decisions on breeding candidates"""

    def __init__(self):
        # In-memory storage (would be database in production)
        self.candidates: Dict[str, Dict[str, Any]] = {}
        self.decisions: Dict[str, Dict[str, Any]] = {}
        self.decision_history: List[Dict[str, Any]] = []
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize with demo candidates"""
        demo_candidates = [
            {
                "id": "cand-001",
                "name": "BM-2025-001",
                "germplasm_id": "germ-001",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "generation": "F6",
                "gebv": 2.45,
                "yield_estimate": 7.2,
                "traits": ["High yield", "Disease resistant", "Lodging tolerant"],
                "pedigree": "IR64 / Swarna // Sahbhagi Dhan",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "location": "IRRI, Los Baños",
                "created_at": "2025-01-15",
            },
            {
                "id": "cand-002",
                "name": "BM-2025-015",
                "germplasm_id": "germ-015",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "generation": "F6",
                "gebv": 2.38,
                "yield_estimate": 6.9,
                "traits": ["Drought tolerant", "Early maturity", "Good grain quality"],
                "pedigree": "Sahbhagi Dhan / IR64",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "location": "IRRI, Los Baños",
                "created_at": "2025-01-15",
            },
            {
                "id": "cand-003",
                "name": "BM-2025-023",
                "germplasm_id": "germ-023",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "generation": "F5",
                "gebv": 2.31,
                "yield_estimate": 6.7,
                "traits": ["Premium quality", "High yield", "Medium duration"],
                "pedigree": "Basmati 370 / IR64 // Swarna",
                "trial_id": "trial-2025-002",
                "trial_name": "Quality Evaluation Trial 2025",
                "location": "PAU, Ludhiana",
                "created_at": "2025-02-01",
            },
            {
                "id": "cand-004",
                "name": "BM-2025-042",
                "germplasm_id": "germ-042",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "generation": "F6",
                "gebv": 2.28,
                "yield_estimate": 6.5,
                "traits": ["Blast resistant", "BLB resistant", "Good tillering"],
                "pedigree": "Swarna-Sub1 / IR64",
                "trial_id": "trial-2025-001",
                "trial_name": "Advanced Yield Trial 2025",
                "location": "IRRI, Los Baños",
                "created_at": "2025-01-15",
            },
            {
                "id": "cand-005",
                "name": "BM-2025-056",
                "germplasm_id": "germ-056",
                "program_id": "prog-002",
                "program_name": "Wheat Breeding Program",
                "generation": "F7",
                "gebv": 2.15,
                "yield_estimate": 5.8,
                "traits": ["Wide adaptation", "Heat tolerant", "Rust resistant"],
                "pedigree": "HD2967 / PBW343",
                "trial_id": "trial-2025-003",
                "trial_name": "Multi-Location Trial 2025",
                "location": "IARI, New Delhi",
                "created_at": "2025-01-20",
            },
            {
                "id": "cand-006",
                "name": "BM-2025-078",
                "germplasm_id": "germ-078",
                "program_id": "prog-002",
                "program_name": "Wheat Breeding Program",
                "generation": "F6",
                "gebv": 2.08,
                "yield_estimate": 5.5,
                "traits": ["Stress tolerant", "Good protein", "Early maturity"],
                "pedigree": "DBW17 / HD2967",
                "trial_id": "trial-2025-003",
                "trial_name": "Multi-Location Trial 2025",
                "location": "IARI, New Delhi",
                "created_at": "2025-01-20",
            },
            {
                "id": "cand-007",
                "name": "BM-2025-089",
                "germplasm_id": "germ-089",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "generation": "F5",
                "gebv": 1.95,
                "yield_estimate": 6.1,
                "traits": ["Early maturity", "Short duration", "Photoperiod insensitive"],
                "pedigree": "IR64 / MTU1010",
                "trial_id": "trial-2025-002",
                "trial_name": "Quality Evaluation Trial 2025",
                "location": "PAU, Ludhiana",
                "created_at": "2025-02-01",
            },
            {
                "id": "cand-008",
                "name": "BM-2025-102",
                "germplasm_id": "germ-102",
                "program_id": "prog-001",
                "program_name": "Rice Improvement Program",
                "generation": "F4",
                "gebv": 1.82,
                "yield_estimate": 5.8,
                "traits": ["Aromatic", "Long grain", "Premium quality"],
                "pedigree": "Pusa Basmati 1 / IR64",
                "trial_id": "trial-2025-002",
                "trial_name": "Quality Evaluation Trial 2025",
                "location": "PAU, Ludhiana",
                "created_at": "2025-02-01",
            },
            {
                "id": "cand-009",
                "name": "BM-2025-115",
                "germplasm_id": "germ-115",
                "program_id": "prog-003",
                "program_name": "Maize Hybrid Program",
                "generation": "S4",
                "gebv": 2.52,
                "yield_estimate": 9.2,
                "traits": ["High yield", "Stay green", "Drought tolerant"],
                "pedigree": "CML451 / CML312",
                "trial_id": "trial-2025-004",
                "trial_name": "Hybrid Evaluation 2025",
                "location": "CIMMYT, Mexico",
                "created_at": "2025-02-15",
            },
            {
                "id": "cand-010",
                "name": "BM-2025-128",
                "germplasm_id": "germ-128",
                "program_id": "prog-003",
                "program_name": "Maize Hybrid Program",
                "generation": "S3",
                "gebv": 2.41,
                "yield_estimate": 8.8,
                "traits": ["QPM", "High lysine", "Good standability"],
                "pedigree": "CML176 / CML142",
                "trial_id": "trial-2025-004",
                "trial_name": "Hybrid Evaluation 2025",
                "location": "CIMMYT, Mexico",
                "created_at": "2025-02-15",
            },
        ]

        for candidate in demo_candidates:
            self.candidates[candidate["id"]] = candidate

    def list_candidates(
        self,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
        generation: Optional[str] = None,
        decision_status: Optional[str] = None,
        min_gebv: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List selection candidates with optional filters"""
        results = []

        for candidate in self.candidates.values():
            # Apply filters
            if program_id and candidate.get("program_id") != program_id:
                continue
            if trial_id and candidate.get("trial_id") != trial_id:
                continue
            if generation and candidate.get("generation") != generation:
                continue
            if min_gebv and candidate.get("gebv", 0) < min_gebv:
                continue
            if search:
                search_lower = search.lower()
                if not (
                    search_lower in candidate.get("name", "").lower()
                    or search_lower in candidate.get("pedigree", "").lower()
                    or any(search_lower in t.lower() for t in candidate.get("traits", []))
                ):
                    continue

            # Add decision info
            decision = self.decisions.get(candidate["id"])
            candidate_with_decision = {
                **candidate,
                "decision": decision.get("decision") if decision else None,
                "decision_notes": decision.get("notes") if decision else None,
                "decision_date": decision.get("date") if decision else None,
                "decided_by": decision.get("decided_by") if decision else None,
            }

            # Filter by decision status
            if decision_status:
                if decision_status == "pending" and candidate_with_decision["decision"]:
                    continue
                elif decision_status != "pending" and candidate_with_decision["decision"] != decision_status:
                    continue

            results.append(candidate_with_decision)

        # Sort by GEBV descending
        results.sort(key=lambda x: x.get("gebv", 0), reverse=True)
        return results

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get a single candidate with decision info"""
        candidate = self.candidates.get(candidate_id)
        if not candidate:
            return None

        decision = self.decisions.get(candidate_id)
        return {
            **candidate,
            "decision": decision.get("decision") if decision else None,
            "decision_notes": decision.get("notes") if decision else None,
            "decision_date": decision.get("date") if decision else None,
            "decided_by": decision.get("decided_by") if decision else None,
        }

    def record_decision(
        self,
        candidate_id: str,
        decision: str,
        notes: Optional[str] = None,
        decided_by: str = "user",
    ) -> Dict[str, Any]:
        """Record a selection decision for a candidate"""
        if candidate_id not in self.candidates:
            return {"error": f"Candidate {candidate_id} not found"}

        if decision not in ["advance", "reject", "hold"]:
            return {"error": f"Invalid decision: {decision}. Must be advance, reject, or hold"}

        # Record decision
        decision_record = {
            "candidate_id": candidate_id,
            "decision": decision,
            "notes": notes,
            "decided_by": decided_by,
            "date": datetime.now().isoformat(),
        }
        self.decisions[candidate_id] = decision_record

        # Add to history
        history_entry = {
            "id": str(uuid.uuid4()),
            **decision_record,
            "candidate_name": self.candidates[candidate_id]["name"],
        }
        self.decision_history.append(history_entry)

        return {"status": "success", "decision": decision_record}

    def record_bulk_decisions(
        self,
        decisions: List[Dict[str, Any]],
        decided_by: str = "user",
    ) -> Dict[str, Any]:
        """Record multiple decisions at once"""
        results = []
        for d in decisions:
            result = self.record_decision(
                candidate_id=d["candidate_id"],
                decision=d["decision"],
                notes=d.get("notes"),
                decided_by=decided_by,
            )
            results.append(result)

        success_count = sum(1 for r in results if "error" not in r)
        return {
            "status": "success",
            "total": len(decisions),
            "successful": success_count,
            "failed": len(decisions) - success_count,
            "results": results,
        }

    def get_statistics(
        self,
        program_id: Optional[str] = None,
        trial_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get selection decision statistics"""
        candidates = self.list_candidates(program_id=program_id, trial_id=trial_id)

        total = len(candidates)
        advanced = sum(1 for c in candidates if c.get("decision") == "advance")
        rejected = sum(1 for c in candidates if c.get("decision") == "reject")
        on_hold = sum(1 for c in candidates if c.get("decision") == "hold")
        pending = sum(1 for c in candidates if not c.get("decision"))

        # Calculate average GEBV by decision
        advanced_gebvs = [c["gebv"] for c in candidates if c.get("decision") == "advance"]
        rejected_gebvs = [c["gebv"] for c in candidates if c.get("decision") == "reject"]

        return {
            "total_candidates": total,
            "advanced": advanced,
            "rejected": rejected,
            "on_hold": on_hold,
            "pending": pending,
            "selection_rate": round(advanced / total * 100, 1) if total > 0 else 0,
            "avg_gebv_advanced": round(sum(advanced_gebvs) / len(advanced_gebvs), 2) if advanced_gebvs else None,
            "avg_gebv_rejected": round(sum(rejected_gebvs) / len(rejected_gebvs), 2) if rejected_gebvs else None,
        }

    def get_decision_history(
        self,
        limit: int = 50,
        candidate_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision history"""
        history = self.decision_history

        if candidate_id:
            history = [h for h in history if h["candidate_id"] == candidate_id]

        # Return most recent first
        return sorted(history, key=lambda x: x["date"], reverse=True)[:limit]

    def get_programs(self) -> List[Dict[str, str]]:
        """Get unique programs from candidates"""
        programs = {}
        for c in self.candidates.values():
            pid = c.get("program_id")
            if pid and pid not in programs:
                programs[pid] = {
                    "id": pid,
                    "name": c.get("program_name", pid),
                }
        return list(programs.values())

    def get_trials(self, program_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Get unique trials from candidates"""
        trials = {}
        for c in self.candidates.values():
            if program_id and c.get("program_id") != program_id:
                continue
            tid = c.get("trial_id")
            if tid and tid not in trials:
                trials[tid] = {
                    "id": tid,
                    "name": c.get("trial_name", tid),
                    "program_id": c.get("program_id"),
                }
        return list(trials.values())


# Singleton instance
selection_decisions_service = SelectionDecisionsService()
