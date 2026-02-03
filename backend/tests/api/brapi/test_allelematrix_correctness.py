
import pytest
from dataclasses import dataclass

# Mock classes to mimic the SQLAlchemy models
@dataclass
class MockVariant:
    variant_db_id: str

@dataclass
class MockCallSet:
    call_set_db_id: str

@dataclass
class MockCall:
    call_set: MockCallSet
    variant: MockVariant
    genotype_value: str

def baseline_impl(variants, call_sets, calls):
    """
    The original O(N^2) implementation for reference.
    """
    matrix = []
    for var in variants:
        row = []
        for cs in call_sets:
            # Find call for this variant and callset
            call = next(
                (c for c in calls
                 if c.call_set.call_set_db_id == cs.call_set_db_id
                 and c.variant.variant_db_id == var.variant_db_id),
                None
            )
            row.append(call.genotype_value if call else "./.")
        matrix.append(row)
    return matrix

def optimized_impl(variants, call_sets, calls):
    """
    The new O(N) implementation.
    """
    calls_map = {
        (c.variant.variant_db_id, c.call_set.call_set_db_id): c
        for c in calls
    }

    matrix = []
    for var in variants:
        row = []
        for cs in call_sets:
            call = calls_map.get((var.variant_db_id, cs.call_set_db_id))
            row.append(call.genotype_value if call else "./.")
        matrix.append(row)
    return matrix

def test_allelematrix_optimization_correctness():
    """
    Verifies that the optimized implementation produces exactly the same result
    as the baseline implementation for a variety of scenarios.
    """
    # 1. Sparse data
    variants = [MockVariant(f"v{i}") for i in range(5)]
    call_sets = [MockCallSet(f"cs{i}") for i in range(5)]
    calls = [
        MockCall(call_sets[0], variants[0], "0/0"),
        MockCall(call_sets[1], variants[1], "0/1"),
        MockCall(call_sets[4], variants[4], "1/1"),
        MockCall(call_sets[2], variants[3], "1/0"),
    ]

    base_result = baseline_impl(variants, call_sets, calls)
    opt_result = optimized_impl(variants, call_sets, calls)

    assert base_result == opt_result
    assert base_result[0][0] == "0/0"
    assert base_result[0][1] == "./." # Missing

    # 2. Dense data
    calls = []
    for v in variants:
        for cs in call_sets:
            calls.append(MockCall(cs, v, "0/0"))

    base_result = baseline_impl(variants, call_sets, calls)
    opt_result = optimized_impl(variants, call_sets, calls)
    assert base_result == opt_result
    assert all(all(cell == "0/0" for cell in row) for row in opt_result)

    # 3. Empty data
    calls = []
    base_result = baseline_impl(variants, call_sets, calls)
    opt_result = optimized_impl(variants, call_sets, calls)
    assert base_result == opt_result
    assert all(all(cell == "./." for cell in row) for row in opt_result)
