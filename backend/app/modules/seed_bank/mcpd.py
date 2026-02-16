"""
MCPD (Multi-Crop Passport Descriptors) v2.1 Service

Provides import/export functionality for genebank data exchange
following the FAO/Bioversity MCPD standard.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
import csv
import io


# ============ MCPD Code Mappings ============

# Biological Status Codes (SAMPSTAT)
BIOLOGICAL_STATUS_CODES = {
    100: "Wild",
    110: "Natural",
    120: "Semi-natural/wild",
    130: "Semi-natural/sown",
    200: "Weedy",
    300: "Traditional cultivar/landrace",
    400: "Breeding/research material",
    410: "Breeder's line",
    411: "Synthetic population",
    412: "Hybrid",
    413: "Founder stock/Base population",
    414: "Inbred line (parent of hybrid)",
    415: "Segregating population",
    416: "Clonal selection",
    420: "Genetic stock",
    421: "Mutant",
    422: "Cytogenetic stocks",
    423: "Other genetic stocks",
    500: "Advanced/improved cultivar",
    600: "GMO",
    999: "Other",
}

# Acquisition Source Codes (COLLSRC)
ACQUISITION_SOURCE_CODES = {
    10: "Wild habitat",
    11: "Forest or woodland",
    12: "Shrubland",
    13: "Grassland",
    14: "Desert or tundra",
    15: "Aquatic habitat",
    20: "Farm or cultivated habitat",
    21: "Field",
    22: "Orchard",
    23: "Backyard, kitchen or home garden",
    24: "Fallow land",
    25: "Pasture",
    26: "Farm store",
    27: "Threshing floor",
    28: "Park",
    30: "Market or shop",
    40: "Institute, Experimental station, Research organization, Genebank",
    50: "Seed company",
    60: "Weedy, disturbed or ruderal habitat",
    61: "Roadside",
    62: "Field margin",
    99: "Other",
}

# Storage Type Codes (STORAGE)
STORAGE_TYPE_CODES = {
    10: "Seed collection",
    11: "Short term (active collection)",
    12: "Medium term",
    13: "Long term (base collection)",
    20: "Field collection",
    30: "In vitro collection",
    40: "Cryopreserved collection",
    50: "DNA collection",
    99: "Other",
}

# MLS Status Codes
MLS_STATUS_CODES = {
    0: "Not included in MLS",
    1: "Included in MLS",
    99: "Unknown",
}


# ISO 3166-1 Alpha-3 Country Codes (common ones)
COUNTRY_CODES = {
    "AFG": "Afghanistan", "ALB": "Albania", "DZA": "Algeria", "ARG": "Argentina",
    "AUS": "Australia", "AUT": "Austria", "BGD": "Bangladesh", "BEL": "Belgium",
    "BOL": "Bolivia", "BRA": "Brazil", "BGR": "Bulgaria", "CAN": "Canada",
    "CHL": "Chile", "CHN": "China", "COL": "Colombia", "CRI": "Costa Rica",
    "CUB": "Cuba", "CZE": "Czech Republic", "DNK": "Denmark", "ECU": "Ecuador",
    "EGY": "Egypt", "ETH": "Ethiopia", "FIN": "Finland", "FRA": "France",
    "DEU": "Germany", "GHA": "Ghana", "GRC": "Greece", "GTM": "Guatemala",
    "HND": "Honduras", "HUN": "Hungary", "IND": "India", "IDN": "Indonesia",
    "IRN": "Iran", "IRQ": "Iraq", "IRL": "Ireland", "ISR": "Israel",
    "ITA": "Italy", "JPN": "Japan", "JOR": "Jordan", "KEN": "Kenya",
    "KOR": "South Korea", "LBN": "Lebanon", "MYS": "Malaysia", "MEX": "Mexico",
    "MAR": "Morocco", "MMR": "Myanmar", "NPL": "Nepal", "NLD": "Netherlands",
    "NZL": "New Zealand", "NGA": "Nigeria", "NOR": "Norway", "PAK": "Pakistan",
    "PAN": "Panama", "PRY": "Paraguay", "PER": "Peru", "PHL": "Philippines",
    "POL": "Poland", "PRT": "Portugal", "ROU": "Romania", "RUS": "Russia",
    "SAU": "Saudi Arabia", "SEN": "Senegal", "ZAF": "South Africa", "ESP": "Spain",
    "LKA": "Sri Lanka", "SDN": "Sudan", "SWE": "Sweden", "CHE": "Switzerland",
    "SYR": "Syria", "TWN": "Taiwan", "TZA": "Tanzania", "THA": "Thailand",
    "TUR": "Turkey", "UGA": "Uganda", "UKR": "Ukraine", "GBR": "United Kingdom",
    "USA": "United States", "URY": "Uruguay", "VEN": "Venezuela", "VNM": "Vietnam",
    "YEM": "Yemen", "ZMB": "Zambia", "ZWE": "Zimbabwe",
}

# Reverse lookup: country name to code
COUNTRY_NAME_TO_CODE = {v.lower(): k for k, v in COUNTRY_CODES.items()}


# ============ MCPD Schema ============

class MCPDRecord(BaseModel):
    """MCPD v2.1 compliant record"""
    # Identifiers
    PUID: Optional[str] = Field(None, description="Persistent Unique Identifier (DOI)")
    INSTCODE: Optional[str] = Field(None, description="FAO WIEWS institute code")
    ACCESSION_NUMBER: str = Field(..., alias="ACCENUMB", description="Accession number")
    COLLNUMB: Optional[str] = Field(None, description="Collecting number")
    OTHERNUMB: Optional[str] = Field(None, description="Other identifiers")

    # Collecting
    COLLCODE: Optional[str] = Field(None, description="Collecting institute code")
    COLLNAME: Optional[str] = Field(None, description="Collecting institute name")
    COLLINSTADDRESS: Optional[str] = Field(None, description="Collecting institute address")
    COLLMISSID: Optional[str] = Field(None, description="Collecting mission ID")
    COLLDATE: Optional[str] = Field(None, description="Collection date (YYYYMMDD)")

    # Taxonomy
    GENUS: str = Field(..., description="Genus name")
    SPECIES: Optional[str] = Field(None, description="Species epithet")
    SPAUTHOR: Optional[str] = Field(None, description="Species authority")
    SUBTAXA: Optional[str] = Field(None, description="Subtaxon")
    SUBTAUTHOR: Optional[str] = Field(None, description="Subtaxon authority")
    CROPNAME: Optional[str] = Field(None, description="Common crop name")

    # Accession info
    ACCENAME: Optional[str] = Field(None, description="Accession name")
    ACQDATE: Optional[str] = Field(None, description="Acquisition date (YYYYMMDD)")
    ORIGCTY: Optional[str] = Field(None, description="Country of origin (ISO 3166-1 alpha-3)")

    # Geographic
    COLLSITE: Optional[str] = Field(None, description="Collection site")
    LATITUDE: Optional[float] = Field(None, ge=-90, le=90, description="Latitude (decimal)")
    LONGITUDE: Optional[float] = Field(None, ge=-180, le=180, description="Longitude (decimal)")
    COORDUNCERT: Optional[float] = Field(None, description="Coordinate uncertainty (m)")
    COORDDATUM: Optional[str] = Field(None, description="Coordinate datum")
    GEOREFMETH: Optional[str] = Field(None, description="Georeferencing method")
    ELEVATION: Optional[float] = Field(None, description="Elevation (m)")

    # Breeding
    BREDCODE: Optional[str] = Field(None, description="Breeding institute code")
    BREDNAME: Optional[str] = Field(None, description="Breeding institute name")
    ANCEST: Optional[str] = Field(None, description="Ancestral/pedigree data")

    # Donor
    DONORCODE: Optional[str] = Field(None, description="Donor institute code")
    DONORNAME: Optional[str] = Field(None, description="Donor institute name")
    DONORNUMB: Optional[str] = Field(None, description="Donor accession number")

    # Status codes
    SAMPSTAT: Optional[int] = Field(None, description="Biological status code")
    COLLSRC: Optional[int] = Field(None, description="Acquisition source code")

    # Safety duplication
    DUPLSITE: Optional[str] = Field(None, description="Safety duplicate site code")
    DUPLINSTNAME: Optional[str] = Field(None, description="Safety duplicate institute name")

    # Storage
    STORAGE: Optional[str] = Field(None, description="Storage type code(s)")

    # MLS
    MLSSTAT: Optional[int] = Field(None, description="MLS status (0/1/99)")

    # Additional
    REMARKS: Optional[str] = Field(None, description="Remarks")
    ACCEURL: Optional[str] = Field(None, description="Accession URL")

    # Metadata
    MCPDVERSION: str = Field("2.1", description="MCPD version")

    model_config = ConfigDict(populate_by_name=True)



# ============ Conversion Functions ============

def format_mcpd_date(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to MCPD date format (YYYYMMDD)"""
    if not dt:
        return None
    return dt.strftime("%Y%m%d")


def parse_mcpd_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse MCPD date format (YYYYMMDD) to datetime"""
    if not date_str or len(date_str) < 4:
        return None
    try:
        # Handle partial dates (unknown month/day)
        year = int(date_str[:4])
        month = int(date_str[4:6]) if len(date_str) >= 6 and date_str[4:6] != "00" else 1
        day = int(date_str[6:8]) if len(date_str) >= 8 and date_str[6:8] != "00" else 1
        return datetime(year, month, day)
    except (ValueError, IndexError):
        return None


def country_name_to_iso(name: Optional[str]) -> Optional[str]:
    """Convert country name to ISO 3166-1 alpha-3 code"""
    if not name:
        return None
    # Check if already a code
    if name.upper() in COUNTRY_CODES:
        return name.upper()
    # Try name lookup
    return COUNTRY_NAME_TO_CODE.get(name.lower())


def iso_to_country_name(code: Optional[str]) -> Optional[str]:
    """Convert ISO 3166-1 alpha-3 code to country name"""
    if not code:
        return None
    return COUNTRY_CODES.get(code.upper())


def map_status_to_sampstat(status: Optional[str]) -> Optional[int]:
    """Map Bijmantra accession status to MCPD SAMPSTAT code"""
    status_mapping = {
        "wild": 100,
        "landrace": 300,
        "traditional": 300,
        "breeding_line": 410,
        "breeder's line": 410,
        "hybrid": 412,
        "inbred": 414,
        "cultivar": 500,
        "improved": 500,
        "active": 400,  # Default for active accessions
    }
    if not status:
        return None
    return status_mapping.get(status.lower(), 999)


def map_sampstat_to_status(sampstat: Optional[int]) -> str:
    """Map MCPD SAMPSTAT code to Bijmantra accession status"""
    if not sampstat:
        return "active"
    if sampstat < 200:
        return "active"  # Wild types
    if sampstat == 300:
        return "active"  # Landrace
    if 400 <= sampstat < 500:
        return "active"  # Breeding material
    if sampstat >= 500:
        return "active"  # Cultivar
    return "active"


def map_vault_type_to_storage(vault_type: Optional[str]) -> Optional[str]:
    """Map Bijmantra vault type to MCPD STORAGE code"""
    vault_mapping = {
        "base": "13",      # Long term
        "active": "11",    # Short term
        "cryo": "40",      # Cryopreserved
    }
    if not vault_type:
        return None
    return vault_mapping.get(vault_type.lower(), "10")


def map_storage_to_vault_type(storage: Optional[str]) -> Optional[str]:
    """Map MCPD STORAGE code to Bijmantra vault type"""
    if not storage:
        return None
    storage_code = storage.split(";")[0].strip()  # Take first if multiple
    storage_mapping = {
        "10": "active",
        "11": "active",
        "12": "active",
        "13": "base",
        "20": "active",
        "30": "active",
        "40": "cryo",
        "50": "active",
    }
    return storage_mapping.get(storage_code, "active")



# ============ Export Functions ============

def accession_to_mcpd(accession: Any, inst_code: str = "BIJ001") -> MCPDRecord:
    """Convert Bijmantra Accession to MCPD record"""
    return MCPDRecord(
        INSTCODE=inst_code,
        ACCENUMB=accession.accession_number,
        GENUS=accession.genus,
        SPECIES=accession.species,
        SUBTAXA=accession.subspecies,
        CROPNAME=accession.common_name,
        ORIGCTY=country_name_to_iso(accession.origin),
        COLLDATE=format_mcpd_date(accession.collection_date),
        COLLSITE=accession.collection_site,
        LATITUDE=accession.latitude,
        LONGITUDE=accession.longitude,
        ELEVATION=accession.altitude,
        SAMPSTAT=map_status_to_sampstat(accession.status.value if hasattr(accession.status, 'value') else accession.status),
        STORAGE=map_vault_type_to_storage(accession.vault.type.value if accession.vault else None) if hasattr(accession, 'vault') and accession.vault else None,
        MLSSTAT=1 if accession.mls else 0,
        DONORNAME=accession.donor_institution,
        ANCEST=accession.pedigree,
        REMARKS=accession.notes,
        MCPDVERSION="2.1",
    )


def export_to_mcpd_csv(accessions: List[Any], inst_code: str = "BIJ001") -> str:
    """Export accessions to MCPD CSV format"""
    output = io.StringIO()

    # MCPD field order
    fieldnames = [
        "PUID", "INSTCODE", "ACCENUMB", "COLLNUMB", "OTHERNUMB",
        "COLLCODE", "COLLNAME", "COLLINSTADDRESS", "COLLMISSID", "COLLDATE",
        "GENUS", "SPECIES", "SPAUTHOR", "SUBTAXA", "SUBTAUTHOR", "CROPNAME",
        "ACCENAME", "ACQDATE", "ORIGCTY",
        "COLLSITE", "LATITUDE", "LONGITUDE", "COORDUNCERT", "COORDDATUM", "GEOREFMETH", "ELEVATION",
        "BREDCODE", "BREDNAME", "ANCEST",
        "DONORCODE", "DONORNAME", "DONORNUMB",
        "SAMPSTAT", "COLLSRC",
        "DUPLSITE", "DUPLINSTNAME",
        "STORAGE", "MLSSTAT",
        "REMARKS", "ACCEURL", "MCPDVERSION",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()

    for accession in accessions:
        mcpd = accession_to_mcpd(accession, inst_code)
        row = mcpd.model_dump(by_alias=True, exclude_none=False)
        # Convert None to empty string for CSV
        row = {k: (v if v is not None else "") for k, v in row.items()}
        writer.writerow(row)

    return output.getvalue()


def export_to_mcpd_json(accessions: List[Any], inst_code: str = "BIJ001") -> List[Dict[str, Any]]:
    """Export accessions to MCPD JSON format"""
    return [
        accession_to_mcpd(acc, inst_code).model_dump(by_alias=True, exclude_none=True)
        for acc in accessions
    ]


# ============ Import Functions ============

class MCPDImportResult(BaseModel):
    """Result of MCPD import operation"""
    total_records: int
    imported: int
    skipped: int
    errors: List[Dict[str, Any]]


def parse_mcpd_csv(csv_content: str) -> List[Dict[str, Any]]:
    """Parse MCPD CSV content to list of dictionaries"""
    reader = csv.DictReader(io.StringIO(csv_content))
    records = []
    for row in reader:
        # Clean up empty strings to None
        cleaned = {k: (v if v.strip() else None) for k, v in row.items()}
        records.append(cleaned)
    return records


def mcpd_to_accession_data(mcpd_row: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MCPD row to Bijmantra accession data"""
    return {
        "accession_number": mcpd_row.get("ACCENUMB"),
        "genus": mcpd_row.get("GENUS"),
        "species": mcpd_row.get("SPECIES"),
        "subspecies": mcpd_row.get("SUBTAXA"),
        "common_name": mcpd_row.get("CROPNAME"),
        "origin": iso_to_country_name(mcpd_row.get("ORIGCTY")) or mcpd_row.get("ORIGCTY"),
        "collection_date": parse_mcpd_date(mcpd_row.get("COLLDATE")),
        "collection_site": mcpd_row.get("COLLSITE"),
        "latitude": float(mcpd_row["LATITUDE"]) if mcpd_row.get("LATITUDE") else None,
        "longitude": float(mcpd_row["LONGITUDE"]) if mcpd_row.get("LONGITUDE") else None,
        "altitude": float(mcpd_row["ELEVATION"]) if mcpd_row.get("ELEVATION") else None,
        "mls": mcpd_row.get("MLSSTAT") == "1",
        "donor_institution": mcpd_row.get("DONORNAME"),
        "pedigree": mcpd_row.get("ANCEST"),
        "notes": mcpd_row.get("REMARKS"),
        "acquisition_type": mcpd_row.get("COLLSRC"),
        # Metadata for reference
        "_mcpd_sampstat": mcpd_row.get("SAMPSTAT"),
        "_mcpd_storage": mcpd_row.get("STORAGE"),
        "_mcpd_instcode": mcpd_row.get("INSTCODE"),
    }


def validate_mcpd_record(mcpd_row: Dict[str, Any]) -> List[str]:
    """Validate MCPD record and return list of errors"""
    errors = []

    # Required fields
    if not mcpd_row.get("ACCENUMB"):
        errors.append("ACCENUMB (Accession Number) is required")
    if not mcpd_row.get("GENUS"):
        errors.append("GENUS is required")

    # Validate country code
    origcty = mcpd_row.get("ORIGCTY")
    if origcty and origcty.upper() not in COUNTRY_CODES:
        errors.append(f"Invalid country code: {origcty}")

    # Validate coordinates
    lat = mcpd_row.get("LATITUDE")
    if lat:
        try:
            lat_val = float(lat)
            if lat_val < -90 or lat_val > 90:
                errors.append(f"LATITUDE must be between -90 and 90: {lat}")
        except ValueError:
            errors.append(f"Invalid LATITUDE value: {lat}")

    lon = mcpd_row.get("LONGITUDE")
    if lon:
        try:
            lon_val = float(lon)
            if lon_val < -180 or lon_val > 180:
                errors.append(f"LONGITUDE must be between -180 and 180: {lon}")
        except ValueError:
            errors.append(f"Invalid LONGITUDE value: {lon}")

    # Validate SAMPSTAT code
    sampstat = mcpd_row.get("SAMPSTAT")
    if sampstat:
        try:
            sampstat_val = int(sampstat)
            if sampstat_val not in BIOLOGICAL_STATUS_CODES:
                errors.append(f"Invalid SAMPSTAT code: {sampstat}")
        except ValueError:
            errors.append(f"SAMPSTAT must be a number: {sampstat}")

    # Validate date format
    colldate = mcpd_row.get("COLLDATE")
    if colldate and len(colldate) >= 4:
        try:
            int(colldate[:4])  # Year must be numeric
        except ValueError:
            errors.append(f"Invalid COLLDATE format: {colldate}")

    return errors


# ============ Reference Data ============

def get_biological_status_codes() -> Dict[int, str]:
    """Get all biological status codes"""
    return BIOLOGICAL_STATUS_CODES.copy()


def get_acquisition_source_codes() -> Dict[int, str]:
    """Get all acquisition source codes"""
    return ACQUISITION_SOURCE_CODES.copy()


def get_storage_type_codes() -> Dict[int, str]:
    """Get all storage type codes"""
    return STORAGE_TYPE_CODES.copy()


def get_country_codes() -> Dict[str, str]:
    """Get all country codes"""
    return COUNTRY_CODES.copy()
