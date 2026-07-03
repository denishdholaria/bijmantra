"""MCPD v2.1 reference vocabulary for accession passport exchange."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any


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

MLS_STATUS_CODES = {
    0: "Not included in MLS",
    1: "Included in MLS",
    99: "Unknown",
}

COUNTRY_CODES = {
    "AFG": "Afghanistan",
    "ALB": "Albania",
    "DZA": "Algeria",
    "ARG": "Argentina",
    "AUS": "Australia",
    "AUT": "Austria",
    "BGD": "Bangladesh",
    "BEL": "Belgium",
    "BOL": "Bolivia",
    "BRA": "Brazil",
    "BGR": "Bulgaria",
    "CAN": "Canada",
    "CHL": "Chile",
    "CHN": "China",
    "COL": "Colombia",
    "CRI": "Costa Rica",
    "CUB": "Cuba",
    "CZE": "Czech Republic",
    "DNK": "Denmark",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "ETH": "Ethiopia",
    "FIN": "Finland",
    "FRA": "France",
    "DEU": "Germany",
    "GHA": "Ghana",
    "GRC": "Greece",
    "GTM": "Guatemala",
    "HND": "Honduras",
    "HUN": "Hungary",
    "IND": "India",
    "IDN": "Indonesia",
    "IRN": "Iran",
    "IRQ": "Iraq",
    "IRL": "Ireland",
    "ISR": "Israel",
    "ITA": "Italy",
    "JPN": "Japan",
    "JOR": "Jordan",
    "KEN": "Kenya",
    "KOR": "South Korea",
    "LBN": "Lebanon",
    "MYS": "Malaysia",
    "MEX": "Mexico",
    "MAR": "Morocco",
    "MMR": "Myanmar",
    "NPL": "Nepal",
    "NLD": "Netherlands",
    "NZL": "New Zealand",
    "NGA": "Nigeria",
    "NOR": "Norway",
    "PAK": "Pakistan",
    "PAN": "Panama",
    "PRY": "Paraguay",
    "PER": "Peru",
    "PHL": "Philippines",
    "POL": "Poland",
    "PRT": "Portugal",
    "ROU": "Romania",
    "RUS": "Russia",
    "SAU": "Saudi Arabia",
    "SEN": "Senegal",
    "ZAF": "South Africa",
    "ESP": "Spain",
    "LKA": "Sri Lanka",
    "SDN": "Sudan",
    "SWE": "Sweden",
    "CHE": "Switzerland",
    "SYR": "Syria",
    "TWN": "Taiwan",
    "TZA": "Tanzania",
    "THA": "Thailand",
    "TUR": "Turkey",
    "UGA": "Uganda",
    "UKR": "Ukraine",
    "GBR": "United Kingdom",
    "USA": "United States",
    "URY": "Uruguay",
    "VEN": "Venezuela",
    "VNM": "Vietnam",
    "YEM": "Yemen",
    "ZMB": "Zambia",
    "ZWE": "Zimbabwe",
}

COUNTRY_NAME_TO_CODE = {v.lower(): k for k, v in COUNTRY_CODES.items()}

MCPD_TEMPLATE_FIELDNAMES = (
    "PUID",
    "INSTCODE",
    "ACCENUMB",
    "COLLNUMB",
    "OTHERNUMB",
    "COLLCODE",
    "COLLNAME",
    "COLLINSTADDRESS",
    "COLLMISSID",
    "COLLDATE",
    "GENUS",
    "SPECIES",
    "SPAUTHOR",
    "SUBTAXA",
    "SUBTAUTHOR",
    "CROPNAME",
    "ACCENAME",
    "ACQDATE",
    "ORIGCTY",
    "COLLSITE",
    "LATITUDE",
    "LONGITUDE",
    "COORDUNCERT",
    "COORDDATUM",
    "GEOREFMETH",
    "ELEVATION",
    "BREDCODE",
    "BREDNAME",
    "ANCEST",
    "DONORCODE",
    "DONORNAME",
    "DONORNUMB",
    "SAMPSTAT",
    "COLLSRC",
    "DUPLSITE",
    "DUPLINSTNAME",
    "STORAGE",
    "MLSSTAT",
    "REMARKS",
    "ACCEURL",
    "MCPDVERSION",
)

MCPD_TEMPLATE_EXAMPLE_ROW = (
    "",
    "BIJ001",
    "ACC-001",
    "",
    "",
    "",
    "",
    "",
    "",
    "20240115",
    "Oryza",
    "sativa",
    "L.",
    "indica",
    "",
    "Rice",
    "IR64",
    "20240101",
    "IND",
    "Punjab, India",
    "30.7333",
    "76.7794",
    "",
    "WGS84",
    "GPS",
    "250",
    "",
    "",
    "IR8/TKM6",
    "",
    "IRRI",
    "",
    "500",
    "40",
    "",
    "",
    "13",
    "1",
    "Example accession",
    "",
    "2.1",
)


def build_mcpd_template_csv() -> str:
    """Build an MCPD v2.1 CSV import template."""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(MCPD_TEMPLATE_FIELDNAMES)
    writer.writerow(MCPD_TEMPLATE_EXAMPLE_ROW)
    return output.getvalue()


def format_mcpd_date(dt: datetime | None) -> str | None:
    """Convert a datetime to MCPD date format."""

    if not dt:
        return None
    return dt.strftime("%Y%m%d")


def parse_mcpd_date(date_str: str | None) -> datetime | None:
    """Parse MCPD date format into a datetime."""

    if not date_str or len(date_str) < 4:
        return None
    try:
        year = int(date_str[:4])
        month = int(date_str[4:6]) if len(date_str) >= 6 and date_str[4:6] != "00" else 1
        day = int(date_str[6:8]) if len(date_str) >= 8 and date_str[6:8] != "00" else 1
        return datetime(year, month, day)
    except (ValueError, IndexError):
        return None


def country_name_to_iso(name: str | None) -> str | None:
    """Convert a country name to an ISO 3166-1 alpha-3 code."""

    if not name:
        return None
    if name.upper() in COUNTRY_CODES:
        return name.upper()
    return COUNTRY_NAME_TO_CODE.get(name.lower())


def iso_to_country_name(code: str | None) -> str | None:
    """Convert an ISO 3166-1 alpha-3 code to a country name."""

    if not code:
        return None
    return COUNTRY_CODES.get(code.upper())


def map_status_to_sampstat(status: str | None) -> int | None:
    """Map a BijMantra accession status to an MCPD SAMPSTAT code."""

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
        "active": 400,
    }
    if not status:
        return None
    return status_mapping.get(status.lower(), 999)


def map_sampstat_to_status(sampstat: int | None) -> str:
    """Map an MCPD SAMPSTAT code to a BijMantra accession status."""

    if not sampstat:
        return "active"
    if sampstat < 200:
        return "active"
    if sampstat == 300:
        return "active"
    if 400 <= sampstat < 500:
        return "active"
    if sampstat >= 500:
        return "active"
    return "active"


def map_vault_type_to_storage(vault_type: str | None) -> str | None:
    """Map a BijMantra vault type to an MCPD STORAGE code."""

    vault_mapping = {
        "base": "13",
        "active": "11",
        "cryo": "40",
    }
    if not vault_type:
        return None
    return vault_mapping.get(vault_type.lower(), "10")


def map_storage_to_vault_type(storage: str | None) -> str | None:
    """Map an MCPD STORAGE code to a BijMantra vault type."""

    if not storage:
        return None
    storage_code = storage.split(";")[0].strip()
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


def parse_mcpd_csv(csv_content: str) -> list[dict[str, Any]]:
    """Parse MCPD CSV content to rows with empty strings normalized to None."""

    reader = csv.DictReader(io.StringIO(csv_content))
    records = []
    for row in reader:
        cleaned = {key: (value if value.strip() else None) for key, value in row.items()}
        records.append(cleaned)
    return records


def mcpd_to_accession_data(mcpd_row: dict[str, Any]) -> dict[str, Any]:
    """Convert an MCPD row to accession persistence data."""

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
        "_mcpd_sampstat": mcpd_row.get("SAMPSTAT"),
        "_mcpd_storage": mcpd_row.get("STORAGE"),
        "_mcpd_instcode": mcpd_row.get("INSTCODE"),
    }


def validate_mcpd_record(mcpd_row: dict[str, Any]) -> list[str]:
    """Validate a parsed MCPD row and return human-readable errors."""

    errors = []

    if not mcpd_row.get("ACCENUMB"):
        errors.append("ACCENUMB (Accession Number) is required")
    if not mcpd_row.get("GENUS"):
        errors.append("GENUS is required")

    origcty = mcpd_row.get("ORIGCTY")
    if origcty and origcty.upper() not in COUNTRY_CODES:
        errors.append(f"Invalid country code: {origcty}")

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

    sampstat = mcpd_row.get("SAMPSTAT")
    if sampstat:
        try:
            sampstat_val = int(sampstat)
            if sampstat_val not in BIOLOGICAL_STATUS_CODES:
                errors.append(f"Invalid SAMPSTAT code: {sampstat}")
        except ValueError:
            errors.append(f"SAMPSTAT must be a number: {sampstat}")

    colldate = mcpd_row.get("COLLDATE")
    if colldate and len(colldate) >= 4:
        try:
            int(colldate[:4])
        except ValueError:
            errors.append(f"Invalid COLLDATE format: {colldate}")

    return errors


def biological_status_codes_payload() -> dict[str, Any]:
    """Return the MCPD SAMPSTAT reference payload."""

    return {
        "field": "SAMPSTAT",
        "description": "Biological status of accession",
        "codes": [
            {"code": code, "description": description}
            for code, description in BIOLOGICAL_STATUS_CODES.items()
        ],
    }


def acquisition_source_codes_payload() -> dict[str, Any]:
    """Return the MCPD COLLSRC reference payload."""

    return {
        "field": "COLLSRC",
        "description": "Collecting/acquisition source",
        "codes": [
            {"code": code, "description": description}
            for code, description in ACQUISITION_SOURCE_CODES.items()
        ],
    }


def storage_type_codes_payload() -> dict[str, Any]:
    """Return the MCPD STORAGE reference payload."""

    return {
        "field": "STORAGE",
        "description": "Type of germplasm storage",
        "codes": [
            {"code": code, "description": description}
            for code, description in STORAGE_TYPE_CODES.items()
        ],
    }


def country_codes_payload() -> dict[str, Any]:
    """Return the MCPD ORIGCTY reference payload."""

    return {
        "field": "ORIGCTY",
        "description": "Country of origin (ISO 3166-1 alpha-3)",
        "codes": [
            {"code": code, "name": name}
            for code, name in sorted(COUNTRY_CODES.items(), key=lambda item: item[1])
        ],
    }
