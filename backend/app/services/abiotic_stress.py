"""
Abiotic Stress Tolerance Service
Track drought, heat, salinity, and other abiotic stress tolerance
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4


class AbioticStressService:
    """Service for abiotic stress tolerance tracking"""
    
    def __init__(self):
        # In-memory storage
        self.stress_types: Dict[str, Dict] = {}
        self.tolerance_genes: Dict[str, Dict] = {}
        self.screenings: Dict[str, List[Dict]] = {}
        self.stress_indices: Dict[str, Dict] = {}
        
        # Initialize sample data
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with common abiotic stresses"""
        stresses = [
            {"stress_id": "STR-001", "name": "Drought", "category": "water", "description": "Water deficit stress"},
            {"stress_id": "STR-002", "name": "Heat", "category": "temperature", "description": "High temperature stress"},
            {"stress_id": "STR-003", "name": "Cold", "category": "temperature", "description": "Low temperature/chilling stress"},
            {"stress_id": "STR-004", "name": "Salinity", "category": "soil", "description": "Salt stress in soil"},
            {"stress_id": "STR-005", "name": "Submergence", "category": "water", "description": "Flooding/waterlogging"},
            {"stress_id": "STR-006", "name": "Nutrient Deficiency", "category": "soil", "description": "Low nutrient availability"},
            {"stress_id": "STR-007", "name": "Heavy Metal", "category": "soil", "description": "Toxic metal accumulation"},
            {"stress_id": "STR-008", "name": "UV Radiation", "category": "radiation", "description": "High UV exposure"},
        ]
        
        for s in stresses:
            s["created_at"] = datetime.now().isoformat()
            self.stress_types[s["stress_id"]] = s
            self.screenings[s["stress_id"]] = []
        
        # Tolerance genes
        genes = [
            {"gene_id": "TGENE-001", "name": "DREB1A", "stress_id": "STR-001", "mechanism": "transcription factor", "crop": "Multiple"},
            {"gene_id": "TGENE-002", "name": "LEA proteins", "stress_id": "STR-001", "mechanism": "osmoprotection", "crop": "Multiple"},
            {"gene_id": "TGENE-003", "name": "HSP101", "stress_id": "STR-002", "mechanism": "protein folding", "crop": "Multiple"},
            {"gene_id": "TGENE-004", "name": "Sub1A", "stress_id": "STR-005", "mechanism": "ethylene response", "crop": "Rice"},
            {"gene_id": "TGENE-005", "name": "Saltol", "stress_id": "STR-004", "mechanism": "ion exclusion", "crop": "Rice"},
            {"gene_id": "TGENE-006", "name": "SKC1", "stress_id": "STR-004", "mechanism": "K+/Na+ homeostasis", "crop": "Rice"},
        ]
        
        for g in genes:
            g["created_at"] = datetime.now().isoformat()
            self.tolerance_genes[g["gene_id"]] = g
    
    def get_stress_type(self, stress_id: str) -> Optional[Dict]:
        """Get stress type details"""
        return self.stress_types.get(stress_id)
    
    def list_stress_types(
        self,
        category: Optional[str] = None,
    ) -> List[Dict]:
        """List stress types"""
        stresses = list(self.stress_types.values())
        
        if category:
            stresses = [s for s in stresses if s["category"] == category]
        
        return stresses
    
    def register_gene(
        self,
        name: str,
        stress_id: str,
        mechanism: str,
        crop: str,
        chromosome: Optional[str] = None,
        markers: Optional[List[str]] = None,
    ) -> Dict:
        """Register a tolerance gene"""
        gene_id = f"TGENE-{str(uuid4())[:8].upper()}"
        
        gene = {
            "gene_id": gene_id,
            "name": name,
            "stress_id": stress_id,
            "mechanism": mechanism,
            "crop": crop,
            "chromosome": chromosome,
            "markers": markers or [],
            "created_at": datetime.now().isoformat(),
        }
        
        self.tolerance_genes[gene_id] = gene
        
        return gene
    
    def list_genes(
        self,
        stress_id: Optional[str] = None,
        crop: Optional[str] = None,
    ) -> List[Dict]:
        """List tolerance genes"""
        genes = list(self.tolerance_genes.values())
        
        if stress_id:
            genes = [g for g in genes if g["stress_id"] == stress_id]
        if crop:
            genes = [g for g in genes if g["crop"].lower() == crop.lower() or g["crop"] == "Multiple"]
        
        return genes
    
    def record_screening(
        self,
        stress_id: str,
        genotype_id: str,
        genotype_name: str,
        screening_date: str,
        treatment: str,
        duration_days: int,
        control_value: float,
        stress_value: float,
        trait: str,
        notes: Optional[str] = None,
    ) -> Dict:
        """Record stress screening result"""
        if stress_id not in self.stress_types:
            raise ValueError(f"Stress type {stress_id} not found")
        
        # Calculate stress indices
        stress_index = (stress_value / control_value) * 100 if control_value > 0 else 0
        reduction = ((control_value - stress_value) / control_value) * 100 if control_value > 0 else 0
        
        screening = {
            "screening_id": str(uuid4()),
            "stress_id": stress_id,
            "genotype_id": genotype_id,
            "genotype_name": genotype_name,
            "screening_date": screening_date,
            "treatment": treatment,
            "duration_days": duration_days,
            "trait": trait,
            "control_value": control_value,
            "stress_value": stress_value,
            "stress_index": round(stress_index, 2),
            "reduction_percent": round(reduction, 2),
            "tolerance_rating": self._rate_tolerance(stress_index),
            "notes": notes,
            "created_at": datetime.now().isoformat(),
        }
        
        self.screenings[stress_id].append(screening)
        
        return screening
    
    def _rate_tolerance(self, stress_index: float) -> str:
        """Rate tolerance based on stress index"""
        if stress_index >= 90:
            return "Highly Tolerant"
        elif stress_index >= 75:
            return "Tolerant"
        elif stress_index >= 60:
            return "Moderately Tolerant"
        elif stress_index >= 40:
            return "Moderately Susceptible"
        elif stress_index >= 20:
            return "Susceptible"
        else:
            return "Highly Susceptible"
    
    def get_screenings(
        self,
        stress_id: str,
        genotype_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get screening results"""
        screenings = self.screenings.get(stress_id, [])
        
        if genotype_id:
            screenings = [s for s in screenings if s["genotype_id"] == genotype_id]
        
        return screenings
    
    def calculate_stress_indices(
        self,
        control_yield: float,
        stress_yield: float,
    ) -> Dict:
        """Calculate various stress tolerance indices"""
        if control_yield <= 0:
            return {"error": "Control yield must be positive"}
        
        # Stress Susceptibility Index (SSI)
        # SSI = (1 - Ys/Yp) / SI where SI = 1 - (mean Ys / mean Yp)
        # Simplified: SSI = (Yp - Ys) / Yp
        ssi = (control_yield - stress_yield) / control_yield
        
        # Stress Tolerance Index (STI)
        # STI = (Yp × Ys) / (mean Yp)²
        # Simplified using control as reference
        sti = (control_yield * stress_yield) / (control_yield ** 2)
        
        # Yield Stability Index (YSI)
        ysi = stress_yield / control_yield
        
        # Geometric Mean Productivity (GMP)
        import math
        gmp = math.sqrt(control_yield * stress_yield)
        
        # Mean Productivity (MP)
        mp = (control_yield + stress_yield) / 2
        
        # Tolerance Index (TOL)
        tol = control_yield - stress_yield
        
        # Harmonic Mean (HM)
        hm = (2 * control_yield * stress_yield) / (control_yield + stress_yield) if (control_yield + stress_yield) > 0 else 0
        
        return {
            "control_yield": control_yield,
            "stress_yield": stress_yield,
            "indices": {
                "SSI": round(ssi, 4),
                "STI": round(sti, 4),
                "YSI": round(ysi, 4),
                "GMP": round(gmp, 4),
                "MP": round(mp, 4),
                "TOL": round(tol, 4),
                "HM": round(hm, 4),
            },
            "interpretation": {
                "SSI": "Lower is better (less susceptible)",
                "STI": "Higher is better (more tolerant)",
                "YSI": "Higher is better (more stable)",
                "GMP": "Higher is better",
                "MP": "Higher is better",
                "TOL": "Lower is better (less yield loss)",
                "HM": "Higher is better",
            },
        }
    
    def rank_genotypes(
        self,
        screenings: List[Dict],
        index: str = "STI",
    ) -> List[Dict]:
        """Rank genotypes by stress tolerance index"""
        # Group by genotype
        genotype_data = {}
        for s in screenings:
            gid = s["genotype_id"]
            if gid not in genotype_data:
                genotype_data[gid] = {
                    "genotype_id": gid,
                    "genotype_name": s["genotype_name"],
                    "control_values": [],
                    "stress_values": [],
                }
            genotype_data[gid]["control_values"].append(s["control_value"])
            genotype_data[gid]["stress_values"].append(s["stress_value"])
        
        # Calculate indices
        results = []
        for gid, data in genotype_data.items():
            avg_control = sum(data["control_values"]) / len(data["control_values"])
            avg_stress = sum(data["stress_values"]) / len(data["stress_values"])
            
            indices = self.calculate_stress_indices(avg_control, avg_stress)
            
            results.append({
                "genotype_id": gid,
                "genotype_name": data["genotype_name"],
                "avg_control": round(avg_control, 2),
                "avg_stress": round(avg_stress, 2),
                "indices": indices["indices"],
            })
        
        # Sort by selected index
        reverse = index not in ["SSI", "TOL"]  # Lower is better for SSI and TOL
        results.sort(key=lambda x: x["indices"].get(index, 0), reverse=reverse)
        
        # Add rank
        for i, r in enumerate(results):
            r["rank"] = i + 1
        
        return results
    
    def get_tolerance_profile(self, genotype_id: str) -> Dict:
        """Get complete stress tolerance profile for a genotype"""
        profile = {
            "genotype_id": genotype_id,
            "screenings": [],
            "tolerance_summary": {},
        }
        
        for stress_id, screenings in self.screenings.items():
            genotype_screenings = [s for s in screenings if s["genotype_id"] == genotype_id]
            if genotype_screenings:
                stress = self.stress_types.get(stress_id, {})
                
                # Average stress index
                avg_index = sum(s["stress_index"] for s in genotype_screenings) / len(genotype_screenings)
                
                profile["screenings"].extend(genotype_screenings)
                profile["tolerance_summary"][stress.get("name", stress_id)] = {
                    "avg_stress_index": round(avg_index, 2),
                    "rating": self._rate_tolerance(avg_index),
                    "n_screenings": len(genotype_screenings),
                }
        
        return profile
    
    def get_statistics(self) -> Dict:
        """Get abiotic stress statistics"""
        total_screenings = sum(len(s) for s in self.screenings.values())
        
        return {
            "total_stress_types": len(self.stress_types),
            "total_genes": len(self.tolerance_genes),
            "total_screenings": total_screenings,
            "stress_by_category": self._count_by_field(self.stress_types.values(), "category"),
        }
    
    def _count_by_field(self, items, field: str) -> Dict[str, int]:
        """Count items by field value"""
        counts = {}
        for item in items:
            value = item.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts


# Singleton instance
abiotic_stress_service = AbioticStressService()
