"""
Disease Resistance Service
Track disease resistance genes, screening results, and resistance breeding
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4


class DiseaseResistanceService:
    """Service for disease resistance tracking and breeding"""
    
    def __init__(self):
        # In-memory storage
        self.diseases: Dict[str, Dict] = {}
        self.resistance_genes: Dict[str, Dict] = {}
        self.screenings: Dict[str, List[Dict]] = {}
        self.gene_pyramids: Dict[str, Dict] = {}
        
        # Initialize sample data
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with common crop diseases and resistance genes"""
        # Common diseases
        diseases = [
            {"disease_id": "DIS-001", "name": "Bacterial Leaf Blight", "pathogen": "Xanthomonas oryzae pv. oryzae", "crop": "Rice", "type": "bacterial"},
            {"disease_id": "DIS-002", "name": "Rice Blast", "pathogen": "Magnaporthe oryzae", "crop": "Rice", "type": "fungal"},
            {"disease_id": "DIS-003", "name": "Brown Planthopper", "pathogen": "Nilaparvata lugens", "crop": "Rice", "type": "insect"},
            {"disease_id": "DIS-004", "name": "Stem Rust", "pathogen": "Puccinia graminis", "crop": "Wheat", "type": "fungal"},
            {"disease_id": "DIS-005", "name": "Leaf Rust", "pathogen": "Puccinia triticina", "crop": "Wheat", "type": "fungal"},
            {"disease_id": "DIS-006", "name": "Yellow Rust", "pathogen": "Puccinia striiformis", "crop": "Wheat", "type": "fungal"},
            {"disease_id": "DIS-007", "name": "Powdery Mildew", "pathogen": "Blumeria graminis", "crop": "Wheat", "type": "fungal"},
            {"disease_id": "DIS-008", "name": "Late Blight", "pathogen": "Phytophthora infestans", "crop": "Potato", "type": "oomycete"},
        ]
        
        for d in diseases:
            d["created_at"] = datetime.now().isoformat()
            self.diseases[d["disease_id"]] = d
            self.screenings[d["disease_id"]] = []
        
        # Resistance genes
        genes = [
            {"gene_id": "GENE-001", "name": "Xa21", "disease_id": "DIS-001", "chromosome": "11", "type": "R-gene", "mechanism": "receptor kinase"},
            {"gene_id": "GENE-002", "name": "xa13", "disease_id": "DIS-001", "chromosome": "8", "type": "recessive", "mechanism": "sugar transporter"},
            {"gene_id": "GENE-003", "name": "xa5", "disease_id": "DIS-001", "chromosome": "5", "type": "recessive", "mechanism": "transcription factor"},
            {"gene_id": "GENE-004", "name": "Pi-ta", "disease_id": "DIS-002", "chromosome": "12", "type": "R-gene", "mechanism": "NBS-LRR"},
            {"gene_id": "GENE-005", "name": "Pi9", "disease_id": "DIS-002", "chromosome": "6", "type": "R-gene", "mechanism": "NBS-LRR"},
            {"gene_id": "GENE-006", "name": "Bph3", "disease_id": "DIS-003", "chromosome": "6", "type": "QTL", "mechanism": "antibiosis"},
            {"gene_id": "GENE-007", "name": "Sr31", "disease_id": "DIS-004", "chromosome": "1B", "type": "R-gene", "mechanism": "hypersensitive response"},
            {"gene_id": "GENE-008", "name": "Lr34", "disease_id": "DIS-005", "chromosome": "7D", "type": "APR", "mechanism": "ABC transporter"},
            {"gene_id": "GENE-009", "name": "Yr15", "disease_id": "DIS-006", "chromosome": "1B", "type": "R-gene", "mechanism": "kinase-pseudokinase"},
        ]
        
        for g in genes:
            g["created_at"] = datetime.now().isoformat()
            self.resistance_genes[g["gene_id"]] = g
    
    def register_disease(
        self,
        name: str,
        pathogen: str,
        crop: str,
        disease_type: str,
        symptoms: Optional[str] = None,
        economic_impact: Optional[str] = None,
    ) -> Dict:
        """Register a new disease"""
        disease_id = f"DIS-{str(uuid4())[:8].upper()}"
        
        disease = {
            "disease_id": disease_id,
            "name": name,
            "pathogen": pathogen,
            "crop": crop,
            "type": disease_type,
            "symptoms": symptoms,
            "economic_impact": economic_impact,
            "created_at": datetime.now().isoformat(),
        }
        
        self.diseases[disease_id] = disease
        self.screenings[disease_id] = []
        
        return disease
    
    def get_disease(self, disease_id: str) -> Optional[Dict]:
        """Get disease details"""
        return self.diseases.get(disease_id)
    
    def list_diseases(
        self,
        crop: Optional[str] = None,
        disease_type: Optional[str] = None,
    ) -> List[Dict]:
        """List diseases with optional filters"""
        diseases = list(self.diseases.values())
        
        if crop:
            diseases = [d for d in diseases if d["crop"].lower() == crop.lower()]
        if disease_type:
            diseases = [d for d in diseases if d["type"] == disease_type]
        
        return diseases
    
    def register_gene(
        self,
        name: str,
        disease_id: str,
        chromosome: str,
        gene_type: str,
        mechanism: Optional[str] = None,
        markers: Optional[List[str]] = None,
        donor_source: Optional[str] = None,
    ) -> Dict:
        """Register a resistance gene"""
        gene_id = f"GENE-{str(uuid4())[:8].upper()}"
        
        gene = {
            "gene_id": gene_id,
            "name": name,
            "disease_id": disease_id,
            "chromosome": chromosome,
            "type": gene_type,
            "mechanism": mechanism,
            "markers": markers or [],
            "donor_source": donor_source,
            "created_at": datetime.now().isoformat(),
        }
        
        self.resistance_genes[gene_id] = gene
        
        return gene
    
    def get_gene(self, gene_id: str) -> Optional[Dict]:
        """Get gene details"""
        return self.resistance_genes.get(gene_id)
    
    def list_genes(
        self,
        disease_id: Optional[str] = None,
        gene_type: Optional[str] = None,
    ) -> List[Dict]:
        """List resistance genes"""
        genes = list(self.resistance_genes.values())
        
        if disease_id:
            genes = [g for g in genes if g["disease_id"] == disease_id]
        if gene_type:
            genes = [g for g in genes if g["type"] == gene_type]
        
        return genes
    
    def record_screening(
        self,
        disease_id: str,
        genotype_id: str,
        genotype_name: str,
        screening_date: str,
        method: str,
        score: float,
        scale: str,
        reaction: str,  # R, MR, MS, S, HS
        notes: Optional[str] = None,
    ) -> Dict:
        """Record disease screening result"""
        if disease_id not in self.diseases:
            raise ValueError(f"Disease {disease_id} not found")
        
        screening = {
            "screening_id": str(uuid4()),
            "disease_id": disease_id,
            "genotype_id": genotype_id,
            "genotype_name": genotype_name,
            "screening_date": screening_date,
            "method": method,
            "score": score,
            "scale": scale,
            "reaction": reaction,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
        }
        
        self.screenings[disease_id].append(screening)
        
        return screening
    
    def get_screenings(
        self,
        disease_id: str,
        genotype_id: Optional[str] = None,
        reaction: Optional[str] = None,
    ) -> List[Dict]:
        """Get screening results"""
        screenings = self.screenings.get(disease_id, [])
        
        if genotype_id:
            screenings = [s for s in screenings if s["genotype_id"] == genotype_id]
        if reaction:
            screenings = [s for s in screenings if s["reaction"] == reaction]
        
        return screenings
    
    def create_gene_pyramid(
        self,
        name: str,
        target_disease_id: str,
        gene_ids: List[str],
        description: Optional[str] = None,
    ) -> Dict:
        """Create a gene pyramiding strategy"""
        pyramid_id = f"PYR-{str(uuid4())[:8].upper()}"
        
        # Get gene details
        genes = [self.resistance_genes.get(gid) for gid in gene_ids]
        genes = [g for g in genes if g is not None]
        
        pyramid = {
            "pyramid_id": pyramid_id,
            "name": name,
            "target_disease_id": target_disease_id,
            "gene_ids": gene_ids,
            "genes": genes,
            "n_genes": len(genes),
            "description": description,
            "created_at": datetime.now().isoformat(),
        }
        
        self.gene_pyramids[pyramid_id] = pyramid
        
        return pyramid
    
    def get_pyramid(self, pyramid_id: str) -> Optional[Dict]:
        """Get gene pyramid details"""
        return self.gene_pyramids.get(pyramid_id)
    
    def list_pyramids(self) -> List[Dict]:
        """List all gene pyramids"""
        return list(self.gene_pyramids.values())
    
    def get_resistance_profile(self, genotype_id: str) -> Dict:
        """Get complete resistance profile for a genotype"""
        profile = {
            "genotype_id": genotype_id,
            "screenings": [],
            "resistance_summary": {},
        }
        
        for disease_id, screenings in self.screenings.items():
            genotype_screenings = [s for s in screenings if s["genotype_id"] == genotype_id]
            if genotype_screenings:
                disease = self.diseases.get(disease_id, {})
                latest = max(genotype_screenings, key=lambda x: x["screening_date"])
                
                profile["screenings"].extend(genotype_screenings)
                profile["resistance_summary"][disease.get("name", disease_id)] = {
                    "reaction": latest["reaction"],
                    "score": latest["score"],
                    "date": latest["screening_date"],
                }
        
        return profile
    
    def get_reaction_scale(self) -> List[Dict]:
        """Get standard disease reaction scale"""
        return [
            {"code": "HR", "name": "Highly Resistant", "score_range": "0-1", "description": "No visible symptoms"},
            {"code": "R", "name": "Resistant", "score_range": "1-3", "description": "Minor symptoms, no yield loss"},
            {"code": "MR", "name": "Moderately Resistant", "score_range": "3-5", "description": "Some symptoms, minimal yield loss"},
            {"code": "MS", "name": "Moderately Susceptible", "score_range": "5-7", "description": "Moderate symptoms and yield loss"},
            {"code": "S", "name": "Susceptible", "score_range": "7-9", "description": "Severe symptoms, significant yield loss"},
            {"code": "HS", "name": "Highly Susceptible", "score_range": "9", "description": "Plant death or complete yield loss"},
        ]
    
    def get_statistics(self) -> Dict:
        """Get disease resistance statistics"""
        total_screenings = sum(len(s) for s in self.screenings.values())
        
        return {
            "total_diseases": len(self.diseases),
            "total_genes": len(self.resistance_genes),
            "total_screenings": total_screenings,
            "total_pyramids": len(self.gene_pyramids),
            "diseases_by_type": self._count_by_field(self.diseases.values(), "type"),
            "genes_by_type": self._count_by_field(self.resistance_genes.values(), "type"),
        }
    
    def _count_by_field(self, items, field: str) -> Dict[str, int]:
        """Count items by field value"""
        counts = {}
        for item in items:
            value = item.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts


# Singleton instance
disease_resistance_service = DiseaseResistanceService()
