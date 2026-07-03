"""Pure Knowledge Graph edge identity rules."""

import hashlib
import json
from typing import Any


def deterministic_edge_id(
    *,
    source_asset_type: str,
    source_asset_id: str,
    relationship_type: str,
    target_asset_type: str,
    target_asset_id: str,
) -> str:
    """Return the stable tenant-local identity for a graph edge relation."""
    digest = _sha256_digest(
        {
            "sourceAssetType": source_asset_type,
            "sourceAssetId": source_asset_id,
            "relationshipType": relationship_type,
            "targetAssetType": target_asset_type,
            "targetAssetId": target_asset_id,
        }
    )
    return f"kg-edge-{digest[:16]}"


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_digest(data: Any) -> str:
    return hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()
