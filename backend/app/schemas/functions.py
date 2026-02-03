"""
Bijmantra Function Schemas for FunctionGemma

Defines all available functions that Veena can execute.
These are the "tools" that FunctionGemma can call.

Format follows OpenAI function calling schema for compatibility.
"""

from typing import List, Dict, Any

# ============================================
# FUNCTION SCHEMAS
# ============================================

BIJMANTRA_FUNCTIONS: List[Dict[str, Any]] = [
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
        "description": "Get detailed information about a specific germplasm entry including traits, pedigree, and performance data.",
        "parameters": {
            "type": "object",
            "properties": {
                "germplasm_id": {
                    "type": "string",
                    "description": "Germplasm ID or accession number",
                },
            },
            "required": ["germplasm_id"],
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
        "description": "Get results and performance data from a specific trial.",
        "parameters": {
            "type": "object",
            "properties": {
                "trial_id": {
                    "type": "string",
                    "description": "Trial ID",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Sort results by trait (e.g., yield, height)",
                },
            },
            "required": ["trial_id"],
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
        "description": "Calculate BLUP or GEBV for germplasm entries.",
        "parameters": {
            "type": "object",
            "properties": {
                "germplasm_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of germplasm IDs",
                },
                "trait": {
                    "type": "string",
                    "description": "Trait to calculate breeding value for",
                },
                "method": {
                    "type": "string",
                    "description": "Method: BLUP or GBLUP",
                    "enum": ["BLUP", "GBLUP"],
                },
            },
            "required": ["germplasm_ids", "trait"],
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
    {
        "name": "calculate_gdd",
        "description": "Calculate Growing Degree Days for a location and date range.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location name",
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date (YYYY-MM-DD)",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date (YYYY-MM-DD)",
                },
                "base_temp": {
                    "type": "number",
                    "description": "Base temperature (°C)",
                    "default": 10,
                },
            },
            "required": ["location", "date_from", "date_to"],
        },
    },
    
    # ========== REPORTS & EXPORT ==========
    {
        "name": "generate_trial_report",
        "description": "Generate a comprehensive trial report with statistics and visualizations.",
        "parameters": {
            "type": "object",
            "properties": {
                "trial_id": {
                    "type": "string",
                    "description": "Trial ID",
                },
                "format": {
                    "type": "string",
                    "description": "Report format",
                    "enum": ["PDF", "DOCX", "HTML"],
                    "default": "PDF",
                },
                "include_plots": {
                    "type": "boolean",
                    "description": "Include plots and charts",
                    "default": True,
                },
            },
            "required": ["trial_id"],
        },
    },
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

def get_function_by_name(name: str) -> Dict[str, Any] | None:
    """Get function schema by name"""
    for func in BIJMANTRA_FUNCTIONS:
        if func["name"] == name:
            return func
    return None


def get_all_function_names() -> List[str]:
    """Get list of all available function names"""
    return [func["name"] for func in BIJMANTRA_FUNCTIONS]


def format_functions_for_prompt() -> str:
    """Format functions as text for LLM prompt"""
    lines = ["Available functions:"]
    for func in BIJMANTRA_FUNCTIONS:
        params = func["parameters"]["properties"].keys()
        lines.append(f"- {func['name']}({', '.join(params)}): {func['description']}")
    return "\n".join(lines)
