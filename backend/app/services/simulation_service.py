"""
Sadhana Simulation Engine

Executes agricultural simulations defined by the SimulationProtocol.
Domain-agnostic engine that applies environmental drivers and stress factors to plant growth models.
"""
import logging
import math
from typing import Dict, Any, List
from datetime import datetime

from app.schemas.simulation import (
    SimulationProtocol, 
    SimulationInputs, 
    TimeStep, 
    StressType, 
    DomainType,
    MetricType
)

logger = logging.getLogger(__name__)

class SimulationState:
    def __init__(self, inputs: SimulationInputs):
        self.current_step_idx = 0
        self.total_days = 0
        self.biomass = 0.0 # kg
        self.survival_rate = 1.0 # 0.0 to 1.0
        self.stress_levels: Dict[str, float] = {}
        self.resources_consumed = {"water": 0.0, "energy": 0.0, "nutrients": 0.0}
        self.history: List[Dict[str, Any]] = []
        
        # Initial Biomass (Seed weight * quantity)
        # Simplified: 1g per seed * quantity
        total_seeds = sum(g.quantity for g in inputs.germplasm)
        self.biomass = (total_seeds * 0.001) 

class SimulationService:
    def __init__(self):
        pass

    async def run_simulation(self, protocol: SimulationProtocol) -> Dict[str, Any]:
        """
        Execute the full simulation based on the protocol.
        """
        logger.info(f"Starting Simulation: {protocol.metadata.name if protocol.metadata else protocol.simulation_id}")
        state = SimulationState(protocol.inputs)
        
        # Main Simulation Loop
        for step_idx, step in enumerate(protocol.time_steps):
            state.current_step_idx = step_idx
            self._process_time_step(step, protocol, state)
            
            # Check Termination Conditions
            if self._check_termination(protocol, state):
                break

        # Compile Results
        results = self._compile_results(protocol, state)
        return results

    def _process_time_step(self, step: TimeStep, protocol: SimulationProtocol, state: SimulationState):
        """Process a single time step (Growth + Stress)."""
        duration = step.duration.value # assuming days for simplicity
        state.total_days += duration
        
        # 1. Base Parameters
        env = protocol.inputs.environment
        # Apply overrides if any
        # (Simplified: ignoring overrides for first pass)

        # 2. Calculate Growth Factors
        # Light Factor
        light_hours = env.photoperiod.light_hours
        intensity = env.photoperiod.intensity_par or 400
        light_factor = min(1.0, (light_hours * intensity) / (16 * 600)) # Base benchmark 16h @ 600uMol
        
        # Temperature Factor
        avg_temp = (env.temperature.day + env.temperature.night) / 2
        # Ideal range 18-25C (Simplified Gaussian)
        temp_factor = math.exp(-0.5 * ((avg_temp - 22) / 5) ** 2)

        # 3. Calculate Stress Impact
        total_stress_penalty = 0.0
        active_stresses = self._get_active_stresses(protocol, step.step_id)
        
        for stress in active_stresses:
            impact = stress.intensity * 0.5 # Impact coefficient
            
            # Domain specific multipliers
            if protocol.domain == DomainType.MARS and stress.type == StressType.RADIATION:
                impact *= 1.2 # Radiation is worse on Mars
            
            total_stress_penalty += impact
            
            # Update state stress tracking
            state.stress_levels[stress.type] = stress.intensity

        # 4. Update State (Growth Equation)
        # Daily Growth Rate (Logistic Growth simplified)
        growth_potential = 0.05 # 5% per day base
        
        # Combined Environment Efficiency
        efficiency = light_factor * temp_factor * (1.0 - min(1.0, total_stress_penalty))
        
        # Apply Growth
        # Biomass = Biomass * (1 + rate)^days
        # But we apply linear approx for step to allow resource drain calc
        step_growth = state.biomass * (growth_potential * efficiency * duration)
        state.biomass += step_growth
        
        # Survival Attrition
        if total_stress_penalty > 0.5:
             attrition = (total_stress_penalty - 0.5) * 0.1 * duration # 10% loss per day of excess stress
             state.survival_rate = max(0.0, state.survival_rate - attrition)

        # Log Step
        state.history.append({
            "step": step.step_id,
            "phase": step.phase,
            "biomass": state.biomass,
            "survival": state.survival_rate,
            "stress_load": total_stress_penalty
        })

    def _get_active_stresses(self, protocol: SimulationProtocol, step_id: int):
        active = []
        if protocol.stress_factors:
            for stress in protocol.stress_factors:
                if stress.start_step <= step_id:
                    if stress.end_step is None or stress.end_step >= step_id:
                        active.append(stress)
        return active

    def _check_termination(self, protocol: SimulationProtocol, state: SimulationState) -> bool:
        if state.survival_rate <= 0:
            return True
            
        if protocol.termination_conditions:
             for cond in protocol.termination_conditions:
                 if cond.type == "survival_below" and state.survival_rate < cond.threshold:
                     return True
        return False

    def _compile_results(self, protocol: SimulationProtocol, state: SimulationState) -> Dict[str, Any]:
        outputs = {}
        for metric in protocol.outputs.metrics:
            if metric.type == MetricType.BIOMASS_YIELD:
                outputs[metric.name] = round(state.biomass, 2)
            elif metric.type == MetricType.SURVIVAL_RATE:
                outputs[metric.name] = round(state.survival_rate * 100, 1)
            elif metric.type == MetricType.DAYS_TO_MATURITY:
                outputs[metric.name] = round(state.total_days, 1)
        
        return {
            "simulation_id": str(protocol.simulation_id),
            "timestamp": datetime.now().isoformat(),
            "metrics": outputs,
            "steps_completed": state.current_step_idx + 1,
            "status": "COMPLETED" if state.survival_rate > 0 else "FAILED",
            "history": state.history if protocol.outputs.include_time_series else []
        }
