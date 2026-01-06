"""
Parentage Analysis Service

Provides DNA-based parentage verification and analysis:
- Parent-offspring verification
- Paternity/maternity testing
- Exclusion analysis
- Likelihood ratios
- Marker-based identity verification
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import random
import math


class ParentageAnalysisService:
    """Service for parentage verification and analysis"""
    
    def __init__(self):
        # Demo marker panel (SSR/SNP markers commonly used for parentage)
        self.marker_panel = [
            {"marker_id": "RM1", "name": "RM1", "chromosome": "1", "type": "SSR", "alleles": ["A", "B", "C", "D"]},
            {"marker_id": "RM7", "name": "RM7", "chromosome": "3", "type": "SSR", "alleles": ["A", "B", "C"]},
            {"marker_id": "RM11", "name": "RM11", "chromosome": "7", "type": "SSR", "alleles": ["A", "B", "C", "D", "E"]},
            {"marker_id": "RM19", "name": "RM19", "chromosome": "12", "type": "SSR", "alleles": ["A", "B", "C"]},
            {"marker_id": "RM25", "name": "RM25", "chromosome": "8", "type": "SSR", "alleles": ["A", "B", "C", "D"]},
            {"marker_id": "SNP001", "name": "SNP001", "chromosome": "1", "type": "SNP", "alleles": ["A", "G"]},
            {"marker_id": "SNP002", "name": "SNP002", "chromosome": "2", "type": "SNP", "alleles": ["C", "T"]},
            {"marker_id": "SNP003", "name": "SNP003", "chromosome": "3", "type": "SNP", "alleles": ["A", "T"]},
            {"marker_id": "SNP004", "name": "SNP004", "chromosome": "4", "type": "SNP", "alleles": ["G", "C"]},
            {"marker_id": "SNP005", "name": "SNP005", "chromosome": "5", "type": "SNP", "alleles": ["A", "G"]},
        ]
        
        # Demo genotype data
        self.demo_genotypes = self._generate_demo_genotypes()
        
        # Demo analysis results
        self.demo_analyses = []
    
    def _generate_demo_genotypes(self) -> Dict[str, Dict[str, str]]:
        """Generate demo genotype data for sample individuals"""
        individuals = {
            "IR64": {"type": "variety", "species": "Oryza sativa"},
            "Swarna": {"type": "variety", "species": "Oryza sativa"},
            "IR64-Swarna-F1": {"type": "F1", "species": "Oryza sativa", "female": "IR64", "male": "Swarna"},
            "Progeny-001": {"type": "progeny", "species": "Oryza sativa", "claimed_female": "IR64", "claimed_male": "Swarna"},
            "Progeny-002": {"type": "progeny", "species": "Oryza sativa", "claimed_female": "IR64", "claimed_male": "Swarna"},
            "Progeny-003": {"type": "progeny", "species": "Oryza sativa", "claimed_female": "IR64", "claimed_male": "Unknown"},
            "Unknown-001": {"type": "unknown", "species": "Oryza sativa"},
        }
        
        genotypes = {}
        
        # Generate parent genotypes
        for ind_id, info in individuals.items():
            genotypes[ind_id] = {
                "info": info,
                "markers": {}
            }
            
            for marker in self.marker_panel:
                if info["type"] in ["variety", "unknown"]:
                    # Random homozygous or heterozygous
                    alleles = marker["alleles"]
                    a1 = random.choice(alleles)
                    a2 = random.choice(alleles) if random.random() > 0.7 else a1
                    genotypes[ind_id]["markers"][marker["marker_id"]] = f"{a1}/{a2}"
                elif info["type"] == "F1":
                    # F1 should inherit one allele from each parent
                    female_geno = genotypes.get(info.get("female", ""), {}).get("markers", {}).get(marker["marker_id"], "A/A")
                    male_geno = genotypes.get(info.get("male", ""), {}).get("markers", {}).get(marker["marker_id"], "B/B")
                    f_alleles = female_geno.split("/")
                    m_alleles = male_geno.split("/")
                    genotypes[ind_id]["markers"][marker["marker_id"]] = f"{random.choice(f_alleles)}/{random.choice(m_alleles)}"
                elif info["type"] == "progeny":
                    # Progeny - some match, some don't (for demo)
                    if ind_id == "Progeny-001":
                        # True progeny - matches parents
                        female_geno = genotypes.get("IR64", {}).get("markers", {}).get(marker["marker_id"], "A/A")
                        male_geno = genotypes.get("Swarna", {}).get("markers", {}).get(marker["marker_id"], "B/B")
                        f_alleles = female_geno.split("/")
                        m_alleles = male_geno.split("/")
                        genotypes[ind_id]["markers"][marker["marker_id"]] = f"{random.choice(f_alleles)}/{random.choice(m_alleles)}"
                    elif ind_id == "Progeny-002":
                        # Mostly matches but some exclusions
                        if random.random() > 0.8:
                            alleles = marker["alleles"]
                            genotypes[ind_id]["markers"][marker["marker_id"]] = f"{random.choice(alleles)}/{random.choice(alleles)}"
                        else:
                            female_geno = genotypes.get("IR64", {}).get("markers", {}).get(marker["marker_id"], "A/A")
                            male_geno = genotypes.get("Swarna", {}).get("markers", {}).get(marker["marker_id"], "B/B")
                            f_alleles = female_geno.split("/")
                            m_alleles = male_geno.split("/")
                            genotypes[ind_id]["markers"][marker["marker_id"]] = f"{random.choice(f_alleles)}/{random.choice(m_alleles)}"
                    else:
                        # Random - doesn't match claimed parents
                        alleles = marker["alleles"]
                        genotypes[ind_id]["markers"][marker["marker_id"]] = f"{random.choice(alleles)}/{random.choice(alleles)}"
        
        return genotypes
    
    def get_marker_panel(self) -> List[Dict[str, Any]]:
        """Get the marker panel used for parentage analysis"""
        return self.marker_panel
    
    def get_individuals(self) -> List[Dict[str, Any]]:
        """Get list of individuals with genotype data"""
        return [
            {
                "individual_id": ind_id,
                "type": data["info"]["type"],
                "species": data["info"].get("species", "Unknown"),
                "markers_genotyped": len(data["markers"]),
                "claimed_female": data["info"].get("claimed_female"),
                "claimed_male": data["info"].get("claimed_male"),
            }
            for ind_id, data in self.demo_genotypes.items()
        ]
    
    def get_genotype(self, individual_id: str) -> Optional[Dict[str, Any]]:
        """Get genotype data for an individual"""
        if individual_id not in self.demo_genotypes:
            return None
        
        data = self.demo_genotypes[individual_id]
        return {
            "individual_id": individual_id,
            "info": data["info"],
            "markers": data["markers"],
            "marker_count": len(data["markers"]),
        }
    
    def verify_parentage(
        self,
        offspring_id: str,
        claimed_female_id: str,
        claimed_male_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify parentage of an offspring against claimed parents
        
        Returns exclusion analysis and likelihood ratios
        """
        if offspring_id not in self.demo_genotypes:
            return {"error": f"Offspring {offspring_id} not found"}
        if claimed_female_id not in self.demo_genotypes:
            return {"error": f"Claimed female {claimed_female_id} not found"}
        if claimed_male_id and claimed_male_id not in self.demo_genotypes:
            return {"error": f"Claimed male {claimed_male_id} not found"}
        
        offspring = self.demo_genotypes[offspring_id]
        female = self.demo_genotypes[claimed_female_id]
        male = self.demo_genotypes.get(claimed_male_id, {}) if claimed_male_id else {}
        
        # Analyze each marker
        marker_results = []
        exclusions_female = 0
        exclusions_male = 0
        matches = 0
        
        for marker in self.marker_panel:
            marker_id = marker["marker_id"]
            
            off_geno = offspring["markers"].get(marker_id, "")
            fem_geno = female["markers"].get(marker_id, "")
            mal_geno = male.get("markers", {}).get(marker_id, "") if male else ""
            
            if not off_geno or not fem_geno:
                continue
            
            off_alleles = set(off_geno.split("/"))
            fem_alleles = set(fem_geno.split("/"))
            mal_alleles = set(mal_geno.split("/")) if mal_geno else set()
            
            # Check if offspring could have inherited from female
            female_compatible = bool(off_alleles & fem_alleles)
            
            # Check if offspring could have inherited from male
            male_compatible = bool(off_alleles & mal_alleles) if mal_alleles else None
            
            # Determine match status
            if claimed_male_id:
                if female_compatible and male_compatible:
                    status = "match"
                    matches += 1
                elif not female_compatible:
                    status = "female_exclusion"
                    exclusions_female += 1
                elif not male_compatible:
                    status = "male_exclusion"
                    exclusions_male += 1
                else:
                    status = "inconclusive"
            else:
                if female_compatible:
                    status = "match"
                    matches += 1
                else:
                    status = "female_exclusion"
                    exclusions_female += 1
            
            marker_results.append({
                "marker_id": marker_id,
                "marker_name": marker["name"],
                "offspring_genotype": off_geno,
                "female_genotype": fem_geno,
                "male_genotype": mal_geno if mal_geno else "N/A",
                "female_compatible": female_compatible,
                "male_compatible": male_compatible,
                "status": status,
            })
        
        total_markers = len(marker_results)
        
        # Calculate likelihood ratio (simplified)
        if total_markers > 0:
            match_rate = matches / total_markers
            # Simplified LR calculation
            if exclusions_female == 0 and exclusions_male == 0:
                likelihood_ratio = 10 ** (matches * 0.5)  # Simplified
                conclusion = "CONFIRMED"
                confidence = min(99.9, 90 + matches)
            elif exclusions_female > 0 or exclusions_male > 2:
                likelihood_ratio = 0.01
                conclusion = "EXCLUDED"
                confidence = min(99.9, 90 + (exclusions_female + exclusions_male) * 5)
            else:
                likelihood_ratio = 1.0
                conclusion = "INCONCLUSIVE"
                confidence = 50.0
        else:
            match_rate = 0
            likelihood_ratio = 0
            conclusion = "INSUFFICIENT_DATA"
            confidence = 0
        
        result = {
            "analysis_id": f"PA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "offspring_id": offspring_id,
            "claimed_female_id": claimed_female_id,
            "claimed_male_id": claimed_male_id,
            "analysis_date": datetime.now().isoformat(),
            "summary": {
                "total_markers": total_markers,
                "matches": matches,
                "female_exclusions": exclusions_female,
                "male_exclusions": exclusions_male,
                "match_rate": round(match_rate * 100, 1),
                "likelihood_ratio": round(likelihood_ratio, 2),
                "conclusion": conclusion,
                "confidence": round(confidence, 1),
            },
            "marker_results": marker_results,
            "interpretation": self._get_interpretation(conclusion, exclusions_female, exclusions_male, claimed_male_id),
        }
        
        # Store analysis
        self.demo_analyses.append(result)
        
        return result
    
    def _get_interpretation(
        self,
        conclusion: str,
        exclusions_female: int,
        exclusions_male: int,
        has_male: bool
    ) -> str:
        """Generate human-readable interpretation"""
        if conclusion == "CONFIRMED":
            if has_male:
                return "The offspring is consistent with being the progeny of the claimed female and male parents. No exclusions were found at any marker."
            else:
                return "The offspring is consistent with being the progeny of the claimed female parent. No exclusions were found at any marker."
        elif conclusion == "EXCLUDED":
            parts = []
            if exclusions_female > 0:
                parts.append(f"The claimed female parent is EXCLUDED as the mother ({exclusions_female} marker exclusions)")
            if exclusions_male > 0:
                parts.append(f"The claimed male parent is EXCLUDED as the father ({exclusions_male} marker exclusions)")
            return ". ".join(parts) + ". The offspring cannot be the progeny of the claimed parent(s)."
        elif conclusion == "INCONCLUSIVE":
            return "The analysis is inconclusive. Some markers show exclusions but the number is within the range that could be due to mutation or genotyping error. Additional markers or re-genotyping is recommended."
        else:
            return "Insufficient marker data for reliable parentage analysis. More markers need to be genotyped."
    
    def find_parents(
        self,
        offspring_id: str,
        candidate_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Find potential parents for an offspring from a pool of candidates
        """
        if offspring_id not in self.demo_genotypes:
            return {"error": f"Offspring {offspring_id} not found"}
        
        # Use all individuals as candidates if not specified
        if candidate_ids is None:
            candidate_ids = [k for k in self.demo_genotypes.keys() if k != offspring_id]
        
        offspring = self.demo_genotypes[offspring_id]
        
        # Score each candidate
        candidates = []
        for cand_id in candidate_ids:
            if cand_id not in self.demo_genotypes or cand_id == offspring_id:
                continue
            
            candidate = self.demo_genotypes[cand_id]
            
            matches = 0
            exclusions = 0
            total = 0
            
            for marker in self.marker_panel:
                marker_id = marker["marker_id"]
                off_geno = offspring["markers"].get(marker_id, "")
                cand_geno = candidate["markers"].get(marker_id, "")
                
                if not off_geno or not cand_geno:
                    continue
                
                total += 1
                off_alleles = set(off_geno.split("/"))
                cand_alleles = set(cand_geno.split("/"))
                
                if off_alleles & cand_alleles:
                    matches += 1
                else:
                    exclusions += 1
            
            if total > 0:
                score = (matches / total) * 100
                candidates.append({
                    "candidate_id": cand_id,
                    "type": candidate["info"]["type"],
                    "matches": matches,
                    "exclusions": exclusions,
                    "total_markers": total,
                    "compatibility_score": round(score, 1),
                    "likely_parent": exclusions == 0,
                })
        
        # Sort by score
        candidates.sort(key=lambda x: (-x["compatibility_score"], x["exclusions"]))
        
        return {
            "offspring_id": offspring_id,
            "candidates_evaluated": len(candidates),
            "likely_parents": [c for c in candidates if c["likely_parent"]],
            "all_candidates": candidates,
        }
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get history of parentage analyses"""
        return [
            {
                "analysis_id": a["analysis_id"],
                "offspring_id": a["offspring_id"],
                "claimed_female_id": a["claimed_female_id"],
                "claimed_male_id": a["claimed_male_id"],
                "conclusion": a["summary"]["conclusion"],
                "confidence": a["summary"]["confidence"],
                "analysis_date": a["analysis_date"],
            }
            for a in self.demo_analyses
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parentage analysis statistics"""
        total = len(self.demo_analyses)
        if total == 0:
            return {
                "total_analyses": 0,
                "confirmed": 0,
                "excluded": 0,
                "inconclusive": 0,
                "confirmation_rate": 0,
            }
        
        confirmed = sum(1 for a in self.demo_analyses if a["summary"]["conclusion"] == "CONFIRMED")
        excluded = sum(1 for a in self.demo_analyses if a["summary"]["conclusion"] == "EXCLUDED")
        inconclusive = sum(1 for a in self.demo_analyses if a["summary"]["conclusion"] == "INCONCLUSIVE")
        
        return {
            "total_analyses": total,
            "confirmed": confirmed,
            "excluded": excluded,
            "inconclusive": inconclusive,
            "confirmation_rate": round(confirmed / total * 100, 1) if total > 0 else 0,
            "exclusion_rate": round(excluded / total * 100, 1) if total > 0 else 0,
        }


# Singleton instance
parentage_service = ParentageAnalysisService()
