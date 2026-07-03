"""
Trait Ontology API for Plant Breeding
Standardized trait definitions and measurement protocols

Endpoints:
- GET /api/v2/ontology/traits - List traits
- POST /api/v2/ontology/traits - Register trait
- GET /api/v2/ontology/traits/search - Search traits
- GET /api/v2/ontology/scales - List scales
- POST /api/v2/ontology/scales - Register scale
- GET /api/v2/ontology/methods - List methods
- POST /api/v2/ontology/methods - Register method
- GET /api/v2/ontology/variables - List variables
- POST /api/v2/ontology/variables - Create variable
"""


import ast
import operator
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_current_user
from app.modules.phenotyping.services.trait_ontology_service import get_ontology_service


router = APIRouter(prefix="/ontology", tags=["Trait Ontology"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class TraitRegisterRequest(BaseModel):
    """Request to register a trait"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "trait_id": "T100",
            "name": "Leaf Area",
            "description": "Total leaf area per plant",
            "category": "morphological",
            "ontology_id": "CO_320:0000100",
            "synonyms": ["LA", "leaf size"]
        }
    })

    trait_id: str = Field(..., description="Unique trait ID")
    name: str = Field(..., description="Trait name")
    description: str = Field(..., description="Trait description")
    category: str = Field(..., description="Category: morphological, agronomic, physiological, biochemical, phenological, quality, stress, molecular")
    ontology_id: str = Field("", description="External ontology ID (e.g., CO_320:0000001)")
    synonyms: list[str] = Field([], description="Alternative names")


class ScaleRegisterRequest(BaseModel):
    """Request to register a scale"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "scale_id": "S100",
            "name": "Square centimeters",
            "scale_type": "numerical",
            "unit": "cm²",
            "min_value": 0,
            "max_value": 10000,
            "decimal_places": 1
        }
    })

    scale_id: str = Field(..., description="Unique scale ID")
    name: str = Field(..., description="Scale name")
    scale_type: str = Field(..., description="Type: nominal, ordinal, numerical, date, text")
    unit: str = Field("", description="Unit of measurement")
    min_value: float | None = Field(None, description="Minimum value (for numerical)")
    max_value: float | None = Field(None, description="Maximum value (for numerical)")
    categories: list[dict[str, str]] | None = Field(None, description="Categories (for nominal/ordinal)")
    decimal_places: int = Field(2, description="Decimal places (for numerical)")


class MethodRegisterRequest(BaseModel):
    """Request to register a method"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "method_id": "M100",
            "name": "Leaf area meter",
            "description": "Measure using LI-COR leaf area meter",
            "formula": "",
            "reference": "LI-COR LI-3100C"
        }
    })

    method_id: str = Field(..., description="Unique method ID")
    name: str = Field(..., description="Method name")
    description: str = Field(..., description="Method description")
    formula: str = Field("", description="Calculation formula (if applicable)")
    reference: str = Field("", description="Reference/citation")


class VariableCreateRequest(BaseModel):
    """Request to create a variable"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "variable_id": "V001",
            "name": "Plant Height (cm)",
            "trait_id": "T001",
            "method_id": "M001",
            "scale_id": "S001"
        }
    })

    variable_id: str = Field(..., description="Unique variable ID")
    name: str = Field(..., description="Variable name")
    trait_id: str = Field(..., description="Trait ID")
    method_id: str = Field(..., description="Method ID")
    scale_id: str = Field(..., description="Scale ID")


# ============================================
# ENDPOINTS
# ============================================

@router.get("/traits")
async def list_traits(
    category: str | None = Query(None, description="Filter by category")
):
    """
    List trait definitions

    Includes 15 common plant breeding traits by default.
    """
    service = get_ontology_service()

    traits = service.list_traits(category=category)

    return {
        "success": True,
        "count": len(traits),
        "category_filter": category,
        "traits": traits,
    }


@router.post("/traits")
async def register_trait(request: TraitRegisterRequest):
    """Register a new trait definition"""
    service = get_ontology_service()

    try:
        trait = service.register_trait(
            trait_id=request.trait_id,
            name=request.name,
            description=request.description,
            category=request.category,
            ontology_id=request.ontology_id,
            synonyms=request.synonyms,
        )

        return {
            "success": True,
            "message": f"Trait {request.trait_id} registered",
            **trait.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register trait: {str(e)}")


@router.get("/traits/search")
async def search_traits(
    q: str = Query(..., min_length=2, description="Search query")
):
    """Search traits by name or synonym"""
    service = get_ontology_service()

    results = service.search_traits(q)

    return {
        "success": True,
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/scales")
async def list_scales():
    """
    List measurement scales

    Includes common scales for plant breeding measurements.
    """
    service = get_ontology_service()

    scales = service.list_scales()

    return {
        "success": True,
        "count": len(scales),
        "scales": scales,
    }


@router.post("/scales")
async def register_scale(request: ScaleRegisterRequest):
    """Register a new measurement scale"""
    service = get_ontology_service()

    try:
        scale = service.register_scale(
            scale_id=request.scale_id,
            name=request.name,
            scale_type=request.scale_type,
            unit=request.unit,
            min_value=request.min_value,
            max_value=request.max_value,
            categories=request.categories,
            decimal_places=request.decimal_places,
        )

        return {
            "success": True,
            "message": f"Scale {request.scale_id} registered",
            **scale.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register scale: {str(e)}")


@router.get("/methods")
async def list_methods():
    """
    List measurement methods

    Includes common methods for plant breeding observations.
    """
    service = get_ontology_service()

    methods = service.list_methods()

    return {
        "success": True,
        "count": len(methods),
        "methods": methods,
    }


@router.post("/methods")
async def register_method(request: MethodRegisterRequest):
    """Register a new measurement method"""
    service = get_ontology_service()

    try:
        method = service.register_method(
            method_id=request.method_id,
            name=request.name,
            description=request.description,
            formula=request.formula,
            reference=request.reference,
        )

        return {
            "success": True,
            "message": f"Method {request.method_id} registered",
            **method.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to register method: {str(e)}")


@router.get("/variables")
async def list_variables():
    """
    List observation variables

    Variables combine trait + method + scale for standardized observations.
    """
    service = get_ontology_service()

    variables = service.list_variables()

    return {
        "success": True,
        "count": len(variables),
        "variables": variables,
    }


@router.post("/variables")
async def create_variable(request: VariableCreateRequest):
    """
    Create an observation variable

    Combines a trait, method, and scale into a standardized variable.
    """
    service = get_ontology_service()

    try:
        variable = service.create_variable(
            variable_id=request.variable_id,
            name=request.name,
            trait_id=request.trait_id,
            method_id=request.method_id,
            scale_id=request.scale_id,
        )

        return {
            "success": True,
            "message": f"Variable {request.variable_id} created",
            **variable.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to create variable: {str(e)}")


@router.get("/categories")
async def list_categories():
    """List trait categories"""
    return {
        "categories": [
            {"id": "morphological", "name": "Morphological", "description": "Plant structure and form"},
            {"id": "agronomic", "name": "Agronomic", "description": "Yield and production traits"},
            {"id": "physiological", "name": "Physiological", "description": "Plant function and processes"},
            {"id": "biochemical", "name": "Biochemical", "description": "Chemical composition"},
            {"id": "phenological", "name": "Phenological", "description": "Growth stages and timing"},
            {"id": "quality", "name": "Quality", "description": "Grain/product quality"},
            {"id": "stress", "name": "Stress", "description": "Biotic and abiotic stress response"},
            {"id": "molecular", "name": "Molecular", "description": "Molecular markers and genes"},
            {"id": "text", "name": "Text", "description": "Free text observations"}
        ]
    }


# ============================================
# FORMULAS (Dynamic Trait Calculation)
# ============================================

class FormulaInput(BaseModel):
    name: str
    unit: str

class FormulaOutput(BaseModel):
    name: str
    unit: str

class Formula(BaseModel):
    id: str
    name: str
    category: str
    formula: str  # Display string
    inputs: list[FormulaInput]
    output: FormulaOutput
    python_expression: str | None = Field(None, description="Python-evaluable expression using input keys")


# Seed Data
SEEDED_FORMULAS = [
  {
    "id": "harvest-index",
    "name": "Harvest Index",
    "category": "Yield",
    "formula": "HI = (Grain Yield / Total Biomass) * 100",
    "inputs": [{"name": "Grain Yield", "unit": "g"}, {"name": "Total Biomass", "unit": "g"}],
    "output": {"name": "Harvest Index", "unit": "%"},
    "python_expression": "(grain_yield / total_biomass) * 100 if total_biomass > 0 else 0"
  },
  {
    "id": "yield-per-ha",
    "name": "Yield per Hectare",
    "category": "Yield",
    "formula": "Yield (t/ha) = (Plot Yield * 10000) / Plot Area",
    "inputs": [{"name": "Plot Yield", "unit": "kg"}, {"name": "Plot Area", "unit": "m2"}],
    "output": {"name": "Yield", "unit": "t/ha"},
    "python_expression": "(plot_yield * 10000) / plot_area if plot_area > 0 else 0"
  },
  {
    "id": "thousand-grain-weight",
    "name": "1000 Grain Weight",
    "category": "Grain",
    "formula": "TGW = (Sample Weight / Grain Count) * 1000",
    "inputs": [{"name": "Sample Weight", "unit": "g"}, {"name": "Grain Count", "unit": "count"}],
    "output": {"name": "1000 Grain Weight", "unit": "g"},
    "python_expression": "(sample_weight / grain_count) * 1000 if grain_count > 0 else 0"
  },
  {
    "id": "grain-moisture",
    "name": "Grain Moisture",
    "category": "Grain",
    "formula": "Moisture = ((Wet - Dry) / Wet) * 100",
    "inputs": [{"name": "Wet Weight", "unit": "g"}, {"name": "Dry Weight", "unit": "g"}],
    "output": {"name": "Moisture Content", "unit": "%"},
    "python_expression": "((wet_weight - dry_weight) / wet_weight) * 100 if wet_weight > 0 else 0"
  },
  {
    "id": "plant-density",
    "name": "Plant Density",
    "category": "Agronomy",
    "formula": "Density = (Plant Count / Plot Area) * 10000",
    "inputs": [{"name": "Plant Count", "unit": "count"}, {"name": "Plot Area", "unit": "m2"}],
    "output": {"name": "Plant Density", "unit": "plants/ha"},
    "python_expression": "(plant_count / plot_area) * 10000 if plot_area > 0 else 0"
  },
  {
    "id": "lodging-score",
    "name": "Lodging Score",
    "category": "Agronomy",
    "formula": "Score = (Lodged Area / Total Area) * Severity",
    "inputs": [{"name": "Lodged Area", "unit": "%"}, {"name": "Severity", "unit": "1-5"}],
    "output": {"name": "Lodging Score", "unit": "score"},
    "python_expression": "(lodged_area / 100) * severity"
  },
  {
    "id": "relative-yield",
    "name": "Relative Yield",
    "category": "Yield",
    "formula": "RY = (Entry Yield / Check Yield) * 100",
    "inputs": [{"name": "Entry Yield", "unit": "t/ha"}, {"name": "Check Yield", "unit": "t/ha"}],
    "output": {"name": "Relative Yield", "unit": "%"},
    "python_expression": "(entry_yield / check_yield) * 100 if check_yield > 0 else 0"
  },
  {
    "id": "protein-yield",
    "name": "Protein Yield",
    "category": "Quality",
    "formula": "Protein Yield = Grain Yield * (Protein % / 100)",
    "inputs": [{"name": "Grain Yield", "unit": "t/ha"}, {"name": "Protein Content", "unit": "%"}],
    "output": {"name": "Protein Yield", "unit": "t/ha"},
    "python_expression": "grain_yield * (protein_content / 100)"
  }
]

@router.get("/formulas", response_model=dict[str, list[Formula]])
async def list_formulas():
    """List available trait calculation formulas"""
    return {"formulas": SEEDED_FORMULAS}

class CalculateRequest(BaseModel):
    formula_id: str
    inputs: dict[str, float]

class CalculateResponse(BaseModel):
    result: float
    unit: str

# ============================================
# SAFE EVALUATION
# ============================================

class SafeEvaluator:
    def __init__(self, variables):
        self.variables = variables
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.Mod: operator.mod,
        }

    def evaluate(self, node):
        if isinstance(node, ast.Expression):
            return self.evaluate(node.body)
        elif isinstance(node, ast.Constant): # Python >= 3.8
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            raise ValueError(f"Unknown variable: {node.id}")
        elif isinstance(node, ast.BinOp):
            return self.operators[type(node.op)](self.evaluate(node.left), self.evaluate(node.right))
        elif isinstance(node, ast.UnaryOp):
             if type(node.op) in self.operators:
                 return self.operators[type(node.op)](self.evaluate(node.operand))
             raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(self.evaluate(v) for v in node.values)
            elif isinstance(node.op, ast.Or):
                return any(self.evaluate(v) for v in node.values)
            raise ValueError(f"Unsupported boolean operator: {type(node.op)}")
        elif isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("Only simple comparisons supported")
            left = self.evaluate(node.left)
            op = type(node.ops[0])
            right = self.evaluate(node.comparators[0])
            if op in self.operators:
                return self.operators[op](left, right)
            raise ValueError(f"Unsupported comparison operator: {op}")
        elif isinstance(node, ast.IfExp):
            test = self.evaluate(node.test)
            if test:
                return self.evaluate(node.body)
            else:
                return self.evaluate(node.orelse)
        else:
            raise ValueError(f"Unsupported syntax: {type(node)}")

def safe_eval(expr, variables):
    try:
        expr = expr.strip()
        tree = ast.parse(expr, mode='eval')
        return SafeEvaluator(variables).evaluate(tree)
    except Exception as e:
        raise ValueError(f"Safe eval failed: {e}")

@router.post("/formulas/calculate", response_model=CalculateResponse)
async def calculate_formula(request: CalculateRequest):
    """Calculate result using a backend formula"""
    # Find formula
    formula = next((f for f in SEEDED_FORMULAS if f["id"] == request.formula_id), None)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")

    # Map inputs to snake_case variable names for python_expression
    # Simple normalizer: lowercase and replace space with underscore
    eval_context = {}
    for inp in formula["inputs"]:
        key = inp["name"].lower().replace(" ", "_").replace("²", "") # basic cleaning
        # Attempt to find matching key in request.inputs
        # Request inputs matches the 'name' in singular form or snake_case?
        # Frontend usually sends what we define.
        # Let's assume frontend sends keys matching the schema we provided?
        # Actually frontend is sending array of numbers in current impl.
        # We will need frontend to send dictionary.

        # We'll try to match request inputs by name
        val = request.inputs.get(inp["name"])
        if val is None:
             # Try snake case
             val = request.inputs.get(key)

        if val is None:
             raise HTTPException(status_code=400, detail=f"Missing input: {inp['name']}")

        eval_context[key] = val

    try:
        # Secure evaluation using AST parser
        result = safe_eval(formula["python_expression"], eval_context)
        return {"result": float(result), "unit": formula["output"]["unit"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")
