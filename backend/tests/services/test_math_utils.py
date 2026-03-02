import pytest
from backend.app.services.math_utils import clamp, safe_divide

def test_clamp_within_range():
    """Test clamp when value is within the range."""
    assert clamp(5, 0, 10) == 5
    assert clamp(5.0, 0.0, 10.0) == 5.0
    assert clamp(0.5, 0.0, 1.0) == 0.5

def test_clamp_below_minimum():
    """Test clamp when value is below the minimum."""
    assert clamp(-5, 0, 10) == 0
    assert clamp(-5.0, 0.0, 10.0) == 0.0
    assert clamp(-0.1, 0.0, 1.0) == 0.0

def test_clamp_above_maximum():
    """Test clamp when value is above the maximum."""
    assert clamp(15, 0, 10) == 10
    assert clamp(15.0, 0.0, 10.0) == 10.0
    assert clamp(1.1, 0.0, 1.0) == 1.0

def test_clamp_boundary_values():
    """Test clamp when value equals the minimum or maximum."""
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10
    assert clamp(0.0, 0.0, 10.0) == 0.0
    assert clamp(10.0, 0.0, 10.0) == 10.0

def test_safe_divide_normal():
    """Test safe_divide with normal division."""
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(5.0, 2.0) == 2.5
    assert safe_divide(-10, 2) == -5.0

def test_safe_divide_by_zero():
    """Test safe_divide when dividing by zero."""
    assert safe_divide(10, 0) == 0.0
    assert safe_divide(5.0, 0.0) == 0.0
    assert safe_divide(-10, 0) == 0.0

def test_safe_divide_custom_default():
    """Test safe_divide with a custom default value."""
    assert safe_divide(10, 0, default=None) is None
    assert safe_divide(10, 0, default=-1.0) == -1.0
    assert safe_divide(10, 0, default=float('inf')) == float('inf')

def test_safe_divide_numerator_zero():
    """Test safe_divide when numerator is zero."""
    assert safe_divide(0, 5) == 0.0
    assert safe_divide(0.0, 5.0) == 0.0
