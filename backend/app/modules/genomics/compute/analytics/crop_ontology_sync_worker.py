"""
Crop Ontology Sync Worker
Fetches trait definitions from Crop Ontology BrAPI and syncs to local database.
"""

import logging
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http_tracing import create_traced_async_client
from app.models.phenotyping import ObservationVariable

logger = logging.getLogger(__name__)


class CropOntologySyncWorker:
    """Worker to sync Crop Ontology data via BrAPI"""

    def __init__(self, base_url: str = "https://cropontology.org/brapi/v1"):
        self.base_url = base_url.rstrip("/")

    async def fetch_variables(self, ontology_id: str) -> list[dict[str, Any]]:
        """
        Fetch variables from Crop Ontology BrAPI, handling pagination.

        Args:
            ontology_id: The ontology ID to fetch (e.g., "CO_320")

        Returns:
            List of variable dictionaries
        """
        url = f"{self.base_url}/variables"
        page = 0
        page_size = 1000
        all_variables = []

        async with create_traced_async_client() as client:
            while True:
                params = {"ontologyDbId": ontology_id, "pageSize": page_size, "page": page}
                try:
                    response = await client.get(url, params=params, timeout=30.0)
                    response.raise_for_status()
                    data = response.json()

                    if "result" in data and "data" in data["result"]:
                        chunk = data["result"]["data"]
                        if not chunk:
                            break
                        all_variables.extend(chunk)

                        # Check pagination
                        metadata = data.get("metadata", {})
                        pagination = metadata.get("pagination", {})
                        total_pages = pagination.get("totalPages")
                        current_page = pagination.get("currentPage")

                        # If pagination info is missing, assume single page or stop
                        if total_pages is None:
                            # Try to see if chunk size < page_size, then likely last page
                            if len(chunk) < page_size:
                                break
                            # Else continue? Usually BrAPI returns pagination.
                            # Default to stop if no pagination info to avoid infinite loop
                            break

                        if current_page >= total_pages - 1:
                            break

                        page += 1
                    else:
                        break
                except httpx.HTTPError as e:
                    logger.error(f"Failed to fetch variables page {page} for {ontology_id}: {str(e)}")
                    raise

        return all_variables

    async def sync_ontology(
        self,
        ontology_id: str,
        organization_id: int,
        session: AsyncSession
    ) -> dict[str, int]:
        """
        Sync ontology variables to local database.

        Args:
            ontology_id: The ontology ID to sync
            organization_id: The organization ID to assign variables to
            session: Database session

        Returns:
            Dictionary with counts of created and updated variables
        """
        try:
            variables = await self.fetch_variables(ontology_id)
        except Exception as e:
            logger.error(f"Failed to fetch or parse variables: {e}")
            return {"created": 0, "updated": 0, "errors": 1}

        created_count = 0
        updated_count = 0

        # Collect IDs to sync
        ids = [v.get("observationVariableDbId") for v in variables if v.get("observationVariableDbId")]
        if not ids:
             return {"created": 0, "updated": 0, "errors": 0}

        # Fetch existing variables in batch
        existing_vars = {}
        chunk_size = 500
        # Use set to dedup input IDs just in case
        unique_ids = list(set(ids))

        for i in range(0, len(unique_ids), chunk_size):
            chunk_ids = unique_ids[i:i + chunk_size]
            stmt = select(ObservationVariable).where(
                ObservationVariable.observation_variable_db_id.in_(chunk_ids)
            )
            result = await session.execute(stmt)
            for var in result.scalars().all():
                existing_vars[var.observation_variable_db_id] = var

        processed_ids = set()

        for var_data in variables:
            db_id = var_data.get("observationVariableDbId")
            if not db_id:
                continue

            if db_id in processed_ids:
                logger.warning(f"Duplicate variable ID in response: {db_id}, skipping")
                continue
            processed_ids.add(db_id)

            # Extract sub-objects safely
            trait = var_data.get("trait") or {}
            method = var_data.get("method") or {}
            scale = var_data.get("scale") or {}

            # Prepare model data
            model_data = {
                "organization_id": organization_id,
                "observation_variable_db_id": db_id,
                "observation_variable_name": var_data.get("observationVariableName"),
                "common_crop_name": var_data.get("crop"),
                "default_value": var_data.get("defaultValue"),
                "document_ids": [var_data.get("documentationURL")] if var_data.get("documentationURL") else [],
                "growth_stage": var_data.get("growthStage"),
                "institution": var_data.get("institution"),
                "language": var_data.get("language"),
                "scientist": var_data.get("scientist"),
                "status": var_data.get("status"),
                "submission_timestamp": var_data.get("submissionTimestamp"),
                "synonyms": var_data.get("synonyms"),

                # Trait info
                "trait_db_id": trait.get("traitDbId"),
                "trait_name": trait.get("traitName"),
                "trait_description": trait.get("description"),
                "trait_class": trait.get("class"),

                # Method info
                "method_db_id": method.get("methodDbId"),
                "method_name": method.get("methodName"),
                "method_description": method.get("description"),
                "method_class": method.get("class"),
                "formula": method.get("formula"),

                # Scale info
                "scale_db_id": scale.get("scaleDbId"),
                "scale_name": scale.get("scaleName"),
                "data_type": scale.get("dataType"),
                "decimal_places": scale.get("decimalPlaces"),
                "valid_values": scale.get("validValues"),

                # Ontology
                "ontology_db_id": var_data.get("ontologyDbId"),
                "ontology_name": var_data.get("ontologyName"),
            }

            if db_id in existing_vars:
                # Update existing variable
                existing_var = existing_vars[db_id]
                for key, value in model_data.items():
                    setattr(existing_var, key, value)
                updated_count += 1
            else:
                # Create new variable
                new_var = ObservationVariable(**model_data)
                session.add(new_var)
                created_count += 1

        try:
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to commit sync: {e}")
            await session.rollback()
            return {"created": 0, "updated": 0, "errors": 1}

        return {"created": created_count, "updated": updated_count, "errors": 0}
