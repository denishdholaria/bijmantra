"""
Selection Index Service
Multi-trait selection indices for plant breeding
Implements Smith-Hazel, Desired Gains, and other selection methods
"""

import math
from datetime import datetime
from uuid import uuid4


class SelectionIndexService:
    """Service for multi-trait selection index calculations"""

    def __init__(self):
        # In-memory storage
        self.indices: dict[str, dict] = {}
        self.trait_weights: dict[str, dict] = {}
        self.selection_results: dict[str, list[dict]] = {}

        # Default economic weights for common traits
        self.default_weights = {
            "yield": 1.0,
            "protein_content": 0.5,
            "disease_resistance": 0.8,
            "drought_tolerance": 0.7,
            "days_to_maturity": -0.3,  # Negative = prefer lower
            "plant_height": -0.2,
            "lodging_resistance": 0.6,
            "grain_quality": 0.5,
            "oil_content": 0.4,
            "fiber_strength": 0.5,
        }

    def smith_hazel_index(
        self,
        phenotypic_values: list[dict[str, float]],
        trait_names: list[str],
        economic_weights: list[float],
        heritabilities: list[float],
        genetic_correlations: list[list[float]] | None = None,  # noqa: ARG002
        phenotypic_correlations: list[list[float]] | None = None,  # noqa: ARG002
    ) -> dict:
        """
        Calculate Smith-Hazel selection index
        I = b1*P1 + b2*P2 + ... + bn*Pn
        where b = P^-1 * G * a (index coefficients)
        
        Simplified version using heritabilities as weights
        """
        n_traits = len(trait_names)
        n_individuals = len(phenotypic_values)

        if len(economic_weights) != n_traits or len(heritabilities) != n_traits:
            raise ValueError("Mismatch in number of traits")

        # Calculate index coefficients (simplified: b = h² * a)
        index_coefficients = [
            h2 * w for h2, w in zip(heritabilities, economic_weights, strict=True)
        ]

        # Calculate index values for each individual
        results = []
        for i, individual in enumerate(phenotypic_values):
            index_value = 0.0
            trait_contributions = {}

            for j, trait in enumerate(trait_names):
                if trait in individual:
                    contribution = index_coefficients[j] * individual[trait]
                    index_value += contribution
                    trait_contributions[trait] = {
                        "value": individual[trait],
                        "coefficient": index_coefficients[j],
                        "contribution": contribution,
                    }

            results.append({
                "individual_id": individual.get("id", f"IND-{i+1}"),
                "index_value": round(index_value, 4),
                "trait_contributions": trait_contributions,
            })

        # Sort by index value (descending)
        results.sort(key=lambda x: x["index_value"], reverse=True)

        # Add rank
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return {
            "method": "smith_hazel",
            "n_traits": n_traits,
            "n_individuals": n_individuals,
            "trait_names": trait_names,
            "economic_weights": economic_weights,
            "heritabilities": heritabilities,
            "index_coefficients": dict(zip(trait_names, index_coefficients, strict=True)),
            "results": results,
            "top_10_percent": results[:max(1, n_individuals // 10)],
        }

    def desired_gains_index(
        self,
        phenotypic_values: list[dict[str, float]],
        trait_names: list[str],
        desired_gains: list[float],
        heritabilities: list[float],
        current_means: list[float] | None = None,
    ) -> dict:
        """
        Calculate Desired Gains (Pesek-Baker) selection index
        Weights are calculated to achieve specified genetic gains
        """
        n_traits = len(trait_names)
        n_individuals = len(phenotypic_values)

        # Calculate current means if not provided
        if current_means is None:
            current_means = []
            for trait in trait_names:
                values = [ind.get(trait, 0) for ind in phenotypic_values]
                current_means.append(sum(values) / len(values) if values else 0)

        # Calculate weights based on desired gains and heritabilities
        # Simplified: w = desired_gain / h²
        weights = []
        for _i, (gain, h2) in enumerate(zip(desired_gains, heritabilities, strict=True)):
            if h2 > 0:
                weights.append(gain / h2)
            else:
                weights.append(0)

        # Normalize weights
        max_weight = max(abs(w) for w in weights) if weights else 1
        normalized_weights = [w / max_weight for w in weights]

        # Calculate index values
        results = []
        for i, individual in enumerate(phenotypic_values):
            index_value = 0.0
            standardized_values = {}

            for j, trait in enumerate(trait_names):
                if trait in individual:
                    # Standardize relative to current mean
                    std_value = individual[trait] - current_means[j]
                    contribution = normalized_weights[j] * std_value
                    index_value += contribution
                    standardized_values[trait] = {
                        "raw_value": individual[trait],
                        "standardized": std_value,
                        "weight": normalized_weights[j],
                        "contribution": contribution,
                    }

            results.append({
                "individual_id": individual.get("id", f"IND-{i+1}"),
                "index_value": round(index_value, 4),
                "trait_values": standardized_values,
            })

        # Sort by index value
        results.sort(key=lambda x: x["index_value"], reverse=True)

        for i, r in enumerate(results):
            r["rank"] = i + 1

        return {
            "method": "desired_gains",
            "n_traits": n_traits,
            "n_individuals": n_individuals,
            "trait_names": trait_names,
            "desired_gains": dict(zip(trait_names, desired_gains, strict=True)),
            "current_means": dict(zip(trait_names, current_means, strict=True)),
            "calculated_weights": dict(zip(trait_names, normalized_weights, strict=True)),
            "results": results,
            "top_10_percent": results[:max(1, n_individuals // 10)],
        }

    def base_index(
        self,
        phenotypic_values: list[dict[str, float]],
        trait_names: list[str],
        weights: list[float],
    ) -> dict:
        """
        Simple base index (weighted sum of phenotypic values)
        I = w1*P1 + w2*P2 + ... + wn*Pn
        """
        n_individuals = len(phenotypic_values)

        results = []
        for i, individual in enumerate(phenotypic_values):
            index_value = 0.0
            for j, trait in enumerate(trait_names):
                if trait in individual:
                    index_value += weights[j] * individual[trait]

            results.append({
                "individual_id": individual.get("id", f"IND-{i+1}"),
                "index_value": round(index_value, 4),
            })

        results.sort(key=lambda x: x["index_value"], reverse=True)

        for i, r in enumerate(results):
            r["rank"] = i + 1

        return {
            "method": "base_index",
            "n_traits": len(trait_names),
            "n_individuals": n_individuals,
            "trait_names": trait_names,
            "weights": dict(zip(trait_names, weights, strict=True)),
            "results": results,
        }

    def independent_culling(
        self,
        phenotypic_values: list[dict[str, float]],
        trait_names: list[str],
        thresholds: list[float],
        threshold_types: list[str],  # "min" or "max"
    ) -> dict:
        """
        Independent culling levels selection
        Select individuals that meet ALL threshold criteria
        """
        n_individuals = len(phenotypic_values)

        selected = []
        rejected = []

        for i, individual in enumerate(phenotypic_values):
            ind_id = individual.get("id", f"IND-{i+1}")
            passes_all = True
            trait_status = {}

            for j, trait in enumerate(trait_names):
                value = individual.get(trait)
                threshold = thresholds[j]
                threshold_type = threshold_types[j]

                if value is None:
                    passes = False
                elif threshold_type == "min":
                    passes = value >= threshold
                else:  # max
                    passes = value <= threshold

                trait_status[trait] = {
                    "value": value,
                    "threshold": threshold,
                    "type": threshold_type,
                    "passes": passes,
                }

                if not passes:
                    passes_all = False

            result = {
                "individual_id": ind_id,
                "selected": passes_all,
                "trait_status": trait_status,
            }

            if passes_all:
                selected.append(result)
            else:
                rejected.append(result)

        return {
            "method": "independent_culling",
            "n_traits": len(trait_names),
            "n_individuals": n_individuals,
            "thresholds": dict(zip(trait_names, thresholds, strict=True)),
            "threshold_types": dict(zip(trait_names, threshold_types, strict=True)),
            "n_selected": len(selected),
            "n_rejected": len(rejected),
            "selection_rate": len(selected) / n_individuals if n_individuals > 0 else 0,
            "selected": selected,
            "rejected": rejected,
        }

    def tandem_selection(
        self,
        phenotypic_values: list[dict[str, float]],
        trait_sequence: list[str],
        selection_intensities: list[float],
    ) -> dict:
        """
        Tandem selection - select for one trait at a time in sequence
        """
        current_population = phenotypic_values.copy()
        selection_history = []

        for i, trait in enumerate(trait_sequence):
            intensity = selection_intensities[i]
            n_select = max(1, int(len(current_population) * intensity))

            # Sort by trait value
            sorted_pop = sorted(
                current_population,
                key=lambda x: x.get(trait, float('-inf')),
                reverse=True
            )

            selected = sorted_pop[:n_select]

            selection_history.append({
                "round": i + 1,
                "trait": trait,
                "intensity": intensity,
                "input_size": len(current_population),
                "selected_size": len(selected),
                "selected_ids": [s.get("id", f"IND-{j}") for j, s in enumerate(selected)],
            })

            current_population = selected

        return {
            "method": "tandem_selection",
            "trait_sequence": trait_sequence,
            "selection_intensities": selection_intensities,
            "initial_population": len(phenotypic_values),
            "final_population": len(current_population),
            "overall_selection_rate": len(current_population) / len(phenotypic_values),
            "selection_history": selection_history,
            "final_selected": [
                {"individual_id": ind.get("id", f"IND-{i}"), **ind}
                for i, ind in enumerate(current_population)
            ],
        }

    def calculate_selection_differential(
        self,
        all_values: list[float],
        selected_values: list[float],
    ) -> dict:
        """Calculate selection differential and intensity"""
        if not all_values or not selected_values:
            return {"error": "Empty value lists"}

        pop_mean = sum(all_values) / len(all_values)
        selected_mean = sum(selected_values) / len(selected_values)

        # Population standard deviation
        variance = sum((x - pop_mean) ** 2 for x in all_values) / len(all_values)
        std_dev = math.sqrt(variance) if variance > 0 else 1

        selection_differential = selected_mean - pop_mean
        selection_intensity = selection_differential / std_dev if std_dev > 0 else 0

        return {
            "population_mean": round(pop_mean, 4),
            "selected_mean": round(selected_mean, 4),
            "population_std": round(std_dev, 4),
            "selection_differential": round(selection_differential, 4),
            "selection_intensity": round(selection_intensity, 4),
            "proportion_selected": len(selected_values) / len(all_values),
        }

    def predict_response(
        self,
        selection_intensity: float,
        heritability: float,
        phenotypic_std: float,
    ) -> dict:
        """
        Predict response to selection
        R = i * h² * σp (Breeder's equation)
        """
        response = selection_intensity * heritability * phenotypic_std

        return {
            "selection_intensity": selection_intensity,
            "heritability": heritability,
            "phenotypic_std": phenotypic_std,
            "predicted_response": round(response, 4),
            "formula": "R = i × h² × σp",
        }

    def get_selection_methods(self) -> list[dict]:
        """Get available selection methods"""
        return [
            {
                "code": "smith_hazel",
                "name": "Smith-Hazel Index",
                "description": "Optimal index using genetic parameters",
                "requires": ["economic_weights", "heritabilities"],
            },
            {
                "code": "desired_gains",
                "name": "Desired Gains (Pesek-Baker)",
                "description": "Index to achieve specified genetic gains",
                "requires": ["desired_gains", "heritabilities"],
            },
            {
                "code": "base_index",
                "name": "Base Index",
                "description": "Simple weighted sum of phenotypes",
                "requires": ["weights"],
            },
            {
                "code": "independent_culling",
                "name": "Independent Culling Levels",
                "description": "Threshold-based selection on multiple traits",
                "requires": ["thresholds"],
            },
            {
                "code": "tandem",
                "name": "Tandem Selection",
                "description": "Sequential selection for one trait at a time",
                "requires": ["trait_sequence", "selection_intensities"],
            },
        ]

    def get_default_weights(self) -> dict[str, float]:
        """Get default economic weights for common traits"""
        return self.default_weights.copy()

    def save_index(self, index_data: dict) -> dict:
        """Save a selection index configuration"""
        index_id = str(uuid4())
        index_data["id"] = index_id
        index_data["created_at"] = datetime.now().isoformat()
        self.indices[index_id] = index_data
        return index_data

    def list_indices(self) -> list[dict]:
        """List all saved indices"""
        return list(self.indices.values())

    def get_index(self, index_id: str) -> dict | None:
        """Get a specific index by ID"""
        return self.indices.get(index_id)


# Singleton instance
selection_index_service = SelectionIndexService()
