"""
Pedigree Analysis Service for Plant Breeding
Relationship matrices, inbreeding coefficients, and pedigree visualization

Features:
- Additive relationship matrix (A-matrix)
- Inbreeding coefficient calculation
- Pedigree path tracing
- Coefficient of coancestry
- Pedigree completeness index
"""

from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """Individual in pedigree"""
    id: str
    sire_id: Optional[str] = None
    dam_id: Optional[str] = None
    generation: int = 0
    inbreeding: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sire_id": self.sire_id,
            "dam_id": self.dam_id,
            "generation": self.generation,
            "inbreeding_coefficient": round(self.inbreeding, 4),
        }


@dataclass
class PedigreeStats:
    """Pedigree statistics"""
    n_individuals: int
    n_founders: int
    n_generations: int
    avg_inbreeding: float
    max_inbreeding: float
    completeness: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_individuals": self.n_individuals,
            "n_founders": self.n_founders,
            "n_generations": self.n_generations,
            "avg_inbreeding": round(self.avg_inbreeding, 4),
            "max_inbreeding": round(self.max_inbreeding, 4),
            "completeness_index": round(self.completeness, 2),
        }


class PedigreeService:
    """
    Pedigree analysis for plant breeding
    """

    def __init__(self):
        self.individuals: Dict[str, Individual] = {}
        self.a_matrix: Dict[Tuple[str, str], float] = {}

    def load_pedigree(
        self,
        pedigree_data: List[Dict[str, Any]]
    ) -> PedigreeStats:
        """
        Load pedigree data
        
        Args:
            pedigree_data: List of {id, sire_id, dam_id} dicts
            
        Returns:
            PedigreeStats with summary
        """
        self.individuals.clear()
        self.a_matrix.clear()

        # First pass: create all individuals
        for record in pedigree_data:
            ind_id = str(record["id"])
            sire_id = record.get("sire_id") or record.get("sire")
            dam_id = record.get("dam_id") or record.get("dam")

            self.individuals[ind_id] = Individual(
                id=ind_id,
                sire_id=str(sire_id) if sire_id else None,
                dam_id=str(dam_id) if dam_id else None,
            )

        # Add missing parents as founders
        all_parents = set()
        for ind in self.individuals.values():
            if ind.sire_id and ind.sire_id not in self.individuals:
                all_parents.add(ind.sire_id)
            if ind.dam_id and ind.dam_id not in self.individuals:
                all_parents.add(ind.dam_id)

        for parent_id in all_parents:
            self.individuals[parent_id] = Individual(id=parent_id)

        # Calculate generations
        self._calculate_generations()

        # Calculate inbreeding coefficients
        self._calculate_inbreeding()

        # Calculate statistics
        founders = [i for i in self.individuals.values()
                   if i.sire_id is None and i.dam_id is None]

        inbreeding_values = [i.inbreeding for i in self.individuals.values()]

        return PedigreeStats(
            n_individuals=len(self.individuals),
            n_founders=len(founders),
            n_generations=max(i.generation for i in self.individuals.values()) + 1,
            avg_inbreeding=sum(inbreeding_values) / len(inbreeding_values) if inbreeding_values else 0,
            max_inbreeding=max(inbreeding_values) if inbreeding_values else 0,
            completeness=self._calculate_completeness(),
        )

    def _calculate_generations(self):
        """Calculate generation number for each individual"""
        # Topological sort based on parent-child relationships
        changed = True
        while changed:
            changed = False
            for ind in self.individuals.values():
                parent_gen = -1
                if ind.sire_id and ind.sire_id in self.individuals:
                    parent_gen = max(parent_gen, self.individuals[ind.sire_id].generation)
                if ind.dam_id and ind.dam_id in self.individuals:
                    parent_gen = max(parent_gen, self.individuals[ind.dam_id].generation)

                new_gen = parent_gen + 1
                if new_gen > ind.generation:
                    ind.generation = new_gen
                    changed = True

    def _calculate_inbreeding(self):
        """
        Calculate inbreeding coefficients using tabular method
        F(i) = 0.5 * A(sire, dam)
        """
        # Sort by generation
        sorted_ids = sorted(
            self.individuals.keys(),
            key=lambda x: self.individuals[x].generation
        )

        # Initialize A-matrix diagonal for founders
        for ind_id in sorted_ids:
            ind = self.individuals[ind_id]
            if ind.sire_id is None and ind.dam_id is None:
                self.a_matrix[(ind_id, ind_id)] = 1.0
                ind.inbreeding = 0.0

        # Calculate for non-founders
        for ind_id in sorted_ids:
            ind = self.individuals[ind_id]
            if ind.sire_id is None and ind.dam_id is None:
                continue

            # Inbreeding = 0.5 * relationship between parents
            if ind.sire_id and ind.dam_id:
                a_parents = self._get_relationship(ind.sire_id, ind.dam_id)
                ind.inbreeding = 0.5 * a_parents
            else:
                ind.inbreeding = 0.0

            # Diagonal element: 1 + F
            self.a_matrix[(ind_id, ind_id)] = 1.0 + ind.inbreeding

            # Off-diagonal elements
            for other_id in sorted_ids:
                if other_id == ind_id:
                    continue

                other = self.individuals[other_id]
                if other.generation > ind.generation:
                    continue

                # A(i,j) = 0.5 * (A(sire_i, j) + A(dam_i, j))
                a_sire = self._get_relationship(ind.sire_id, other_id) if ind.sire_id else 0
                a_dam = self._get_relationship(ind.dam_id, other_id) if ind.dam_id else 0

                relationship = 0.5 * (a_sire + a_dam)
                self.a_matrix[(ind_id, other_id)] = relationship
                self.a_matrix[(other_id, ind_id)] = relationship

    def _get_relationship(self, id1: Optional[str], id2: Optional[str]) -> float:
        """Get additive relationship between two individuals"""
        if id1 is None or id2 is None:
            return 0.0
        if id1 == id2:
            return self.a_matrix.get((id1, id1), 1.0)

        # Try both orderings
        return self.a_matrix.get((id1, id2), 0.0) or self.a_matrix.get((id2, id1), 0.0)

    def _calculate_completeness(self) -> float:
        """
        Calculate pedigree completeness index
        Average proportion of known ancestors across generations
        """
        if not self.individuals:
            return 0.0

        total_completeness = 0.0
        n_non_founders = 0

        for ind in self.individuals.values():
            if ind.sire_id is None and ind.dam_id is None:
                continue

            n_non_founders += 1
            known = 0
            if ind.sire_id:
                known += 1
            if ind.dam_id:
                known += 1
            total_completeness += known / 2.0

        return (total_completeness / n_non_founders * 100) if n_non_founders > 0 else 100.0

    def get_relationship_matrix(
        self,
        individual_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get additive relationship matrix (A-matrix)
        
        Args:
            individual_ids: Subset of individuals (None = all)
            
        Returns:
            Matrix as nested dict with individual IDs
        """
        ids = individual_ids or list(self.individuals.keys())
        ids = [i for i in ids if i in self.individuals]

        matrix = {}
        for id1 in ids:
            matrix[id1] = {}
            for id2 in ids:
                matrix[id1][id2] = round(self._get_relationship(id1, id2), 4)

        return {
            "individuals": ids,
            "matrix": matrix,
            "n_individuals": len(ids),
        }

    def get_ancestors(
        self,
        individual_id: str,
        max_generations: int = 5
    ) -> Dict[str, Any]:
        """
        Trace ancestors of an individual
        
        Args:
            individual_id: Target individual
            max_generations: Maximum generations to trace
            
        Returns:
            Ancestor tree structure
        """
        if individual_id not in self.individuals:
            return {"error": f"Individual {individual_id} not found"}

        def trace(ind_id: str, gen: int) -> Optional[Dict]:
            if gen > max_generations or ind_id not in self.individuals:
                return None

            ind = self.individuals[ind_id]
            result = {
                "id": ind_id,
                "generation": gen,
                "inbreeding": round(ind.inbreeding, 4),
            }

            if ind.sire_id:
                result["sire"] = trace(ind.sire_id, gen + 1)
            if ind.dam_id:
                result["dam"] = trace(ind.dam_id, gen + 1)

            return result

        return {
            "individual": individual_id,
            "max_generations": max_generations,
            "tree": trace(individual_id, 0),
        }

    def get_descendants(
        self,
        individual_id: str,
        max_generations: int = 3
    ) -> Dict[str, Any]:
        """
        Find descendants of an individual
        
        Args:
            individual_id: Target individual
            max_generations: Maximum generations to trace
            
        Returns:
            List of descendants by generation
        """
        if individual_id not in self.individuals:
            return {"error": f"Individual {individual_id} not found"}

        descendants: Dict[int, List[str]] = {0: [individual_id]}

        for gen in range(max_generations):
            current_gen = descendants.get(gen, [])
            next_gen = []

            for parent_id in current_gen:
                for ind in self.individuals.values():
                    if ind.sire_id == parent_id or ind.dam_id == parent_id:
                        if ind.id not in next_gen:
                            next_gen.append(ind.id)

            if next_gen:
                descendants[gen + 1] = next_gen
            else:
                break

        return {
            "individual": individual_id,
            "descendants_by_generation": {
                f"gen_{k}": v for k, v in descendants.items() if k > 0
            },
            "total_descendants": sum(len(v) for k, v in descendants.items() if k > 0),
        }

    def calculate_coancestry(
        self,
        id1: str,
        id2: str
    ) -> Dict[str, Any]:
        """
        Calculate coefficient of coancestry between two individuals
        
        Coancestry = 0.5 * A(i,j)
        """
        if id1 not in self.individuals or id2 not in self.individuals:
            return {"error": "One or both individuals not found"}

        relationship = self._get_relationship(id1, id2)
        coancestry = 0.5 * relationship

        # Interpret relationship
        if relationship >= 0.99:
            interpretation = "Same individual or identical twin"
        elif relationship >= 0.49:
            interpretation = "Full siblings or parent-offspring"
        elif relationship >= 0.24:
            interpretation = "Half siblings or grandparent-grandchild"
        elif relationship >= 0.12:
            interpretation = "First cousins"
        elif relationship >= 0.06:
            interpretation = "Second cousins"
        elif relationship > 0:
            interpretation = "Distant relatives"
        else:
            interpretation = "Unrelated"

        return {
            "individual_1": id1,
            "individual_2": id2,
            "additive_relationship": round(relationship, 4),
            "coancestry": round(coancestry, 4),
            "interpretation": interpretation,
            "expected_offspring_inbreeding": round(coancestry, 4),
        }

    def get_individual(self, individual_id: str) -> Optional[Dict[str, Any]]:
        """Get individual details"""
        if individual_id not in self.individuals:
            return None
        return self.individuals[individual_id].to_dict()

    def list_individuals(
        self,
        generation: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List all individuals, optionally filtered by generation"""
        result = []
        for ind in self.individuals.values():
            if generation is None or ind.generation == generation:
                result.append(ind.to_dict())
        return sorted(result, key=lambda x: (x["generation"], x["id"]))


# Singleton
_pedigree_service: Optional[PedigreeService] = None


def get_pedigree_service() -> PedigreeService:
    """Get or create pedigree service singleton"""
    global _pedigree_service
    if _pedigree_service is None:
        _pedigree_service = PedigreeService()
    return _pedigree_service
