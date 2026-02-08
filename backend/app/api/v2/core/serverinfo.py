"""
BrAPI Core - Server Info endpoint
GET /serverinfo - Returns information about the server
"""

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class ServerInfoCall(BaseModel):
    """Individual call/endpoint information"""
    contentTypes: List[str] = ["application/json"]
    dataTypes: List[str] = []
    methods: List[str]
    service: str
    versions: List[str] = ["2.1"]


class ServerInfo(BaseModel):
    """Server information response"""
    contactEmail: Optional[str] = "support@bijmantra.org"
    documentationURL: Optional[str] = "https://bijmantra.org/docs"
    location: Optional[str] = "India"
    organizationName: Optional[str] = "Bijmantra"
    organizationURL: Optional[str] = "https://bijmantra.org"
    serverDescription: Optional[str] = "Bijmantra - Plant Breeding Platform powered by Parashakti Framework"
    serverName: Optional[str] = "Bijmantra BrAPI Server"
    calls: List[ServerInfoCall] = []


# Define all implemented BrAPI calls
BRAPI_CALLS = [
    # Core
    ServerInfoCall(service="serverinfo", methods=["GET"]),
    ServerInfoCall(service="commoncropnames", methods=["GET"]),
    ServerInfoCall(service="programs", methods=["GET", "POST"]),
    ServerInfoCall(service="programs/{programDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="locations", methods=["GET", "POST"]),
    ServerInfoCall(service="locations/{locationDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="trials", methods=["GET", "POST"]),
    ServerInfoCall(service="trials/{trialDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="studies", methods=["GET", "POST"]),
    ServerInfoCall(service="studies/{studyDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="studytypes", methods=["GET"]),
    ServerInfoCall(service="seasons", methods=["GET", "POST"]),
    ServerInfoCall(service="seasons/{seasonDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="people", methods=["GET", "POST"]),
    ServerInfoCall(service="people/{personDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="lists", methods=["GET", "POST"]),
    ServerInfoCall(service="lists/{listDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="lists/{listDbId}/items", methods=["POST"]),
    ServerInfoCall(service="pedigree", methods=["GET", "POST", "PUT"]),
    # Germplasm
    ServerInfoCall(service="germplasm", methods=["GET", "POST"]),
    ServerInfoCall(service="germplasm/{germplasmDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="germplasm/{germplasmDbId}/pedigree", methods=["GET"]),
    ServerInfoCall(service="germplasm/{germplasmDbId}/progeny", methods=["GET"]),
    ServerInfoCall(service="germplasm/{germplasmDbId}/mcpd", methods=["GET"]),
    ServerInfoCall(service="attributes", methods=["GET", "POST"]),
    ServerInfoCall(service="attributes/{attributeDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="attributes/categories", methods=["GET"]),
    ServerInfoCall(service="attributevalues", methods=["GET", "POST"]),
    ServerInfoCall(service="attributevalues/{attributeValueDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="breedingmethods", methods=["GET"]),
    ServerInfoCall(service="breedingmethods/{breedingMethodDbId}", methods=["GET"]),
    ServerInfoCall(service="crosses", methods=["GET", "POST", "PUT"]),
    ServerInfoCall(service="crossingprojects", methods=["GET", "POST"]),
    ServerInfoCall(service="crossingprojects/{crossingProjectDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="plannedcrosses", methods=["GET", "POST", "PUT"]),
    ServerInfoCall(service="seedlots", methods=["GET", "POST"]),
    ServerInfoCall(service="seedlots/{seedLotDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="seedlots/transactions", methods=["GET", "POST"]),
    ServerInfoCall(service="seedlots/{seedLotDbId}/transactions", methods=["GET"]),
    # Phenotyping
    ServerInfoCall(service="observations", methods=["GET", "POST", "PUT"]),
    ServerInfoCall(service="observations/{observationDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="observations/table", methods=["GET"]),
    ServerInfoCall(service="observationunits", methods=["GET", "POST", "PUT"]),
    ServerInfoCall(service="observationunits/{observationUnitDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="observationunits/table", methods=["GET"]),
    ServerInfoCall(service="observationlevels", methods=["GET"]),
    ServerInfoCall(service="variables", methods=["GET", "POST"]),
    ServerInfoCall(service="variables/{observationVariableDbId}", methods=["GET", "PUT", "DELETE"]),
    ServerInfoCall(service="traits", methods=["GET", "POST"]),
    ServerInfoCall(service="traits/{traitDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="methods", methods=["GET", "POST"]),
    ServerInfoCall(service="methods/{methodDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="scales", methods=["GET", "POST"]),
    ServerInfoCall(service="scales/{scaleDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="ontologies", methods=["GET", "POST"]),
    ServerInfoCall(service="ontologies/{ontologyDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="events", methods=["GET", "POST"]),
    ServerInfoCall(service="images", methods=["GET", "POST"]),
    ServerInfoCall(service="images/{imageDbId}", methods=["GET", "PUT"]),
    # Genotyping
    ServerInfoCall(service="samples", methods=["GET", "POST", "PUT"]),
    ServerInfoCall(service="samples/{sampleDbId}", methods=["GET", "PUT"]),
    ServerInfoCall(service="plates", methods=["GET", "POST", "PUT"]),
    ServerInfoCall(service="plates/{plateDbId}", methods=["GET"]),
    ServerInfoCall(service="calls", methods=["GET", "PUT"]),
    ServerInfoCall(service="callsets", methods=["GET"]),
    ServerInfoCall(service="callsets/{callSetDbId}", methods=["GET"]),
    ServerInfoCall(service="callsets/{callSetDbId}/calls", methods=["GET"]),
    ServerInfoCall(service="variants", methods=["GET"]),
    ServerInfoCall(service="variants/{variantDbId}", methods=["GET"]),
    ServerInfoCall(service="variants/{variantDbId}/calls", methods=["GET"]),
    ServerInfoCall(service="variantsets", methods=["GET"]),
    ServerInfoCall(service="variantsets/{variantSetDbId}", methods=["GET"]),
    ServerInfoCall(service="variantsets/{variantSetDbId}/calls", methods=["GET"]),
    ServerInfoCall(service="variantsets/{variantSetDbId}/callsets", methods=["GET"]),
    ServerInfoCall(service="variantsets/{variantSetDbId}/variants", methods=["GET"]),
    ServerInfoCall(service="variantsets/extract", methods=["POST"]),
    ServerInfoCall(service="allelematrix", methods=["GET"]),
    ServerInfoCall(service="references", methods=["GET"]),
    ServerInfoCall(service="references/{referenceDbId}", methods=["GET"]),
    ServerInfoCall(service="references/{referenceDbId}/bases", methods=["GET"]),
    ServerInfoCall(service="referencesets", methods=["GET"]),
    ServerInfoCall(service="referencesets/{referenceSetDbId}", methods=["GET"]),
    ServerInfoCall(service="maps", methods=["GET"]),
    ServerInfoCall(service="maps/{mapDbId}", methods=["GET"]),
    ServerInfoCall(service="maps/{mapDbId}/linkagegroups", methods=["GET"]),
    ServerInfoCall(service="markerpositions", methods=["GET"]),
    # Search endpoints
    ServerInfoCall(service="search/programs", methods=["POST"]),
    ServerInfoCall(service="search/studies", methods=["POST"]),
    ServerInfoCall(service="search/trials", methods=["POST"]),
    ServerInfoCall(service="search/locations", methods=["POST"]),
    ServerInfoCall(service="search/germplasm", methods=["POST"]),
    ServerInfoCall(service="search/observations", methods=["POST"]),
    ServerInfoCall(service="search/observationunits", methods=["POST"]),
    ServerInfoCall(service="search/variables", methods=["POST"]),
    ServerInfoCall(service="search/samples", methods=["POST"]),
    ServerInfoCall(service="search/variants", methods=["POST"]),
    ServerInfoCall(service="search/variantsets", methods=["POST"]),
    ServerInfoCall(service="search/calls", methods=["POST"]),
    ServerInfoCall(service="search/callsets", methods=["POST"]),
]


@router.get("/serverinfo")
async def get_server_info():
    """
    Get information about this BrAPI server
    
    BrAPI Endpoint: GET /serverinfo
    """
    server_info = ServerInfo(calls=BRAPI_CALLS)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": 0,
                "pageSize": 1,
                "totalCount": 1,
                "totalPages": 1
            },
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": server_info.model_dump()
    }
