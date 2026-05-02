"""Utility mathematical helpers for agronomic analysis services."""

from __future__ import annotations


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a value to a closed range."""
    return max(minimum, min(value, maximum))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers and return ``default`` when denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator
