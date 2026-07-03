"""
Research Domain Router Aggregator
Composes all research-related routers into a single mountable router
"""

from fastapi import APIRouter

from app.api.bijmantra.research import (
    cost_analysis,
    economics,
    impact,
    insights,
    ontology,
    proposals,
    reports,
    search,
    yield_gap,
)

research_router = APIRouter()

# Research domain routers
research_router.include_router(cost_analysis.router, tags=["Cost Analysis"])
research_router.include_router(economics.router, tags=["Economics"])
research_router.include_router(impact.router, tags=["Impact"])
research_router.include_router(insights.router, tags=["AI Insights"])
research_router.include_router(ontology.router, tags=["Trait Ontology"])
research_router.include_router(proposals.router, tags=["Proposals"])
research_router.include_router(reports.router, tags=["Reports"])
research_router.include_router(search.router, tags=["Search"])
research_router.include_router(yield_gap.router, tags=["Yield Gap Analysis"])
