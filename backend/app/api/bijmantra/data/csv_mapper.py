import asyncio
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.modules.core.services.infra.csv_enterprise_regex_mapper import CsvRegexMapper, MapperConfig


router = APIRouter()
mapper = CsvRegexMapper()

@router.post("/map")
async def map_csv(
    file: Annotated[UploadFile, File(...)],
    config_json: Annotated[str, Form(...)] # Accept JSON config as string in form
):
    """
    Upload a CSV file and a mapping configuration (as JSON string) to transform the data.
    """
    try:
        config = MapperConfig.model_validate_json(config_json)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}")

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    try:
        # Offload CPU-bound processing to thread pool
        result = await asyncio.to_thread(mapper.process, content, config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In production, log the error here
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return result
