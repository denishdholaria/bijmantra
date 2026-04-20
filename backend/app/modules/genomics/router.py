"""
Genomics Domain API Router

Consolidates all genomics-related endpoints under /api/v2/genomics/*
Migrated from flat api/v2/ structure to domain-based organization.

Endpoints organized by subdomain:
- GWAS (Genome-Wide Association Studies)
- Genomic Selection (GBLUP, GEBV prediction)
- QTL Mapping (QTL detection, candidate genes)
- Haplotype Analysis (haplotype blocks, associations)
- Linkage Disequilibrium (LD calculation, decay, pruning)
- Marker-Assisted Selection (MAS, MABC)
- Molecular Breeding (introgression, gene pyramiding)
- Parentage Analysis (DNA-based verification)
- Population Genetics (structure, PCA, Fst)
- Genotyping (BrAPI-compliant variant data)
"""

from fastapi import APIRouter

# Import all genomics-related routers
from app.api.v2 import (
    gwas,
    genomic_selection,
    qtl_mapping,
    haplotype,
    ld,
    mas,
    molecular_breeding,
    parentage,
    population_genetics,
    genotyping,
)

# Create main genomics router with /api/v2 prefix
# Individual routers will be included with their own prefixes
router = APIRouter(prefix="/api/v2", tags=["Genomics"])

# Include all genomics sub-routers
# These maintain their original prefixes for backward compatibility
router.include_router(gwas.router, tags=["GWAS"])
router.include_router(genomic_selection.router, tags=["Genomic Selection"])
router.include_router(qtl_mapping.router, tags=["QTL Mapping"])
router.include_router(haplotype.router, tags=["Haplotype Analysis"])
router.include_router(ld.router, tags=["Linkage Disequilibrium"])
router.include_router(mas.router, tags=["Marker-Assisted Selection"])
router.include_router(molecular_breeding.router, tags=["Molecular Breeding"])
router.include_router(parentage.router, tags=["Parentage Analysis"])
router.include_router(population_genetics.router, tags=["Population Genetics"])
router.include_router(genotyping.router, tags=["BrAPI Genotyping"])
