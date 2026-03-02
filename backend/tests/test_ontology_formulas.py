import sys
from unittest.mock import MagicMock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import approx

# -----------------------------------------------------------------------------
# MOCK HEAVY DEPENDENCIES BEFORE IMPORTING ROUTER
# -----------------------------------------------------------------------------
from app.api.v2.ontology import router
from app.api.deps import get_current_user

# -----------------------------------------------------------------------------
# SETUP APP
# -----------------------------------------------------------------------------
app = FastAPI()
app.include_router(router)

app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "test"}

client = TestClient(app)

# Helper to verify formula calculation
def calculate(formula_id, inputs):
    return client.post(
        "/ontology/formulas/calculate",
        json={"formula_id": formula_id, "inputs": inputs}
    )

# -----------------------------------------------------------------------------
# GROUP 1: SEEDED FORMULAS (40 Test Cases)
# -----------------------------------------------------------------------------

# 1. Harvest Index
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Grain Yield": 500, "Total Biomass": 1000}, 200, 50.0),
    ({"Grain Yield": 0, "Total Biomass": 1000}, 200, 0.0),
    ({"Grain Yield": 500, "Total Biomass": 0}, 200, 0.0),
    ({"Grain Yield": -500, "Total Biomass": 1000}, 200, -50.0),
    ({"Grain Yield": 1000, "Total Biomass": 1000}, 200, 100.0),
])
def test_harvest_index(inputs, expected_status, expected_result):
    response = calculate("harvest-index", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)

# 2. Yield per Hectare
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Plot Yield": 5, "Plot Area": 10}, 200, 5000.0),
    ({"Plot Yield": 0, "Plot Area": 10}, 200, 0.0),
    ({"Plot Yield": 5, "Plot Area": 0}, 200, 0.0),
    ({"Plot Yield": 1000, "Plot Area": 10000}, 200, 1000.0),
    ({"Plot Yield": 0.001, "Plot Area": 1}, 200, 10.0),
])
def test_yield_per_ha(inputs, expected_status, expected_result):
    response = calculate("yield-per-ha", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)

# 3. 1000 Grain Weight
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Sample Weight": 25, "Grain Count": 500}, 200, 50.0),
    ({"Sample Weight": 0, "Grain Count": 500}, 200, 0.0),
    ({"Sample Weight": 25, "Grain Count": 0}, 200, 0.0),
    ({"Sample Weight": 50, "Grain Count": 1000}, 200, 50.0),
    ({"Sample Weight": 1, "Grain Count": 20}, 200, 50.0),
])
def test_thousand_grain_weight(inputs, expected_status, expected_result):
    response = calculate("thousand-grain-weight", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)

# 4. Grain Moisture
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Wet Weight": 100, "Dry Weight": 86}, 200, 14.0),
    ({"Wet Weight": 100, "Dry Weight": 100}, 200, 0.0),
    ({"Wet Weight": 100, "Dry Weight": 0}, 200, 100.0),
    ({"Wet Weight": 0, "Dry Weight": 0}, 200, 0.0),
    ({"Wet Weight": 100, "Dry Weight": 110}, 200, -10.0),
])
def test_grain_moisture(inputs, expected_status, expected_result):
    response = calculate("grain-moisture", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)

# 5. Plant Density
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Plant Count": 60, "Plot Area": 10}, 200, 60000.0),
    ({"Plant Count": 0, "Plot Area": 10}, 200, 0.0),
    ({"Plant Count": 60, "Plot Area": 0}, 200, 0.0),
    ({"Plant Count": 1, "Plot Area": 10000}, 200, 1.0),
    ({"Plant Count": 1000, "Plot Area": 1}, 200, 10000000.0),
])
def test_plant_density(inputs, expected_status, expected_result):
    response = calculate("plant-density", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)

# 6. Lodging Score
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Lodged Area": 20, "Severity": 3}, 200, 0.6),
    ({"Lodged Area": 0, "Severity": 5}, 200, 0.0),
    ({"Lodged Area": 100, "Severity": 5}, 200, 5.0),
    ({"Lodged Area": 50, "Severity": 1}, 200, 0.5),
    ({"Lodged Area": 200, "Severity": 3}, 200, 6.0),
])
def test_lodging_score(inputs, expected_status, expected_result):
    response = calculate("lodging-score", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)

# 7. Relative Yield
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Entry Yield": 6, "Check Yield": 5}, 200, 120.0),
    ({"Entry Yield": 5, "Check Yield": 5}, 200, 100.0),
    ({"Entry Yield": 0, "Check Yield": 5}, 200, 0.0),
    ({"Entry Yield": 5, "Check Yield": 0}, 200, 0.0),
    ({"Entry Yield": 2.5, "Check Yield": 5}, 200, 50.0),
])
def test_relative_yield(inputs, expected_status, expected_result):
    response = calculate("relative-yield", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)

# 8. Protein Yield
@pytest.mark.parametrize("inputs, expected_status, expected_result", [
    ({"Grain Yield": 5, "Protein Content": 12}, 200, 0.6),
    ({"Grain Yield": 0, "Protein Content": 12}, 200, 0.0),
    ({"Grain Yield": 5, "Protein Content": 0}, 200, 0.0),
    ({"Grain Yield": 10, "Protein Content": 100}, 200, 10.0),
    ({"Grain Yield": 5, "Protein Content": 50}, 200, 2.5),
])
def test_protein_yield(inputs, expected_status, expected_result):
    response = calculate("protein-yield", inputs)
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["result"] == approx(expected_result)


# -----------------------------------------------------------------------------
# GROUP 2: CUSTOM FORMULAS & ENGINE LOGIC (60 Test Cases)
# -----------------------------------------------------------------------------

CUSTOM_TEST_CASES = [
    # Basic Arithmetic
    (41, "Add", "a + b", {"a": 1, "b": 2}, 3.0),
    (42, "Sub", "a - b", {"a": 5, "b": 3}, 2.0),
    (43, "Mul", "a * b", {"a": 4, "b": 2}, 8.0),
    (44, "Div", "a / b", {"a": 10, "b": 2}, 5.0),
    (45, "Float Add", "a + b", {"a": 1.1, "b": 2.2}, 3.3),

    # Division by Zero Handling in Expression
    (46, "DivZero", "a / b if b != 0 else 0", {"a": 10, "b": 0}, 0.0),
    (47, "DivZeroUnsafe", "a / b", {"a": 10, "b": 0}, "ERROR"),

    # Precedence
    (48, "Prec1", "a + b * c", {"a": 2, "b": 3, "c": 4}, 14.0),
    (49, "Prec2", "(a + b) * c", {"a": 2, "b": 3, "c": 4}, 20.0),

    # Power
    (50, "Pow", "a ** b", {"a": 2, "b": 3}, 8.0),
    (51, "Pow2", "a ** 0.5", {"a": 9}, 3.0),

    # Modulo
    (52, "Mod", "a % b", {"a": 10, "b": 3}, 1.0),

    # Variable naming (snake_case conversion test)
    (53, "SpaceVar", "my_var * 2", {"My Var": 5}, 10.0),
    (54, "CaseVar", "myvar * 2", {"MyVar": 5}, 10.0),
    (55, "MixedCase", "variable_a + variable_b", {"Variable A": 1, "Variable B": 2}, 3.0),

    # Unused variables
    (56, "Unused", "a + b", {"a": 1, "b": 2, "c": 3}, 3.0),

    # Negative numbers
    (57, "NegInput", "a + b", {"a": -5, "b": 2}, -3.0),
    (58, "NegResult", "a - b", {"a": 5, "b": 10}, -5.0),

    # Complex expressions
    (59, "Complex1", "(a + b) / (c - d)", {"a": 10, "b": 2, "c": 5, "d": 2}, 4.0),
    (60, "Complex2", "a * b + c * d", {"a": 2, "b": 3, "c": 4, "d": 5}, 26.0),

    # Logic Operators
    (61, "Logic1", "100 if a > b else 0", {"a": 5, "b": 3}, 100.0),
    (62, "Logic2", "100 if a > b else 0", {"a": 2, "b": 3}, 0.0),
    (63, "LogicAnd", "1 if a > 0 and b > 0 else 0", {"a": 1, "b": 1}, 1.0),
    (64, "LogicAndFail", "1 if a > 0 and b > 0 else 0", {"a": 1, "b": -1}, 0.0),

    # Large Numbers
    (65, "Large", "a * b", {"a": 1e10, "b": 1e10}, 1e20),

    # Small Numbers
    (66, "Small", "a * b", {"a": 1e-10, "b": 1e-10}, 1e-20),

    # String constant in return
    (67, "StringConst", "'Pass' if a > 5 else 'Fail'", {"a": 6}, "ERROR"),

    # Security/Builtins (Expect Failure)
    (68, "BuiltinAbs", "abs(a)", {"a": -5}, "ERROR"),
    (69, "BuiltinMax", "max(a, b)", {"a": 1, "b": 2}, "ERROR"),
    (70, "BuiltinMin", "min(a, b)", {"a": 1, "b": 2}, "ERROR"),
    (71, "Import", "__import__('os').system('ls')", {}, "ERROR"),

    # Missing Inputs
    (72, "MissingInput", "a + b", {"a": 1}, "ERROR"),

    # Extra Spaces in Formula
    (73, "Spaces", "  a   +   b  ", {"a": 1, "b": 2}, 3.0),

    # Syntax Error
    (74, "SyntaxError", "(a + b", {"a": 1, "b": 2}, "ERROR"),

    # Undefined variable
    (75, "UndefinedVar", "a + c", {"a": 1, "b": 2}, "ERROR"),

    # Boolean inputs
    (76, "BoolInput", "a + b", {"a": True, "b": False}, 1.0),

    # Integer inputs
    (77, "IntInput", "a + b", {"a": 1, "b": 2}, 3.0),

    # Case Sensitivity Check 2
    (78, "CaseSens", "AbC + aBc", {"abc": 1, "ABC": 2}, "ERROR"),

    # More Arithmetic
    (79, "NegMult", "a * -1", {"a": 5}, -5.0),
    (80, "DoubleNeg", "-a", {"a": -5}, 5.0),

    # Floating point literal
    (81, "FloatLit", "a * 1.5", {"a": 2}, 3.0),

    # Comparison
    (82, "CompGT", "1.0 if a > b else 0.0", {"a": 2, "b": 1}, 1.0),
    (83, "CompLT", "1.0 if a < b else 0.0", {"a": 1, "b": 2}, 1.0),
    (84, "CompEQ", "1.0 if a == b else 0.0", {"a": 2, "b": 2}, 1.0),

    # Identity
    (85, "Identity", "a", {"a": 42}, 42.0),

    # Constant
    (86, "Constant", "42", {}, 42.0),

    # Zero
    (87, "Zero", "0", {}, 0.0),

    # Scientific Notation in Formula
    (88, "SciNot", "1e2 * a", {"a": 2}, 200.0),

    # Multiple Operations
    (89, "MultiOp", "a + b - c * d / e", {"a": 10, "b": 20, "c": 5, "d": 4, "e": 2}, 20.0),

    # Nested Parens
    (90, "Nested", "((a + b) * c)", {"a": 1, "b": 2, "c": 3}, 9.0),

    # Bitwise
    (91, "BitOr", "int(a) | int(b)", {"a": 1, "b": 2}, "ERROR"),
    (92, "BitOrFloat", "a | b", {"a": 1.0, "b": 2.0}, "ERROR"),

    # Squared char replacement
    (93, "SquaredChar", "area * 2", {"Area²": 10}, 20.0),

    # Space in name
    (94, "SpaceName", "my_variable * 2", {"My Variable": 5}, 10.0),

    # Underscores
    (95, "UnderScores", "a_b_c", {"A B C": 10}, 10.0),

    # Numbers in name
    (96, "NumName", "var1 + var2", {"Var1": 1, "Var2": 2}, 3.0),

    # Keyword conflict
    (97, "Keyword", "class_ * 2", {"Class": 5}, "ERROR"),

    # Overflow
    (98, "Overflow", "a ** b", {"a": 1e100, "b": 100}, "ERROR"),

    # Stripped special
    (99, "StripSpecial", "area", {"Area²": 5}, 5.0),

    # Final check
    (100, "Final", "a + b + c", {"a": 1, "b": 1, "c": 1}, 3.0)
]

@pytest.mark.parametrize("case_id, name, expression, inputs, expected", CUSTOM_TEST_CASES)
def test_custom_formulas(case_id, name, expression, inputs, expected):
    """
    Test the calculation engine with custom formulas injected via mocking.
    """
    formula_inputs = [{"name": k, "unit": "u"} for k in inputs.keys()]

    custom_formula = {
        "id": f"custom-{case_id}",
        "name": name,
        "category": "Test",
        "formula": "Display Formula",
        "inputs": formula_inputs,
        "output": {"name": "Result", "unit": "u"},
        "python_expression": expression
    }

    with patch("app.api.v2.ontology.SEEDED_FORMULAS", [custom_formula]):
        response = calculate(f"custom-{case_id}", inputs)

        if expected == "ERROR":
            assert response.status_code in [400, 500, 422]
        else:
            assert response.status_code == 200
            result = response.json()["result"]
            assert result == approx(expected), f"Case {case_id}: expected {expected}, got {result}"
