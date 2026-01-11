"""
Genetic Gain Service
Track and analyze genetic progress over breeding cycles
Calculate realized gain, genetic trend, and breeding efficiency
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
import math


class GeneticGainService:
    """Service for tracking genetic gain and breeding progress"""
    
    def __init__(self):
        # In-memory storage
        self.breeding_programs: Dict[str, Dict] = {}
        self.cycle_data: Dict[str, List[Dict]] = {}
        self.variety_releases: Dict[str, List[Dict]] = {}
        
        # Initialize sample data
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample breeding program data"""
        program = {
            "program_id": "PROG-001",
            "program_name": "Rice Yield Improvement",
            "crop": "Rice",
            "target_trait": "yield",
            "start_year": 2010,
            "organization": "Bijmantra Research",
            "created_at": datetime.now().isoformat(),
        }
        self.breeding_programs["PROG-001"] = program
        
        # Sample cycle data (yield in kg/ha)
        self.cycle_data["PROG-001"] = [
            {"cycle": 1, "year": 2010, "mean_yield": 4500, "best_yield": 5200, "n_entries": 500},
            {"cycle": 2, "year": 2012, "mean_yield": 4650, "best_yield": 5400, "n_entries": 450},
            {"cycle": 3, "year": 2014, "mean_yield": 4820, "best_yield": 5650, "n_entries": 400},
            {"cycle": 4, "year": 2016, "mean_yield": 5010, "best_yield": 5900, "n_entries": 380},
            {"cycle": 5, "year": 2018, "mean_yield": 5180, "best_yield": 6100, "n_entries": 350},
            {"cycle": 6, "year": 2020, "mean_yield": 5350, "best_yield": 6350, "n_entries": 320},
            {"cycle": 7, "year": 2022, "mean_yield": 5520, "best_yield": 6550, "n_entries": 300},
            {"cycle": 8, "year": 2024, "mean_yield": 5700, "best_yield": 6800, "n_entries": 280},
        ]
        
        self.variety_releases["PROG-001"] = [
            {"variety": "BijRice-1", "year": 2012, "yield": 5400},
            {"variety": "BijRice-2", "year": 2016, "yield": 5900},
            {"variety": "BijRice-3", "year": 2020, "yield": 6350},
            {"variety": "BijRice-4", "year": 2024, "yield": 6800},
        ]
    
    def create_program(
        self,
        program_name: str,
        crop: str,
        target_trait: str,
        start_year: int,
        organization: str,
    ) -> Dict:
        """Create a new breeding program for tracking"""
        program_id = f"PROG-{str(uuid4())[:8].upper()}"
        
        program = {
            "program_id": program_id,
            "program_name": program_name,
            "crop": crop,
            "target_trait": target_trait,
            "start_year": start_year,
            "organization": organization,
            "created_at": datetime.now().isoformat(),
        }
        
        self.breeding_programs[program_id] = program
        self.cycle_data[program_id] = []
        self.variety_releases[program_id] = []
        
        return program
    
    def record_cycle(
        self,
        program_id: str,
        cycle: int,
        year: int,
        mean_value: float,
        best_value: float,
        n_entries: int,
        check_value: Optional[float] = None,
        std_dev: Optional[float] = None,
    ) -> Dict:
        """Record data for a breeding cycle"""
        if program_id not in self.breeding_programs:
            raise ValueError(f"Program {program_id} not found")
        
        cycle_record = {
            "cycle": cycle,
            "year": year,
            "mean_value": mean_value,
            "best_value": best_value,
            "n_entries": n_entries,
            "check_value": check_value,
            "std_dev": std_dev,
            "recorded_at": datetime.now().isoformat(),
        }
        
        self.cycle_data[program_id].append(cycle_record)
        
        # Sort by cycle
        self.cycle_data[program_id].sort(key=lambda x: x["cycle"])
        
        return cycle_record
    
    def record_release(
        self,
        program_id: str,
        variety_name: str,
        year: int,
        trait_value: float,
    ) -> Dict:
        """Record a variety release"""
        if program_id not in self.breeding_programs:
            raise ValueError(f"Program {program_id} not found")
        
        release = {
            "variety": variety_name,
            "year": year,
            "value": trait_value,
            "recorded_at": datetime.now().isoformat(),
        }
        
        self.variety_releases[program_id].append(release)
        self.variety_releases[program_id].sort(key=lambda x: x["year"])
        
        return release
    
    def calculate_genetic_gain(
        self,
        program_id: str,
        use_mean: bool = True,
    ) -> Dict:
        """
        Calculate genetic gain over breeding cycles
        Returns absolute gain, percent gain, and annual rate
        """
        if program_id not in self.cycle_data:
            return {"error": f"Program {program_id} not found"}
        
        cycles = self.cycle_data[program_id]
        if len(cycles) < 2:
            return {"error": "Need at least 2 cycles to calculate gain"}
        
        # Get values
        value_key = "mean_value" if use_mean else "best_value"
        
        first_cycle = cycles[0]
        last_cycle = cycles[-1]
        
        initial_value = first_cycle[value_key]
        final_value = last_cycle[value_key]
        
        # Calculate gains
        absolute_gain = final_value - initial_value
        percent_gain = (absolute_gain / initial_value) * 100 if initial_value > 0 else 0
        
        # Years elapsed
        years = last_cycle["year"] - first_cycle["year"]
        annual_gain = absolute_gain / years if years > 0 else 0
        annual_percent = percent_gain / years if years > 0 else 0
        
        # Per cycle gain
        n_cycles = last_cycle["cycle"] - first_cycle["cycle"]
        gain_per_cycle = absolute_gain / n_cycles if n_cycles > 0 else 0
        
        # Linear regression for trend
        trend = self._calculate_trend(cycles, value_key)
        
        return {
            "program_id": program_id,
            "program_name": self.breeding_programs[program_id]["program_name"],
            "metric": "mean" if use_mean else "best",
            "initial_value": initial_value,
            "final_value": final_value,
            "absolute_gain": round(absolute_gain, 2),
            "percent_gain": round(percent_gain, 2),
            "years_elapsed": years,
            "cycles_completed": n_cycles,
            "annual_gain": round(annual_gain, 2),
            "annual_percent": round(annual_percent, 2),
            "gain_per_cycle": round(gain_per_cycle, 2),
            "trend_slope": round(trend["slope"], 4),
            "trend_r_squared": round(trend["r_squared"], 4),
        }
    
    def _calculate_trend(
        self,
        cycles: List[Dict],
        value_key: str,
    ) -> Dict:
        """Calculate linear trend using least squares regression"""
        n = len(cycles)
        if n < 2:
            return {"slope": 0, "intercept": 0, "r_squared": 0}
        
        # Use year as x, value as y
        x_values = [c["year"] for c in cycles]
        y_values = [c[value_key] for c in cycles]
        
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # Calculate slope and intercept
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator if denominator > 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared
        y_pred = [slope * x + intercept for x in x_values]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(y_values, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
        }
    
    def compare_to_check(
        self,
        program_id: str,
    ) -> Dict:
        """Compare breeding progress to check variety"""
        if program_id not in self.cycle_data:
            return {"error": f"Program {program_id} not found"}
        
        cycles = self.cycle_data[program_id]
        cycles_with_check = [c for c in cycles if c.get("check_value") is not None]
        
        if not cycles_with_check:
            return {"error": "No check variety data available"}
        
        comparisons = []
        for cycle in cycles_with_check:
            advantage = cycle["mean_value"] - cycle["check_value"]
            percent_advantage = (advantage / cycle["check_value"]) * 100 if cycle["check_value"] > 0 else 0
            
            comparisons.append({
                "cycle": cycle["cycle"],
                "year": cycle["year"],
                "mean_value": cycle["mean_value"],
                "check_value": cycle["check_value"],
                "advantage": round(advantage, 2),
                "percent_advantage": round(percent_advantage, 2),
            })
        
        # Average advantage
        avg_advantage = sum(c["advantage"] for c in comparisons) / len(comparisons)
        avg_percent = sum(c["percent_advantage"] for c in comparisons) / len(comparisons)
        
        return {
            "program_id": program_id,
            "comparisons": comparisons,
            "average_advantage": round(avg_advantage, 2),
            "average_percent_advantage": round(avg_percent, 2),
        }
    
    def calculate_realized_heritability(
        self,
        program_id: str,
    ) -> Dict:
        """
        Estimate realized heritability from selection response
        h² = R / S (response / selection differential)
        """
        if program_id not in self.cycle_data:
            return {"error": f"Program {program_id} not found"}
        
        cycles = self.cycle_data[program_id]
        if len(cycles) < 2:
            return {"error": "Need at least 2 cycles"}
        
        estimates = []
        for i in range(1, len(cycles)):
            prev = cycles[i - 1]
            curr = cycles[i]
            
            # Response = change in mean
            response = curr["mean_value"] - prev["mean_value"]
            
            # Selection differential = best - mean (approximation)
            selection_diff = prev["best_value"] - prev["mean_value"]
            
            if selection_diff > 0:
                h2_realized = response / selection_diff
                estimates.append({
                    "from_cycle": prev["cycle"],
                    "to_cycle": curr["cycle"],
                    "response": round(response, 2),
                    "selection_differential": round(selection_diff, 2),
                    "realized_h2": round(h2_realized, 4),
                })
        
        if not estimates:
            return {"error": "Could not calculate heritability"}
        
        avg_h2 = sum(e["realized_h2"] for e in estimates) / len(estimates)
        
        return {
            "program_id": program_id,
            "estimates": estimates,
            "average_realized_h2": round(avg_h2, 4),
            "note": "Realized heritability estimated from R/S",
        }
    
    def project_future_gain(
        self,
        program_id: str,
        years_ahead: int = 10,
    ) -> Dict:
        """Project future genetic gain based on historical trend"""
        gain_data = self.calculate_genetic_gain(program_id)
        
        if "error" in gain_data:
            return gain_data
        
        annual_gain = gain_data["annual_gain"]
        current_value = gain_data["final_value"]
        
        projections = []
        current_year = datetime.now().year
        
        for i in range(1, years_ahead + 1):
            projected_value = current_value + (annual_gain * i)
            projections.append({
                "year": current_year + i,
                "projected_value": round(projected_value, 2),
                "gain_from_current": round(annual_gain * i, 2),
            })
        
        return {
            "program_id": program_id,
            "current_value": current_value,
            "annual_gain_rate": annual_gain,
            "projections": projections,
            "note": "Linear projection based on historical trend",
        }
    
    def get_program_summary(self, program_id: str) -> Dict:
        """Get comprehensive summary of breeding program progress"""
        if program_id not in self.breeding_programs:
            return {"error": f"Program {program_id} not found"}
        
        program = self.breeding_programs[program_id]
        cycles = self.cycle_data.get(program_id, [])
        releases = self.variety_releases.get(program_id, [])
        
        gain_mean = self.calculate_genetic_gain(program_id, use_mean=True)
        gain_best = self.calculate_genetic_gain(program_id, use_mean=False)
        
        return {
            "program": program,
            "total_cycles": len(cycles),
            "total_releases": len(releases),
            "cycle_data": cycles,
            "variety_releases": releases,
            "genetic_gain_mean": gain_mean if "error" not in gain_mean else None,
            "genetic_gain_best": gain_best if "error" not in gain_best else None,
        }
    
    def list_programs(self) -> List[Dict]:
        """List all breeding programs"""
        return list(self.breeding_programs.values())
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        programs = list(self.breeding_programs.values())
        
        total_cycles = sum(len(self.cycle_data.get(p["program_id"], [])) for p in programs)
        total_releases = sum(len(self.variety_releases.get(p["program_id"], [])) for p in programs)
        
        crops = list(set(p["crop"] for p in programs))
        
        return {
            "total_programs": len(programs),
            "total_cycles_recorded": total_cycles,
            "total_variety_releases": total_releases,
            "crops": crops,
        }


# Singleton instance
genetic_gain_service = GeneticGainService()
