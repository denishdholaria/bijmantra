"""
Genomics Domain Router Aggregator

Composes all genomics-related routers into a single mountable router.
"""

from fastapi import APIRouter

from app.api.bijmantra.genomics import (
    bioinformatics,
    genomic_selection,
    genotyping,
    gwas,
    gxe,
    haplotype,
    ld,
    mas,
    molecular_breeding,
    parentage,
    phenomic_selection,
    population_genetics,
    population_structure,
    qtl_mapping,
)

genomics_router = APIRouter()

# Genomic Selection and Prediction
genomics_router.include_router(genomic_selection.router, tags=["Genomic Selection"])
genomics_router.include_router(phenomic_selection.router, tags=["Phenomic Selection"])

# Genotyping and Markers
genomics_router.include_router(genotyping.router, tags=["BrAPI Genotyping"])
genomics_router.include_router(mas.router, tags=["Marker-Assisted Selection"])

# QTL and Association Mapping
genomics_router.include_router(qtl_mapping.router, tags=["QTL Mapping"])
genomics_router.include_router(gwas.router, tags=["GWAS"])
genomics_router.include_router(gxe.router, tags=["G×E Analysis"])

# Population Genetics
genomics_router.include_router(population_genetics.router, tags=["Population Genetics"])
genomics_router.include_router(population_structure.router, tags=["Population Structure"])
genomics_router.include_router(ld.router, tags=["Linkage Disequilibrium"])
genomics_router.include_router(haplotype.router, tags=["Haplotype Analysis"])

# Molecular Breeding
genomics_router.include_router(molecular_breeding.router, tags=["Molecular Breeding"])
genomics_router.include_router(parentage.router, tags=["Parentage Analysis"])

# Bioinformatics
genomics_router.include_router(bioinformatics.router, tags=["Bioinformatics"])
