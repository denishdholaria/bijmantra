"""
Molecular Breeding Service

Integrated molecular breeding tools and workflows.
"""

from typing import Optional, List


class MolecularBreedingService:
    """Service for molecular breeding workflows."""
    
    def __init__(self):
        self._schemes = self._generate_demo_schemes()
        self._lines = self._generate_demo_lines()
    
    def _generate_demo_schemes(self) -> list:
        """Generate demo breeding schemes."""
        return [
            {"id": "bs1", "name": "Drought Tolerance Introgression", "type": "MABC", "status": "active", "generation": "BC3F2", "progress": 75, "target_traits": ["qDTY1.1", "qDTY3.1"], "start_date": "2023-01-15", "target_date": "2025-06-30"},
            {"id": "bs2", "name": "Disease Resistance Pyramiding", "type": "MABC", "status": "active", "generation": "BC2F3", "progress": 60, "target_traits": ["Xa21", "Pi54", "Sub1A"], "start_date": "2023-06-01", "target_date": "2025-12-31"},
            {"id": "bs3", "name": "Yield Improvement GS", "type": "GS", "status": "active", "generation": "C2", "progress": 40, "target_traits": ["Grain Yield", "Grain Weight"], "start_date": "2024-01-01", "target_date": "2026-06-30"},
            {"id": "bs4", "name": "Quality Enhancement MARS", "type": "MARS", "status": "planned", "generation": "F2", "progress": 10, "target_traits": ["Protein", "Amylose"], "start_date": "2024-06-01", "target_date": "2027-01-01"},
            {"id": "bs5", "name": "Speed Breeding Elite", "type": "Speed", "status": "active", "generation": "F5", "progress": 85, "target_traits": ["Multiple"], "start_date": "2024-03-01", "target_date": "2024-12-31"},
        ]
    
    def _generate_demo_lines(self) -> list:
        """Generate demo introgression lines."""
        return [
            {"id": "il1", "name": "IL-DT-001", "donor": "Donor-A", "recurrent": "Elite-001", "target_gene": "qDTY1.1", "bc_generation": 3, "rp_recovery": 92, "foreground_status": "fixed", "scheme_id": "bs1"},
            {"id": "il2", "name": "IL-DT-002", "donor": "Donor-A", "recurrent": "Elite-001", "target_gene": "qDTY1.1", "bc_generation": 3, "rp_recovery": 88, "foreground_status": "fixed", "scheme_id": "bs1"},
            {"id": "il3", "name": "IL-BR-001", "donor": "Donor-B", "recurrent": "Elite-002", "target_gene": "Xa21", "bc_generation": 2, "rp_recovery": 78, "foreground_status": "segregating", "scheme_id": "bs2"},
            {"id": "il4", "name": "IL-BR-002", "donor": "Donor-C", "recurrent": "Elite-002", "target_gene": "Pi54", "bc_generation": 2, "rp_recovery": 82, "foreground_status": "fixed", "scheme_id": "bs2"},
            {"id": "il5", "name": "IL-SUB-001", "donor": "FR13A", "recurrent": "Elite-003", "target_gene": "Sub1A", "bc_generation": 3, "rp_recovery": 95, "foreground_status": "fixed", "scheme_id": "bs2"},
        ]

    def get_schemes(self, scheme_type: Optional[str] = None, status: Optional[str] = None) -> list:
        """Get breeding schemes with optional filters."""
        schemes = self._schemes.copy()
        if scheme_type:
            schemes = [s for s in schemes if s["type"].lower() == scheme_type.lower()]
        if status:
            schemes = [s for s in schemes if s["status"].lower() == status.lower()]
        return schemes
    
    def get_scheme(self, scheme_id: str) -> Optional[dict]:
        """Get a specific scheme by ID."""
        for s in self._schemes:
            if s["id"] == scheme_id:
                return s
        return None
    
    def get_introgression_lines(self, scheme_id: Optional[str] = None, foreground_status: Optional[str] = None) -> list:
        """Get introgression lines with optional filters."""
        lines = self._lines.copy()
        if scheme_id:
            lines = [l for l in lines if l["scheme_id"] == scheme_id]
        if foreground_status:
            lines = [l for l in lines if l["foreground_status"].lower() == foreground_status.lower()]
        return lines
    
    def get_statistics(self) -> dict:
        """Get molecular breeding statistics."""
        schemes = self._schemes
        lines = self._lines
        
        avg_progress = sum(s["progress"] for s in schemes) / len(schemes) if schemes else 0
        target_genes = set()
        for l in lines:
            target_genes.add(l["target_gene"])
        
        return {
            "total_schemes": len(schemes),
            "active_schemes": len([s for s in schemes if s["status"] == "active"]),
            "total_lines": len(lines),
            "fixed_lines": len([l for l in lines if l["foreground_status"] == "fixed"]),
            "target_genes": len(target_genes),
            "avg_progress": round(avg_progress, 1),
            "by_type": {
                "MABC": len([s for s in schemes if s["type"] == "MABC"]),
                "MARS": len([s for s in schemes if s["type"] == "MARS"]),
                "GS": len([s for s in schemes if s["type"] == "GS"]),
                "Speed": len([s for s in schemes if s["type"] == "Speed"]),
            }
        }
    
    def get_pyramiding_matrix(self, scheme_id: str) -> dict:
        """Get gene pyramiding matrix for a scheme."""
        lines = [l for l in self._lines if l["scheme_id"] == scheme_id]
        genes = list(set(l["target_gene"] for l in lines))
        
        # Generate pyramid combinations
        pyramids = [
            {"line": "Pyramid-001", "genes": {"Xa21": True, "Pi54": True, "Sub1A": True}, "stack": 3},
            {"line": "Pyramid-002", "genes": {"Xa21": True, "Pi54": True, "Sub1A": False}, "stack": 2},
            {"line": "Pyramid-003", "genes": {"Xa21": True, "Pi54": False, "Sub1A": True}, "stack": 2},
            {"line": "Pyramid-004", "genes": {"Xa21": False, "Pi54": True, "Sub1A": True}, "stack": 2},
        ]
        
        return {
            "scheme_id": scheme_id,
            "target_genes": genes,
            "pyramids": pyramids,
            "triple_stack_count": len([p for p in pyramids if p["stack"] == 3]),
        }


# Singleton instance
molecular_breeding_service = MolecularBreedingService()
