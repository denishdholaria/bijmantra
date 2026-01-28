"""
Data Dictionary API
Endpoints for data schema documentation and field definitions
"""

from fastapi import APIRouter, Query
from typing import Optional, List

router = APIRouter(prefix="/data-dictionary", tags=["Data Dictionary"])

# BrAPI-compliant entity definitions
ENTITIES = {
    "germplasm": {
        "name": "Germplasm",
        "description": "Genetic material used in breeding programs",
        "brapi_module": "Germplasm",
        "fields": [
            {"name": "germplasmDbId", "type": "string", "description": "Unique identifier for germplasm", "required": True, "example": "GERM001", "brapi_field": "germplasmDbId"},
            {"name": "germplasmName", "type": "string", "description": "Human readable name", "required": True, "example": "IR64", "brapi_field": "germplasmName"},
            {"name": "accessionNumber", "type": "string", "description": "Accession number from genebank", "required": False, "example": "ACC-2024-001", "brapi_field": "accessionNumber"},
            {"name": "pedigree", "type": "string", "description": "Pedigree string", "required": False, "example": "IR5657/IR2061", "brapi_field": "pedigree"},
            {"name": "seedSource", "type": "string", "description": "Source of seed material", "required": False, "example": "IRRI Genebank", "brapi_field": "seedSource"},
            {"name": "biologicalStatusOfAccessionCode", "type": "integer", "description": "MCPD biological status code", "required": False, "example": "300", "brapi_field": "biologicalStatusOfAccessionCode"},
            {"name": "countryOfOriginCode", "type": "string", "description": "ISO 3166-1 alpha-3 country code", "required": False, "example": "PHL", "brapi_field": "countryOfOriginCode"},
            {"name": "genus", "type": "string", "description": "Genus name", "required": False, "example": "Oryza", "brapi_field": "genus"},
            {"name": "species", "type": "string", "description": "Species name", "required": False, "example": "sativa", "brapi_field": "species"},
        ],
        "relationships": ["Crosses", "Observations", "SeedLots", "Pedigree", "Progeny"]
    },
    "trial": {
        "name": "Trial",
        "description": "A breeding trial or experiment",
        "brapi_module": "Core",
        "fields": [
            {"name": "trialDbId", "type": "string", "description": "Unique identifier for trial", "required": True, "example": "TRIAL001", "brapi_field": "trialDbId"},
            {"name": "trialName", "type": "string", "description": "Human readable name", "required": True, "example": "Yield Trial 2024", "brapi_field": "trialName"},
            {"name": "programDbId", "type": "string", "description": "Associated breeding program", "required": False, "example": "PROG001", "brapi_field": "programDbId"},
            {"name": "startDate", "type": "date", "description": "Trial start date", "required": False, "example": "2024-01-15", "brapi_field": "startDate"},
            {"name": "endDate", "type": "date", "description": "Trial end date", "required": False, "example": "2024-06-30", "brapi_field": "endDate"},
            {"name": "active", "type": "boolean", "description": "Whether trial is active", "required": False, "example": "true", "brapi_field": "active"},
        ],
        "relationships": ["Studies", "Programs", "Contacts"]
    },
    "study": {
        "name": "Study",
        "description": "A specific study within a trial",
        "brapi_module": "Core",
        "fields": [
            {"name": "studyDbId", "type": "string", "description": "Unique identifier", "required": True, "example": "STUDY001", "brapi_field": "studyDbId"},
            {"name": "studyName", "type": "string", "description": "Human readable name", "required": True, "example": "Yield Study 2024-A", "brapi_field": "studyName"},
            {"name": "trialDbId", "type": "string", "description": "Parent trial", "required": False, "example": "TRIAL001", "brapi_field": "trialDbId"},
            {"name": "locationDbId", "type": "string", "description": "Study location", "required": False, "example": "LOC001", "brapi_field": "locationDbId"},
            {"name": "startDate", "type": "date", "description": "Study start date", "required": False, "example": "2024-02-01", "brapi_field": "startDate"},
            {"name": "studyType", "type": "string", "description": "Type of study", "required": False, "example": "Yield Trial", "brapi_field": "studyType"},
        ],
        "relationships": ["Trials", "Locations", "ObservationUnits", "Observations"]
    },
    "observation": {
        "name": "Observation",
        "description": "A single data point measurement",
        "brapi_module": "Phenotyping",
        "fields": [
            {"name": "observationDbId", "type": "string", "description": "Unique identifier", "required": True, "example": "OBS001", "brapi_field": "observationDbId"},
            {"name": "observationUnitDbId", "type": "string", "description": "Associated observation unit", "required": True, "example": "OU001", "brapi_field": "observationUnitDbId"},
            {"name": "observationVariableDbId", "type": "string", "description": "Variable being measured", "required": True, "example": "VAR001", "brapi_field": "observationVariableDbId"},
            {"name": "value", "type": "string", "description": "Measured value", "required": True, "example": "5.2", "brapi_field": "value"},
            {"name": "observationTimeStamp", "type": "datetime", "description": "When observation was made", "required": False, "example": "2024-03-15T10:30:00Z", "brapi_field": "observationTimeStamp"},
            {"name": "collector", "type": "string", "description": "Person who collected data", "required": False, "example": "John Smith", "brapi_field": "collector"},
        ],
        "relationships": ["ObservationUnits", "ObservationVariables", "Studies"]
    },
    "observationunit": {
        "name": "ObservationUnit",
        "description": "A unit being observed (plot, plant, sample)",
        "brapi_module": "Phenotyping",
        "fields": [
            {"name": "observationUnitDbId", "type": "string", "description": "Unique identifier", "required": True, "example": "OU001", "brapi_field": "observationUnitDbId"},
            {"name": "observationUnitName", "type": "string", "description": "Human readable name", "required": False, "example": "Plot 1-A", "brapi_field": "observationUnitName"},
            {"name": "studyDbId", "type": "string", "description": "Parent study", "required": True, "example": "STUDY001", "brapi_field": "studyDbId"},
            {"name": "germplasmDbId", "type": "string", "description": "Germplasm in this unit", "required": False, "example": "GERM001", "brapi_field": "germplasmDbId"},
            {"name": "observationLevel", "type": "string", "description": "Level of observation", "required": False, "example": "plot", "brapi_field": "observationLevel"},
        ],
        "relationships": ["Studies", "Germplasm", "Observations"]
    },
    "variable": {
        "name": "ObservationVariable",
        "description": "A trait or variable being measured",
        "brapi_module": "Phenotyping",
        "fields": [
            {"name": "observationVariableDbId", "type": "string", "description": "Unique identifier", "required": True, "example": "VAR001", "brapi_field": "observationVariableDbId"},
            {"name": "observationVariableName", "type": "string", "description": "Human readable name", "required": True, "example": "Plant Height", "brapi_field": "observationVariableName"},
            {"name": "trait", "type": "object", "description": "Trait definition", "required": False, "example": "{name: 'Height'}", "brapi_field": "trait"},
            {"name": "method", "type": "object", "description": "Measurement method", "required": False, "example": "{name: 'Ruler'}", "brapi_field": "method"},
            {"name": "scale", "type": "object", "description": "Measurement scale", "required": False, "example": "{dataType: 'Numerical'}", "brapi_field": "scale"},
        ],
        "relationships": ["Observations", "Ontologies"]
    },
    "sample": {
        "name": "Sample",
        "description": "A biological sample for genotyping",
        "brapi_module": "Genotyping",
        "fields": [
            {"name": "sampleDbId", "type": "string", "description": "Unique identifier", "required": True, "example": "SAMP001", "brapi_field": "sampleDbId"},
            {"name": "sampleName", "type": "string", "description": "Human readable name", "required": False, "example": "Sample A1", "brapi_field": "sampleName"},
            {"name": "germplasmDbId", "type": "string", "description": "Source germplasm", "required": False, "example": "GERM001", "brapi_field": "germplasmDbId"},
            {"name": "tissueType", "type": "string", "description": "Type of tissue", "required": False, "example": "Leaf", "brapi_field": "tissueType"},
            {"name": "sampleTimestamp", "type": "datetime", "description": "When sample was taken", "required": False, "example": "2024-03-15T10:30:00Z", "brapi_field": "sampleTimestamp"},
        ],
        "relationships": ["Germplasm", "Plates", "CallSets"]
    },
}


@router.get("/entities")
async def get_entities():
    """Get all data entities"""
    entities_list = [
        {"id": key, "name": val["name"], "description": val["description"], "brapi_module": val["brapi_module"], "field_count": len(val["fields"]), "relationship_count": len(val["relationships"])}
        for key, val in ENTITIES.items()
    ]
    return {"status": "success", "data": entities_list, "count": len(entities_list)}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Get a specific entity with all fields"""
    if entity_id not in ENTITIES:
        return {"status": "error", "message": "Entity not found"}
    return {"status": "success", "data": {"id": entity_id, **ENTITIES[entity_id]}}


@router.get("/fields")
async def search_fields(search: Optional[str] = Query(None), entity: Optional[str] = Query(None)):
    """Search across all fields"""
    results = []
    for entity_id, entity_data in ENTITIES.items():
        if entity and entity_id != entity:
            continue
        for field in entity_data["fields"]:
            if search is None or search.lower() in field["name"].lower() or search.lower() in field["description"].lower():
                results.append({"entity": entity_id, "entity_name": entity_data["name"], **field})
    return {"status": "success", "data": results, "count": len(results)}


@router.get("/stats")
async def get_stats():
    """Get data dictionary statistics"""
    total_fields = sum(len(e["fields"]) for e in ENTITIES.values())
    total_relationships = sum(len(e["relationships"]) for e in ENTITIES.values())
    required_fields = sum(1 for e in ENTITIES.values() for f in e["fields"] if f["required"])
    
    return {
        "status": "success",
        "data": {
            "total_entities": len(ENTITIES),
            "total_fields": total_fields,
            "total_relationships": total_relationships,
            "required_fields": required_fields,
            "optional_fields": total_fields - required_fields,
            "brapi_version": "2.1",
            "modules": list(set(e["brapi_module"] for e in ENTITIES.values()))
        }
    }


@router.get("/export")
async def export_dictionary(format: str = Query("json")):
    """Export the complete data dictionary"""
    return {"status": "success", "data": ENTITIES, "format": format}
