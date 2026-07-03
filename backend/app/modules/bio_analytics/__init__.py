"""Bio-analytics package.

Keep package initialization side-effect free so ORM models can be imported from
their canonical module path without triggering circular imports during CLI setup.
"""

__all__: list[str] = []
