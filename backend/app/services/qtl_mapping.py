"""
QTL Mapping Service

Provides QTL detection, GWAS analysis, and candidate gene identification
for marker-trait association studies.
"""

from typing import Optional
import math
import random


# Demo QTL data
DEMO_QTLS = [
    {
        "id": "qtl1",
        "name": "qYLD1.1",
        "chromosome": "1",
        "position": 45.2,
        "lod": 8.5,
        "pve": 15.2,
        "add_effect": 0.85,
        "dom_effect": 0.12,
        "flanking_markers": ["SNP_1_42", "SNP_1_48"],
        "confidence_interval": [42.1, 48.3],
        "trait": "Grain Yield",
        "population": "RIL-IR64xNipponbare",
    },
    {
        "id": "qtl2",
        "name": "qPH3.1",
        "chromosome": "3",
        "position": 78.6,
        "lod": 12.3,
        "pve": 22.8,
        "add_effect": -2.45,
        "dom_effect": 0.35,
        "flanking_markers": ["SNP_3_75", "SNP_3_82"],
        "confidence_interval": [75.2, 82.1],
        "trait": "Plant Height",
        "population": "RIL-IR64xNipponbare",
    },
    {
        "id": "qtl3",
        "name": "qDTF5.1",
        "chromosome": "5",
        "position": 112.4,
        "lod": 6.8,
        "pve": 11.5,
        "add_effect": 1.2,
        "dom_effect": -0.08,
        "flanking_markers": ["SNP_5_108", "SNP_5_116"],
        "confidence_interval": [108.5, 116.2],
        "trait": "Days to Flowering",
        "population": "RIL-IR64xNipponbare",
    },
    {
        "id": "qtl4",
        "name": "qGW7.1",
        "chromosome": "7",
        "position": 34.8,
        "lod": 9.2,
        "pve": 18.4,
        "add_effect": 0.42,
        "dom_effect": 0.15,
        "flanking_markers": ["SNP_7_31", "SNP_7_38"],
        "confidence_interval": [31.2, 38.5],
        "trait": "Grain Weight",
        "population": "RIL-IR64xNipponbare",
    },
    {
        "id": "qtl5",
        "name": "qTGW2.1",
        "chromosome": "2",
        "position": 88.5,
        "lod": 5.8,
        "pve": 9.2,
        "add_effect": 0.28,
        "dom_effect": 0.05,
        "flanking_markers": ["SNP_2_85", "SNP_2_92"],
        "confidence_interval": [85.0, 92.0],
        "trait": "Thousand Grain Weight",
        "population": "RIL-IR64xNipponbare",
    },
]

# Demo GWAS results
DEMO_GWAS = [
    {"marker": "SNP_1_45", "chromosome": "1", "position": 45.2, "p_value": 2.5e-8, "log_p": 7.6, "effect": 0.82, "maf": 0.35, "trait": "Grain Yield"},
    {"marker": "SNP_3_79", "chromosome": "3", "position": 79.1, "p_value": 1.2e-12, "log_p": 11.9, "effect": -2.38, "maf": 0.42, "trait": "Plant Height"},
    {"marker": "SNP_5_112", "chromosome": "5", "position": 112.8, "p_value": 8.5e-7, "log_p": 6.1, "effect": 1.15, "maf": 0.28, "trait": "Days to Flowering"},
    {"marker": "SNP_7_35", "chromosome": "7", "position": 35.2, "p_value": 5.8e-9, "log_p": 8.2, "effect": 0.45, "maf": 0.38, "trait": "Grain Weight"},
    {"marker": "SNP_2_88", "chromosome": "2", "position": 88.5, "p_value": 3.2e-6, "log_p": 5.5, "effect": 0.28, "maf": 0.31, "trait": "Grain Yield"},
    {"marker": "SNP_4_56", "chromosome": "4", "position": 56.3, "p_value": 7.1e-5, "log_p": 4.1, "effect": -0.95, "maf": 0.22, "trait": "Plant Height"},
    {"marker": "SNP_6_92", "chromosome": "6", "position": 92.4, "p_value": 4.5e-6, "log_p": 5.3, "effect": 0.65, "maf": 0.33, "trait": "Grain Yield"},
    {"marker": "SNP_8_45", "chromosome": "8", "position": 45.8, "p_value": 9.2e-5, "log_p": 4.0, "effect": -0.42, "maf": 0.25, "trait": "Days to Flowering"},
]

# Demo candidate genes
DEMO_CANDIDATE_GENES = {
    "qtl1": [
        {"gene_id": "Os01g0123400", "name": "OsGW2", "function": "Grain width regulator", "distance_kb": 15.2},
        {"gene_id": "Os01g0124500", "name": "OsYLD1", "function": "Yield-related transcription factor", "distance_kb": 28.5},
        {"gene_id": "Os01g0125100", "name": "OsKIN1", "function": "Protein kinase", "distance_kb": 42.1},
    ],
    "qtl2": [
        {"gene_id": "Os03g0567800", "name": "OsGA20ox2", "function": "Gibberellin biosynthesis", "distance_kb": 8.5},
        {"gene_id": "Os03g0568200", "name": "OsPH1", "function": "Plant height regulator", "distance_kb": 22.3},
    ],
    "qtl3": [
        {"gene_id": "Os05g0428700", "name": "Hd1", "function": "Heading date regulator", "distance_kb": 5.2},
        {"gene_id": "Os05g0429100", "name": "OsFT1", "function": "Florigen", "distance_kb": 18.8},
    ],
    "qtl4": [
        {"gene_id": "Os07g0182500", "name": "GW7", "function": "Grain weight QTL", "distance_kb": 12.5},
    ],
}

# GO enrichment results
GO_ENRICHMENT = [
    {"term": "GO:0009628", "name": "Response to abiotic stress", "p_value": 0.001, "gene_count": 8, "fold_enrichment": 3.2},
    {"term": "GO:0005975", "name": "Carbohydrate metabolic process", "p_value": 0.005, "gene_count": 5, "fold_enrichment": 2.8},
    {"term": "GO:0040008", "name": "Regulation of growth", "p_value": 0.012, "gene_count": 4, "fold_enrichment": 2.5},
    {"term": "GO:0015979", "name": "Photosynthesis", "p_value": 0.023, "gene_count": 3, "fold_enrichment": 2.1},
    {"term": "GO:0006950", "name": "Response to stress", "p_value": 0.035, "gene_count": 6, "fold_enrichment": 1.9},
]


class QTLMappingService:
    """Service for QTL mapping and GWAS analysis."""
    
    def __init__(self):
        self.qtls = DEMO_QTLS.copy()
        self.gwas_results = DEMO_GWAS.copy()
    
    def list_qtls(
        self,
        trait: Optional[str] = None,
        chromosome: Optional[str] = None,
        min_lod: float = 0,
        population: Optional[str] = None,
    ) -> list[dict]:
        """List detected QTLs with optional filters."""
        filtered = self.qtls.copy()
        
        if trait:
            filtered = [q for q in filtered if q["trait"].lower() == trait.lower()]
        if chromosome:
            filtered = [q for q in filtered if q["chromosome"] == chromosome]
        if min_lod > 0:
            filtered = [q for q in filtered if q["lod"] >= min_lod]
        if population:
            filtered = [q for q in filtered if q["population"] == population]
        
        return filtered
    
    def get_qtl(self, qtl_id: str) -> Optional[dict]:
        """Get a single QTL by ID."""
        for qtl in self.qtls:
            if qtl["id"] == qtl_id:
                return qtl
        return None
    
    def get_gwas_results(
        self,
        trait: Optional[str] = None,
        chromosome: Optional[str] = None,
        min_log_p: float = 0,
        max_p_value: Optional[float] = None,
    ) -> list[dict]:
        """Get GWAS marker-trait associations."""
        filtered = self.gwas_results.copy()
        
        if trait:
            filtered = [g for g in filtered if g["trait"].lower() == trait.lower()]
        if chromosome:
            filtered = [g for g in filtered if g["chromosome"] == chromosome]
        if min_log_p > 0:
            filtered = [g for g in filtered if g["log_p"] >= min_log_p]
        if max_p_value:
            filtered = [g for g in filtered if g["p_value"] <= max_p_value]
        
        # Sort by -log10(p) descending
        filtered.sort(key=lambda x: x["log_p"], reverse=True)
        return filtered
    
    def get_manhattan_data(self, trait: Optional[str] = None) -> dict:
        """Get data for Manhattan plot visualization."""
        chromosomes = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        
        # Generate simulated data points for each chromosome
        points = []
        cumulative_pos = 0
        chr_boundaries = []
        
        for chr_num in chromosomes:
            chr_length = 150 + random.randint(-20, 20)  # ~150 cM per chromosome
            chr_boundaries.append({"chromosome": chr_num, "start": cumulative_pos, "end": cumulative_pos + chr_length})
            
            # Generate random points
            for _ in range(50):
                pos = random.uniform(0, chr_length)
                log_p = random.uniform(0, 4)  # Most points below threshold
                
                # Check if this position has a real GWAS hit
                for gwas in self.gwas_results:
                    if gwas["chromosome"] == chr_num and abs(gwas["position"] - pos) < 5:
                        if trait is None or gwas["trait"].lower() == trait.lower():
                            log_p = gwas["log_p"]
                            break
                
                points.append({
                    "chromosome": chr_num,
                    "position": pos,
                    "cumulative_position": cumulative_pos + pos,
                    "log_p": round(log_p, 2),
                })
            
            cumulative_pos += chr_length
        
        return {
            "points": points,
            "chromosome_boundaries": chr_boundaries,
            "significance_threshold": 5.0,  # -log10(1e-5)
            "suggestive_threshold": 4.0,
            "genomic_inflation_factor": 1.02,
        }
    
    def get_lod_profile(self, chromosome: str, trait: Optional[str] = None) -> dict:
        """Get LOD score profile for a chromosome."""
        chr_length = 150  # cM
        positions = list(range(0, chr_length + 1, 2))  # Every 2 cM
        
        # Generate baseline LOD scores
        lod_scores = [random.uniform(0, 2) for _ in positions]
        
        # Add peaks for QTLs on this chromosome
        for qtl in self.qtls:
            if qtl["chromosome"] == chromosome:
                if trait and qtl["trait"].lower() != trait.lower():
                    continue
                peak_pos = qtl["position"]
                peak_lod = qtl["lod"]
                
                # Add Gaussian peak
                for i, pos in enumerate(positions):
                    distance = abs(pos - peak_pos)
                    if distance < 20:
                        contribution = peak_lod * math.exp(-(distance ** 2) / 50)
                        lod_scores[i] = max(lod_scores[i], contribution)
        
        return {
            "chromosome": chromosome,
            "positions": positions,
            "lod_scores": [round(s, 2) for s in lod_scores],
            "threshold": 3.0,
            "qtls_on_chromosome": [q for q in self.qtls if q["chromosome"] == chromosome],
        }
    
    def get_candidate_genes(self, qtl_id: str) -> list[dict]:
        """Get candidate genes within a QTL confidence interval."""
        return DEMO_CANDIDATE_GENES.get(qtl_id, [])
    
    def get_go_enrichment(self, qtl_ids: Optional[list[str]] = None) -> list[dict]:
        """Get GO enrichment analysis for candidate genes."""
        return GO_ENRICHMENT
    
    def get_qtl_summary(self) -> dict:
        """Get summary statistics for QTL analysis."""
        traits = list(set(q["trait"] for q in self.qtls))
        chromosomes = list(set(q["chromosome"] for q in self.qtls))
        
        total_pve = sum(q["pve"] for q in self.qtls)
        avg_lod = sum(q["lod"] for q in self.qtls) / len(self.qtls)
        
        return {
            "total_qtls": len(self.qtls),
            "traits_analyzed": len(traits),
            "traits": traits,
            "chromosomes_with_qtls": len(chromosomes),
            "total_pve": round(total_pve, 1),
            "average_lod": round(avg_lod, 2),
            "major_qtls": len([q for q in self.qtls if q["pve"] >= 15]),
            "minor_qtls": len([q for q in self.qtls if q["pve"] < 15]),
        }
    
    def get_gwas_summary(self) -> dict:
        """Get summary statistics for GWAS analysis."""
        traits = list(set(g["trait"] for g in self.gwas_results))
        
        return {
            "total_associations": len(self.gwas_results),
            "significant_associations": len([g for g in self.gwas_results if g["log_p"] >= 5]),
            "suggestive_associations": len([g for g in self.gwas_results if 4 <= g["log_p"] < 5]),
            "traits_analyzed": len(traits),
            "traits": traits,
            "top_association": max(self.gwas_results, key=lambda x: x["log_p"]),
            "genomic_inflation_factor": 1.02,
        }
    
    def get_traits(self) -> list[str]:
        """Get list of available traits."""
        qtl_traits = set(q["trait"] for q in self.qtls)
        gwas_traits = set(g["trait"] for g in self.gwas_results)
        return sorted(list(qtl_traits | gwas_traits))
    
    def get_populations(self) -> list[str]:
        """Get list of available mapping populations."""
        return sorted(list(set(q["population"] for q in self.qtls)))


# Singleton instance
_service = None


def get_qtl_mapping_service() -> QTLMappingService:
    """Get the QTL mapping service singleton."""
    global _service
    if _service is None:
        _service = QTLMappingService()
    return _service
