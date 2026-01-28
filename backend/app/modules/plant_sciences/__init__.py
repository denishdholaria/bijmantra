"""
Plant Sciences Module

Division 1: Breeding operations, genomics, molecular biology, crop sciences.
This module contains all plant science related functionality.

Subsections:
- breeding: Programs, trials, studies, germplasm, crosses
- genomics: Genetic analysis, QTL, GWAS, selection
- phenotyping: Traits, observations, images
- genotyping: Samples, variants, markers
"""

from .router import router as plant_sciences_router

__all__ = ["plant_sciences_router"]
