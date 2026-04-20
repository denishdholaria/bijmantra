"""
Bijmantra Function Schemas for FunctionGemma

Defines all available functions that Veena can execute.
These are the "tools" that FunctionGemma can call.

Format follows OpenAI function calling schema for compatibility.
"""

from typing import Any


FUNCTION_CATEGORY_METADATA: dict[str, dict[str, str]] = {
    "germplasm_breeding": {
        "label": "Germplasm & Breeding",
        "description": "Search, compare, and plan core breeding work across germplasm and crossing data.",
    },
    "trial_management": {
        "label": "Trial Management & Planning",
        "description": "Inspect trial results, create trial plans, and retrieve field observations.",
    },
    "phenotyping_analytics": {
        "label": "Phenotyping & Analytics",
        "description": "Run scientific analysis functions used for trait interpretation and performance ranking.",
    },
    "genomics_analytics": {
        "label": "Genomics & Marker Analytics",
        "description": "Inspect marker-trait associations, QTL findings, and genomics-backed decision support surfaces.",
    },
    "cross_domain_intelligence": {
        "label": "Cross-Domain Intelligence",
        "description": "Join breeding, trial, and environment evidence into an explicit multi-domain retrieval plan.",
    },
    "environment_operations": {
        "label": "Environment & Field Operations",
        "description": "Access weather, seed viability, and other operational field support tools.",
    },
    "data_navigation": {
        "label": "Data & Navigation Utilities",
        "description": "Export data and navigate to related application surfaces when needed.",
    },
}


FUNCTION_LABELS: dict[str, str] = {
    "search_germplasm": "Search Germplasm",
    "get_germplasm_details": "Get Germplasm Details",
    "compare_germplasm": "Compare Germplasm",
    "get_trait_summary": "Get Trait Summary",
    "get_marker_associations": "Get Marker Associations",
    "cross_domain_query": "Run Cross-Domain Query",
    "search_trials": "Search Trials",
    "get_trial_results": "Get Trial Results",
    "propose_create_trial": "Create Trial Proposal",
    "search_crosses": "Search Crosses",
    "predict_cross": "Predict Cross Outcome",
    "propose_create_cross": "Create Cross Proposal",
    "propose_record_observation": "Record Observation Proposal",
    "get_observations": "Get Observations",
    "calculate_breeding_value": "Calculate Breeding Value",
    "analyze_gxe": "Analyze GxE",
    "calculate_genetic_diversity": "Calculate Genetic Diversity",
    "search_accessions": "Search Accessions",
    "check_seed_viability": "Check Seed Viability",
    "get_weather_forecast": "Get Weather Forecast",
    "export_data": "Export Data",
    "navigate_to": "Navigate To",
}


FUNCTION_CATEGORY_BY_NAME: dict[str, str] = {
    "search_germplasm": "germplasm_breeding",
    "get_germplasm_details": "germplasm_breeding",
    "compare_germplasm": "germplasm_breeding",
    "get_trait_summary": "phenotyping_analytics",
    "get_marker_associations": "genomics_analytics",
    "cross_domain_query": "cross_domain_intelligence",
    "search_crosses": "germplasm_breeding",
    "predict_cross": "germplasm_breeding",
    "propose_create_cross": "germplasm_breeding",
    "search_trials": "trial_management",
    "get_trial_results": "trial_management",
    "propose_create_trial": "trial_management",
    "propose_record_observation": "trial_management",
    "get_observations": "trial_management",
    "calculate_breeding_value": "phenotyping_analytics",
    "analyze_gxe": "phenotyping_analytics",
    "calculate_genetic_diversity": "phenotyping_analytics",
    "search_accessions": "environment_operations",
    "check_seed_viability": "environment_operations",
    "get_weather_forecast": "environment_operations",
    "export_data": "data_navigation",
    "navigate_to": "data_navigation",
}


# ============================================
# FUNCTION SCHEMAS
# ============================================

BIJMANTRA_FUNCTIONS: list[dict[str, Any]] = [
    # ========== GERMPLASM ==========
    {
        "name": "search_germplasm",
        "description": "Search for germplasm entries by crop, trait, name, or origin. Returns matching varieties with their characteristics.",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {
                    "type": "string",
                    "description": "Crop name (e.g., rice, wheat, maize)",
                },
                "trait": {
                    "type": "string",
                    "description": "Trait to search for (e.g., blast_resistance, drought_tolerance)",
                },
                "name": {
                    "type": "string",
                    "description": "Germplasm name or accession number",
                },
                "origin": {
                    "type": "string",
                    "description": "Country or region of origin",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 20)",
                    "default": 20,
                },
            },
        },
    },
    {
        "name": "get_germplasm_details",
        "description": (
            "Get detailed information about a specific germplasm entry including traits, pedigree, "
            "and performance data. Accepts an exact germplasm ID or resolves one authoritative match "
            "from a query, accession, or name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "germplasm_id": {
                    "type": "string",
                    "description": "Germplasm ID or accession number",
                },
                "query": {
                    "type": "string",
                    "description": "Free-form germplasm lookup phrase when the exact ID is unknown",
                },
                "accession": {
                    "type": "string",
                    "description": "Accession number or concise accession-like lookup value",
                },
                "name": {
                    "type": "string",
                    "description": "Germplasm display name when resolving one authoritative record",
                },
            },
        },
    },
    {
        "name": "compare_germplasm",
        "description": "Compare multiple germplasm entries side-by-side for specified traits.",
        "parameters": {
            "type": "object",
            "properties": {
                "germplasm_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of germplasm IDs to compare (2-5 entries)",
                },
                "traits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Traits to compare (e.g., yield, disease_resistance)",
                },
            },
            "required": ["germplasm_ids"],
        },
    },
    {
        "name": "get_trait_summary",
        "description": (
            "Get phenotype trait summary statistics for selected germplasm entries or the "
            "current comparison scope."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "germplasm_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of germplasm IDs or accessions to summarize",
                },
            },
        },
    },
    {
        "name": "get_marker_associations",
        "description": (
            "Retrieve genomics marker associations, GWAS hits, and QTL records for a trait "
            "or marker-association question."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "trait": {
                    "type": "string",
                    "description": "Trait name to resolve against available QTL/GWAS traits",
                },
                "query": {
                    "type": "string",
                    "description": "Free-form marker-association request when the exact trait is not isolated",
                },
                "chromosome": {
                    "type": "string",
                    "description": "Optional chromosome filter for marker associations",
                },
            },
        },
    },
    {
        "name": "cross_domain_query",
        "description": (
            "Join breeding, trials, and environment evidence for compound questions that require "
            "more than one agricultural domain."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Original compound question to plan and audit",
                },
                "crop": {
                    "type": "string",
                    "description": "Optional crop filter for breeding and trial retrieval",
                },
                "trait": {
                    "type": "string",
                    "description": "Optional trait filter for breeding retrieval",
                },
                "location": {
                    "type": "string",
                    "description": "Optional location or station name for trial/environment retrieval",
                },
                "germplasm": {
                    "type": "string",
                    "description": "Optional germplasm query anchor when the compound request names a variety/accession",
                },
            },
        },
    },

    # ========== TRIALS ==========
    {
        "name": "search_trials",
        "description": "Search for breeding trials by crop, location, year, or trial type.",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {
                    "type": "string",
                    "description": "Crop name",
                },
                "location": {
                    "type": "string",
                    "description": "Trial location or station name",
                },
                "year": {
                    "type": "integer",
                    "description": "Trial year",
                },
                "trial_type": {
                    "type": "string",
                    "description": "Trial type (e.g., PYT, AYT, MLT)",
                },
                "status": {
                    "type": "string",
                    "description": "Trial status (active, completed, planned)",
                },
            },
        },
    },
    {
        "name": "get_trial_results",
        "description": (
            "Get results and performance data from a specific trial, or resolve one from a "
            "query plus optional crop/location filters."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "trial_id": {
                    "type": "string",
                    "description": "Trial ID",
                },
                "query": {
                    "type": "string",
                    "description": "Trial name or concise lookup phrase when the exact trial ID is unknown",
                },
                "crop": {
                    "type": "string",
                    "description": "Optional crop filter to narrow trial resolution",
                },
                "location": {
                    "type": "string",
                    "description": "Optional location filter to narrow trial resolution",
                },
                "season": {
                    "type": "string",
                    "description": "Optional season label when the request specifies current or named season",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Sort results by trait (e.g., yield, height)",
                },
            },
        },
    },
    {
        "name": "propose_create_trial",
        "description": "Propose a new breeding trial. Creates a draft proposal for review.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Trial name",
                },
                "crop": {
                    "type": "string",
                    "description": "Crop name",
                },
                "location": {
                    "type": "string",
                    "description": "Trial location",
                },
                "trial_type": {
                    "type": "string",
                    "description": "Trial type (OYT, PYT, AYT, MLT)",
                },
                "design": {
                    "type": "string",
                    "description": "Experimental design (RCBD, Alpha-Lattice, Augmented)",
                },
                "entries": {
                    "type": "integer",
                    "description": "Number of entries",
                },
                "rationale": {
                    "type": "string",
                    "description": "Reason for this proposal",
                },
            },
            "required": ["name", "crop", "location", "trial_type"],
        },
    },

    # ========== CROSSES ==========
    {
        "name": "search_crosses",
        "description": "Search for crosses by parent names, crop, or crossing year.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent1": {
                    "type": "string",
                    "description": "Female parent name",
                },
                "parent2": {
                    "type": "string",
                    "description": "Male parent name",
                },
                "crop": {
                    "type": "string",
                    "description": "Crop name",
                },
                "year": {
                    "type": "integer",
                    "description": "Crossing year",
                },
            },
        },
    },
    {
        "name": "predict_cross",
        "description": "Predict the outcome of a cross between two parents including expected GEBV, heterosis, and genetic distance.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent1_id": {
                    "type": "string",
                    "description": "Female parent germplasm ID",
                },
                "parent2_id": {
                    "type": "string",
                    "description": "Male parent germplasm ID",
                },
                "traits": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Traits to predict",
                },
            },
            "required": ["parent1_id", "parent2_id"],
        },
    },
    {
        "name": "propose_create_cross",
        "description": "Propose a new cross between two parents. Creates a draft proposal.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent1_id": {
                    "type": "string",
                    "description": "Female parent ID",
                },
                "parent2_id": {
                    "type": "string",
                    "description": "Male parent ID",
                },
                "crossing_date": {
                    "type": "string",
                    "description": "Date of crossing (YYYY-MM-DD)",
                },
                "seeds_obtained": {
                    "type": "integer",
                    "description": "Number of seeds obtained",
                },
                "rationale": {
                    "type": "string",
                    "description": "Reason for this proposal",
                },
            },
            "required": ["parent1_id", "parent2_id"],
        },
    },

    # ========== OBSERVATIONS ==========
    {
        "name": "propose_record_observation",
        "description": "Propose recording a phenotypic observation. Creates a draft proposal.",
        "parameters": {
            "type": "object",
            "properties": {
                "trial_id": {
                    "type": "string",
                    "description": "Trial ID",
                },
                "plot_id": {
                    "type": "string",
                    "description": "Plot ID",
                },
                "trait": {
                    "type": "string",
                    "description": "Trait name (e.g., plant_height, yield)",
                },
                "value": {
                    "type": "number",
                    "description": "Observed value",
                },
                "date": {
                    "type": "string",
                    "description": "Observation date (YYYY-MM-DD)",
                },
                "rationale": {
                    "type": "string",
                    "description": "Reason for this proposal",
                },
            },
            "required": ["trial_id", "plot_id", "trait", "value"],
        },
    },
    {
        "name": "get_observations",
        "description": "Get observations for a trial, plot, or trait.",
        "parameters": {
            "type": "object",
            "properties": {
                "trial_id": {
                    "type": "string",
                    "description": "Trial ID",
                },
                "trait": {
                    "type": "string",
                    "description": "Trait name",
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)",
                },
            },
        },
    },

    # ========== ANALYSIS ==========
    {
        "name": "calculate_breeding_value",
        "description": (
            "Calculate deterministic BLUP or GBLUP breeding values. BLUP can run from database-backed "
            "trait observations when germplasm_ids are omitted; GBLUP requires matrix-backed inputs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "germplasm_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of germplasm IDs to scope or label the breeding-value output",
                },
                "trait": {
                    "type": "string",
                    "description": "Trait to calculate breeding value for",
                },
                "crop": {
                    "type": "string",
                    "description": "Optional crop filter when resolving database-backed BLUP or GBLUP inputs",
                },
                "method": {
                    "type": "string",
                    "description": "Method: BLUP or GBLUP",
                    "enum": ["BLUP", "GBLUP"],
                },
                "heritability": {
                    "type": "number",
                    "description": "Optional heritability estimate for BLUP/GBLUP calculations",
                },
                "phenotypes": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Optional phenotype vector for deterministic matrix-backed GBLUP",
                },
                "genotype_matrix": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "Optional genotype matrix (n individuals × m markers) for deterministic GBLUP",
                },
                "g_matrix": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "description": "Optional precomputed genomic relationship matrix for deterministic GBLUP",
                },
                "study_id": {
                    "type": "string",
                    "description": "Optional study identifier to scope database-backed BLUP retrieval",
                },
            },
            "required": ["trait"],
        },
    },
    {
        "name": "analyze_gxe",
        "description": "Perform genotype × environment interaction analysis using AMMI or GGE biplot.",
        "parameters": {
            "type": "object",
            "properties": {
                "trial_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of trial IDs (multi-environment)",
                },
                "trait": {
                    "type": "string",
                    "description": "Trait to analyze",
                },
                "method": {
                    "type": "string",
                    "description": "Analysis method",
                    "enum": ["AMMI", "GGE"],
                },
            },
            "required": ["trial_ids", "trait"],
        },
    },
    {
        "name": "calculate_genetic_diversity",
        "description": "Calculate genetic diversity metrics for a population.",
        "parameters": {
            "type": "object",
            "properties": {
                "germplasm_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of germplasm IDs",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Metrics to calculate (shannon, simpson, heterozygosity)",
                },
            },
            "required": ["germplasm_ids"],
        },
    },

    # ========== SEED BANK ==========
    {
        "name": "search_accessions",
        "description": "Search seed bank accessions by crop, origin, or collection date.",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {
                    "type": "string",
                    "description": "Crop name",
                },
                "origin": {
                    "type": "string",
                    "description": "Country of origin",
                },
                "collection_year": {
                    "type": "integer",
                    "description": "Year of collection",
                },
                "vault": {
                    "type": "string",
                    "description": "Vault name",
                },
            },
        },
    },
    {
        "name": "check_seed_viability",
        "description": "Get viability test results for a seed lot or accession.",
        "parameters": {
            "type": "object",
            "properties": {
                "accession_id": {
                    "type": "string",
                    "description": "Accession ID",
                },
            },
            "required": ["accession_id"],
        },
    },

    # ========== WEATHER & ENVIRONMENT ==========
    {
        "name": "get_weather_forecast",
        "description": "Get weather forecast for a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location name or coordinates",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days (1-14)",
                    "default": 7,
                },
            },
            "required": ["location"],
        },
    },

    # ========== REPORTS & EXPORT ==========
    {
        "name": "export_data",
        "description": "Export data to CSV, Excel, or JSON format.",
        "parameters": {
            "type": "object",
            "properties": {
                "data_type": {
                    "type": "string",
                    "description": "Type of data to export",
                    "enum": ["germplasm", "trials", "observations", "crosses"],
                },
                "format": {
                    "type": "string",
                    "description": "Export format",
                    "enum": ["CSV", "XLSX", "JSON"],
                },
                "filters": {
                    "type": "object",
                    "description": "Filters to apply (crop, year, etc.)",
                },
            },
            "required": ["data_type", "format"],
        },
    },

    # ========== NAVIGATION ==========
    {
        "name": "navigate_to",
        "description": "Navigate to a specific page in the application.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "description": "Page name or route (e.g., /programs, /trials, /germplasm)",
                },
                "filters": {
                    "type": "object",
                    "description": "URL query parameters",
                },
            },
            "required": ["page"],
        },
    },
]


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_function_by_name(name: str, functions: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Get function schema by name"""
    for func in functions or BIJMANTRA_FUNCTIONS:
        if func["name"] == name:
            return func
    return None


def get_all_function_names(functions: list[dict[str, Any]] | None = None) -> list[str]:
    """Get list of all available function names"""
    return [func["name"] for func in functions or BIJMANTRA_FUNCTIONS]


def format_functions_for_prompt(functions: list[dict[str, Any]] | None = None) -> str:
    """Format functions as text for LLM prompt"""
    lines = ["Available functions:"]
    for func in functions or BIJMANTRA_FUNCTIONS:
        params = func["parameters"]["properties"].keys()
        lines.append(f"- {func['name']}({', '.join(params)}): {func['description']}")
    return "\n".join(lines)


def get_function_manifest(functions: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        category_id: [] for category_id in FUNCTION_CATEGORY_METADATA
    }

    for function in functions or BIJMANTRA_FUNCTIONS:
        function_name = function["name"]
        category_id = FUNCTION_CATEGORY_BY_NAME.get(function_name, "data_navigation")
        grouped.setdefault(category_id, []).append(
            {
                "name": function_name,
                "label": FUNCTION_LABELS.get(function_name, function_name.replace("_", " ").title()),
                "description": function["description"],
            }
        )

    manifest: list[dict[str, Any]] = []
    for category_id, metadata in FUNCTION_CATEGORY_METADATA.items():
        manifest.append(
            {
                "id": category_id,
                "label": metadata["label"],
                "description": metadata["description"],
                "tools": grouped.get(category_id, []),
            }
        )

    return manifest
