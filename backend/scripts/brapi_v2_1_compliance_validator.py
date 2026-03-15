#!/usr/bin/env python3
"""
# BIJMANTRA JULES JOB CARD: D03
BrAPI v2.1 Compliance Validator Script

This script validates a given URL or JSON file against BrAPI v2.1 schemas.
It supports validating common endpoints like ServerInfo, Programs, Trials, etc.

Usage:
    python backend/scripts/brapi_v2_1_compliance_validator.py --url <URL> --type serverinfo
    python backend/scripts/brapi_v2_1_compliance_validator.py --file <FILE> --type program
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError


# Ensure project root is in sys.path for app imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# --- Local Schema Definitions (if missing in app.schemas) ---

class Service(BaseModel):
    """BrAPI Service Schema"""
    service: str
    versions: list[str]

class ServerInfo(BaseModel):
    """BrAPI ServerInfo Schema"""
    serverName: str = Field(..., alias="serverName")
    serverDescription: str | None = Field(None, alias="serverDescription")
    apiVersion: str = Field(..., alias="apiVersion")
    documentationURL: str | None = Field(None, alias="documentationURL")
    contactEmail: str | None = Field(None, alias="contactEmail")
    organizationName: str | None = Field(None, alias="organizationName")
    organizationUrl: str | None = Field(None, alias="organizationUrl")
    location: str | None = Field(None, alias="location")
    calls: list[Service] = []

    model_config = ConfigDict(populate_by_name=True)

# Attempt to import app schemas, fallback to local definitions if necessary
APP_SCHEMAS_AVAILABLE = False
BrAPIResponse = None
Metadata = None

try:
    from app.schemas.brapi import BrAPIResponse
    from app.schemas.core import Location, Person, Program, Season, Study, Trial
    APP_SCHEMAS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import app schemas: {e}. Using local definitions where possible.")
    # Define minimal fallbacks or exit if strict validation is required
    # For now, we will assume the environment is correct as per instructions.
    # If BrAPIResponse is missing, we can't really validate effectively without redefining it fully.
    # But since we are in the repo, it should be available.

# --- Validator Logic ---

def validate_brapi_response(data: dict[str, Any], result_model: type[BaseModel] | None = None) -> bool:
    """
    Validates a dictionary against the BrAPIResponse schema and an optional result model.
    """
    if not APP_SCHEMAS_AVAILABLE or BrAPIResponse is None:
        logger.error("App schemas not available. Cannot perform strict validation.")
        return False

    try:
        # Validate structure
        # If result_model is provided, use it to validate the 'result' field
        if result_model:
            # Dynamically create the parameterized class
            # Note: BrAPIResponse[result_model] returns a class in Pydantic V2
            ResponseModel = BrAPIResponse[result_model]
            ResponseModel.model_validate(data)
        else:
            # Validate generic structure
            # Use object or dict for generic result validation if not specified
            ResponseModel = BrAPIResponse[Any]
            ResponseModel.model_validate(data)

        logger.info("Structure validation passed.")

        # Additional BrAPI v2.1 specific checks (logic not covered by types)
        # 1. Check metadata.pagination exists (it is required in schema)
        # 2. Check metadata.status is a list

        # Since model_validate passed, types are correct.

        return True

    except ValidationError as e:
        logger.error(f"Validation failed:\n{e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return False

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="BrAPI v2.1 Compliance Validator")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="URL to fetch and validate")
    group.add_argument("--file", help="JSON file to validate")

    parser.add_argument("--type", help="Expected object type (serverinfo, program, trial, etc.)",
                        choices=["serverinfo", "program", "trial", "study", "location", "person", "season"],
                        default=None)

    args = parser.parse_args()

    # Determine the model to validate against
    model_map = {
        "serverinfo": ServerInfo,
    }

    if APP_SCHEMAS_AVAILABLE:
        try:
            model_map.update({
                "program": Program,
                "trial": Trial,
                "study": Study,
                "location": Location,
                "person": Person,
                "season": Season
            })
        except NameError:
            pass # Some might not be imported if imports failed

    target_model = model_map.get(args.type) if args.type else None

    # If type is provided but model not found (and schemas available), warn user
    if args.type and not target_model and APP_SCHEMAS_AVAILABLE:
        logger.warning(f"Type '{args.type}' requested but model definition not found/imported.")

    data = {}

    if args.file:
        try:
            with open(args.file) as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            sys.exit(1)
    elif args.url:
        try:
            logger.info(f"Fetching {args.url}...")
            # Use httpx to fetch
            with httpx.Client() as client:
                response = client.get(args.url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            sys.exit(1)
        except json.JSONDecodeError:
            logger.error("Response is not valid JSON")
            sys.exit(1)

    if validate_brapi_response(data, target_model):
        logger.info("✅ Validation SUCCESS")
        sys.exit(0)
    else:
        logger.error("❌ Validation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
