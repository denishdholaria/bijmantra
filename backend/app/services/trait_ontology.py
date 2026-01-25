"""
Trait Ontology Service for Plant Breeding
Standardized trait definitions and measurement protocols

Features:
- Trait definitions with ontology IDs
- Measurement scales and methods
- Trait categories and hierarchies
- Variable definitions (trait + method + scale)
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScaleType(str, Enum):
    NOMINAL = "nominal"  # Categories without order
    ORDINAL = "ordinal"  # Ordered categories
    NUMERICAL = "numerical"  # Continuous values
    DATE = "date"
    TEXT = "text"


class TraitCategory(str, Enum):
    MORPHOLOGICAL = "morphological"
    AGRONOMIC = "agronomic"
    PHYSIOLOGICAL = "physiological"
    BIOCHEMICAL = "biochemical"
    PHENOLOGICAL = "phenological"
    QUALITY = "quality"
    STRESS = "stress"
    MOLECULAR = "molecular"


@dataclass
class Scale:
    """Measurement scale definition"""
    scale_id: str
    name: str
    scale_type: ScaleType
    unit: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    categories: Optional[List[Dict[str, str]]] = None  # For nominal/ordinal
    decimal_places: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "scale_id": self.scale_id,
            "name": self.name,
            "scale_type": self.scale_type.value,
            "unit": self.unit,
            "decimal_places": self.decimal_places,
        }
        if self.min_value is not None:
            result["min_value"] = self.min_value
        if self.max_value is not None:
            result["max_value"] = self.max_value
        if self.categories:
            result["categories"] = self.categories
        return result


@dataclass
class Method:
    """Measurement method definition"""
    method_id: str
    name: str
    description: str
    formula: str = ""
    reference: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_id": self.method_id,
            "name": self.name,
            "description": self.description,
            "formula": self.formula,
            "reference": self.reference,
        }


@dataclass
class Trait:
    """Trait definition"""
    trait_id: str
    name: str
    description: str
    category: TraitCategory
    ontology_id: str = ""  # e.g., CO_320:0000001
    synonyms: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trait_id": self.trait_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "ontology_id": self.ontology_id,
            "synonyms": self.synonyms or [],
        }


@dataclass
class Variable:
    """Observation variable (trait + method + scale)"""
    variable_id: str
    name: str
    trait: Trait
    method: Method
    scale: Scale
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_id": self.variable_id,
            "name": self.name,
            "trait": self.trait.to_dict(),
            "method": self.method.to_dict(),
            "scale": self.scale.to_dict(),
        }


class TraitOntologyService:
    """
    Trait ontology management
    """
    
    def __init__(self):
        self.traits: Dict[str, Trait] = {}
        self.methods: Dict[str, Method] = {}
        self.scales: Dict[str, Scale] = {}
        self.variables: Dict[str, Variable] = {}
        
        # Initialize common traits
        self._init_common_traits()
    
    def _init_common_traits(self):
        """Initialize common plant breeding traits"""
        # Agronomic traits
        common_traits = [
            Trait("T001", "Plant Height", "Height of plant from ground to tip", TraitCategory.MORPHOLOGICAL, "CO_320:0000001", ["height", "PH"]),
            Trait("T002", "Days to Flowering", "Days from sowing to 50% flowering", TraitCategory.PHENOLOGICAL, "CO_320:0000002", ["DTF", "flowering time"]),
            Trait("T003", "Days to Maturity", "Days from sowing to physiological maturity", TraitCategory.PHENOLOGICAL, "CO_320:0000003", ["DTM", "maturity"]),
            Trait("T004", "Grain Yield", "Grain yield per unit area", TraitCategory.AGRONOMIC, "CO_320:0000004", ["yield", "GY"]),
            Trait("T005", "1000 Grain Weight", "Weight of 1000 grains", TraitCategory.AGRONOMIC, "CO_320:0000005", ["TGW", "seed weight"]),
            Trait("T006", "Tiller Number", "Number of productive tillers per plant", TraitCategory.MORPHOLOGICAL, "CO_320:0000006", ["tillers"]),
            Trait("T007", "Panicle Length", "Length of panicle", TraitCategory.MORPHOLOGICAL, "CO_320:0000007", ["PL"]),
            Trait("T008", "Grain Length", "Length of grain", TraitCategory.QUALITY, "CO_320:0000008", ["GL"]),
            Trait("T009", "Grain Width", "Width of grain", TraitCategory.QUALITY, "CO_320:0000009", ["GW"]),
            Trait("T010", "Protein Content", "Grain protein percentage", TraitCategory.BIOCHEMICAL, "CO_320:0000010", ["protein"]),
            Trait("T011", "Amylose Content", "Grain amylose percentage", TraitCategory.BIOCHEMICAL, "CO_320:0000011", ["amylose"]),
            Trait("T012", "Disease Score", "Disease severity score", TraitCategory.STRESS, "CO_320:0000012", ["disease"]),
            Trait("T013", "Drought Tolerance", "Drought tolerance score", TraitCategory.STRESS, "CO_320:0000013", ["drought"]),
            Trait("T014", "Lodging Score", "Lodging resistance score", TraitCategory.AGRONOMIC, "CO_320:0000014", ["lodging"]),
            Trait("T015", "Chlorophyll Content", "Leaf chlorophyll content (SPAD)", TraitCategory.PHYSIOLOGICAL, "CO_320:0000015", ["SPAD", "greenness"]),
        ]
        
        for trait in common_traits:
            self.traits[trait.trait_id] = trait
        
        # Common scales
        common_scales = [
            Scale("S001", "Centimeters", ScaleType.NUMERICAL, "cm", 0, 500, decimal_places=1),
            Scale("S002", "Days", ScaleType.NUMERICAL, "days", 0, 365, decimal_places=0),
            Scale("S003", "Kilograms per hectare", ScaleType.NUMERICAL, "kg/ha", 0, 20000, decimal_places=0),
            Scale("S004", "Grams", ScaleType.NUMERICAL, "g", 0, 100, decimal_places=2),
            Scale("S005", "Percentage", ScaleType.NUMERICAL, "%", 0, 100, decimal_places=1),
            Scale("S006", "Count", ScaleType.NUMERICAL, "count", 0, 1000, decimal_places=0),
            Scale("S007", "Millimeters", ScaleType.NUMERICAL, "mm", 0, 100, decimal_places=2),
            Scale("S008", "1-9 Scale", ScaleType.ORDINAL, "", 1, 9, categories=[
                {"value": "1", "label": "Highly resistant/Excellent"},
                {"value": "3", "label": "Resistant/Good"},
                {"value": "5", "label": "Moderately resistant/Average"},
                {"value": "7", "label": "Susceptible/Poor"},
                {"value": "9", "label": "Highly susceptible/Very poor"},
            ]),
            Scale("S009", "SPAD units", ScaleType.NUMERICAL, "SPAD", 0, 70, decimal_places=1),
        ]
        
        for scale in common_scales:
            self.scales[scale.scale_id] = scale
        
        # Common methods
        common_methods = [
            Method("M001", "Ruler measurement", "Measure with ruler from base to tip", "", "Standard method"),
            Method("M002", "Visual counting", "Count by visual observation", "", "Standard method"),
            Method("M003", "Weighing", "Weigh using precision balance", "", "Standard method"),
            Method("M004", "NIR spectroscopy", "Near-infrared spectroscopy analysis", "", "AACC Method"),
            Method("M005", "Visual scoring", "Score using standard evaluation scale", "", "IRRI SES"),
            Method("M006", "SPAD meter", "Measure with SPAD-502 chlorophyll meter", "", "Minolta"),
        ]
        
        for method in common_methods:
            self.methods[method.method_id] = method
    
    def register_trait(
        self,
        trait_id: str,
        name: str,
        description: str,
        category: str,
        ontology_id: str = "",
        synonyms: List[str] = None
    ) -> Trait:
        """Register a new trait"""
        trait = Trait(
            trait_id=trait_id,
            name=name,
            description=description,
            category=TraitCategory(category),
            ontology_id=ontology_id,
            synonyms=synonyms or [],
        )
        self.traits[trait_id] = trait
        return trait
    
    def register_scale(
        self,
        scale_id: str,
        name: str,
        scale_type: str,
        unit: str = "",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        categories: Optional[List[Dict[str, str]]] = None,
        decimal_places: int = 2
    ) -> Scale:
        """Register a new scale"""
        scale = Scale(
            scale_id=scale_id,
            name=name,
            scale_type=ScaleType(scale_type),
            unit=unit,
            min_value=min_value,
            max_value=max_value,
            categories=categories,
            decimal_places=decimal_places,
        )
        self.scales[scale_id] = scale
        return scale
    
    def register_method(
        self,
        method_id: str,
        name: str,
        description: str,
        formula: str = "",
        reference: str = ""
    ) -> Method:
        """Register a new method"""
        method = Method(
            method_id=method_id,
            name=name,
            description=description,
            formula=formula,
            reference=reference,
        )
        self.methods[method_id] = method
        return method
    
    def create_variable(
        self,
        variable_id: str,
        name: str,
        trait_id: str,
        method_id: str,
        scale_id: str
    ) -> Variable:
        """Create an observation variable"""
        if trait_id not in self.traits:
            raise ValueError(f"Trait {trait_id} not found")
        if method_id not in self.methods:
            raise ValueError(f"Method {method_id} not found")
        if scale_id not in self.scales:
            raise ValueError(f"Scale {scale_id} not found")
        
        variable = Variable(
            variable_id=variable_id,
            name=name,
            trait=self.traits[trait_id],
            method=self.methods[method_id],
            scale=self.scales[scale_id],
        )
        self.variables[variable_id] = variable
        return variable
    
    def list_traits(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List traits with optional category filter"""
        result = []
        for trait in self.traits.values():
            if category and trait.category.value != category:
                continue
            result.append(trait.to_dict())
        return result
    
    def list_scales(self) -> List[Dict[str, Any]]:
        """List all scales"""
        return [s.to_dict() for s in self.scales.values()]
    
    def list_methods(self) -> List[Dict[str, Any]]:
        """List all methods"""
        return [m.to_dict() for m in self.methods.values()]
    
    def list_variables(self) -> List[Dict[str, Any]]:
        """List all variables"""
        return [v.to_dict() for v in self.variables.values()]
    
    def search_traits(self, query: str) -> List[Dict[str, Any]]:
        """Search traits by name or synonym"""
        query_lower = query.lower()
        results = []
        
        for trait in self.traits.values():
            if query_lower in trait.name.lower():
                results.append(trait.to_dict())
            elif trait.synonyms and any(query_lower in s.lower() for s in trait.synonyms):
                results.append(trait.to_dict())
        
        return results


# Singleton
_ontology_service: Optional[TraitOntologyService] = None


def get_ontology_service() -> TraitOntologyService:
    """Get or create ontology service singleton"""
    global _ontology_service
    if _ontology_service is None:
        _ontology_service = TraitOntologyService()
    return _ontology_service
