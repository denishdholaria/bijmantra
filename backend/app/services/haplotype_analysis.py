"""
Haplotype Analysis Service

Provides haplotype-based analysis for breeding:
- Haplotype block detection
- Haplotype diversity analysis
- Haplotype-trait associations
- Favorable haplotype identification
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import random


class HaplotypeAnalysisService:
    """Service for haplotype analysis"""
    
    def __init__(self):
        # Demo haplotype blocks
        self.haplotype_blocks = self._generate_demo_blocks()
        self.haplotypes = self._generate_demo_haplotypes()
        self.associations = self._generate_demo_associations()
    
    def _generate_demo_blocks(self) -> List[Dict[str, Any]]:
        """Generate demo haplotype blocks"""
        blocks = []
        for chr_num in range(1, 13):
            n_blocks = random.randint(3, 8)
            start = 0
            for i in range(n_blocks):
                length = random.randint(50, 500)  # kb
                blocks.append({
                    "block_id": f"HB_{chr_num}_{i+1}",
                    "chromosome": str(chr_num),
                    "start_position": start * 1000,
                    "end_position": (start + length) * 1000,
                    "length_kb": length,
                    "n_markers": random.randint(5, 30),
                    "n_haplotypes": random.randint(2, 6),
                    "major_haplotype_freq": round(random.uniform(0.3, 0.7), 2),
                    "diversity": round(random.uniform(0.2, 0.8), 3),
                })
                start += length + random.randint(10, 100)
        return blocks
    
    def _generate_demo_haplotypes(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate demo haplotypes for each block"""
        haplotypes = {}
        for block in self.haplotype_blocks:
            block_id = block["block_id"]
            n_haps = block["n_haplotypes"]
            haps = []
            remaining_freq = 1.0
            
            for i in range(n_haps):
                if i == n_haps - 1:
                    freq = remaining_freq
                else:
                    freq = round(random.uniform(0.05, remaining_freq * 0.6), 3)
                    remaining_freq -= freq
                
                # Generate allele string
                n_markers = block["n_markers"]
                alleles = ''.join(random.choice(['A', 'T', 'G', 'C']) for _ in range(min(n_markers, 10)))
                
                haps.append({
                    "haplotype_id": f"{block_id}_H{i+1}",
                    "block_id": block_id,
                    "allele_string": alleles,
                    "frequency": round(freq, 3),
                    "n_carriers": random.randint(5, 100),
                    "is_favorable": random.random() > 0.7,
                    "associated_traits": random.sample(
                        ["Yield", "Height", "Maturity", "Disease Resistance", "Drought Tolerance"],
                        k=random.randint(0, 2)
                    ),
                })
            
            haplotypes[block_id] = sorted(haps, key=lambda x: -x["frequency"])
        
        return haplotypes
    
    def _generate_demo_associations(self) -> List[Dict[str, Any]]:
        """Generate demo haplotype-trait associations"""
        associations = []
        traits = ["Yield", "Plant Height", "Days to Flowering", "Grain Weight", "Disease Resistance"]
        
        for trait in traits:
            n_assoc = random.randint(2, 5)
            blocks = random.sample(self.haplotype_blocks, min(n_assoc, len(self.haplotype_blocks)))
            
            for block in blocks:
                block_id = block["block_id"]
                haps = self.haplotypes.get(block_id, [])
                if haps:
                    fav_hap = random.choice(haps)
                    associations.append({
                        "association_id": f"ASSOC_{trait[:3]}_{block_id}",
                        "trait": trait,
                        "block_id": block_id,
                        "chromosome": block["chromosome"],
                        "favorable_haplotype": fav_hap["haplotype_id"],
                        "effect_size": round(random.uniform(0.1, 0.5), 3),
                        "p_value": round(random.uniform(1e-8, 1e-3), 10),
                        "variance_explained": round(random.uniform(0.02, 0.15), 3),
                        "favorable_allele_freq": fav_hap["frequency"],
                    })
        
        return sorted(associations, key=lambda x: x["p_value"])
    
    def get_blocks(
        self,
        chromosome: Optional[str] = None,
        min_length: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get haplotype blocks with optional filtering"""
        blocks = self.haplotype_blocks
        
        if chromosome:
            blocks = [b for b in blocks if b["chromosome"] == chromosome]
        
        if min_length:
            blocks = [b for b in blocks if b["length_kb"] >= min_length]
        
        return blocks
    
    def get_block(self, block_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific haplotype block"""
        for block in self.haplotype_blocks:
            if block["block_id"] == block_id:
                return {
                    **block,
                    "haplotypes": self.haplotypes.get(block_id, []),
                }
        return None
    
    def get_haplotypes(self, block_id: str) -> List[Dict[str, Any]]:
        """Get haplotypes for a block"""
        return self.haplotypes.get(block_id, [])
    
    def get_associations(
        self,
        trait: Optional[str] = None,
        chromosome: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get haplotype-trait associations"""
        assocs = self.associations
        
        if trait:
            assocs = [a for a in assocs if a["trait"].lower() == trait.lower()]
        
        if chromosome:
            assocs = [a for a in assocs if a["chromosome"] == chromosome]
        
        return assocs
    
    def get_favorable_haplotypes(self, trait: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get favorable haplotypes for breeding"""
        favorable = []
        
        for block_id, haps in self.haplotypes.items():
            for hap in haps:
                if hap["is_favorable"]:
                    # Find associated traits
                    assocs = [a for a in self.associations if a["favorable_haplotype"] == hap["haplotype_id"]]
                    
                    if trait and not any(a["trait"].lower() == trait.lower() for a in assocs):
                        continue
                    
                    block = next((b for b in self.haplotype_blocks if b["block_id"] == block_id), None)
                    
                    favorable.append({
                        **hap,
                        "chromosome": block["chromosome"] if block else "?",
                        "block_length_kb": block["length_kb"] if block else 0,
                        "associations": [{"trait": a["trait"], "effect": a["effect_size"]} for a in assocs],
                    })
        
        return sorted(favorable, key=lambda x: -x["frequency"])
    
    def get_diversity_summary(self) -> Dict[str, Any]:
        """Get haplotype diversity summary"""
        total_blocks = len(self.haplotype_blocks)
        total_haplotypes = sum(len(h) for h in self.haplotypes.values())
        
        diversities = [b["diversity"] for b in self.haplotype_blocks]
        
        return {
            "total_blocks": total_blocks,
            "total_haplotypes": total_haplotypes,
            "avg_haplotypes_per_block": round(total_haplotypes / total_blocks, 1) if total_blocks > 0 else 0,
            "mean_diversity": round(sum(diversities) / len(diversities), 3) if diversities else 0,
            "min_diversity": round(min(diversities), 3) if diversities else 0,
            "max_diversity": round(max(diversities), 3) if diversities else 0,
            "blocks_by_chromosome": {
                str(c): len([b for b in self.haplotype_blocks if b["chromosome"] == str(c)])
                for c in range(1, 13)
            },
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        return {
            "total_blocks": len(self.haplotype_blocks),
            "total_haplotypes": sum(len(h) for h in self.haplotypes.values()),
            "total_associations": len(self.associations),
            "favorable_haplotypes": sum(
                1 for haps in self.haplotypes.values() for h in haps if h["is_favorable"]
            ),
            "traits_analyzed": len(set(a["trait"] for a in self.associations)),
            "chromosomes_covered": len(set(b["chromosome"] for b in self.haplotype_blocks)),
        }


# Singleton instance
haplotype_service = HaplotypeAnalysisService()
