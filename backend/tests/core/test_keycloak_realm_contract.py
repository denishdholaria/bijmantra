"""Contract tests for the local Keycloak realm import."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REALM_PATH = (
    Path(__file__).resolve().parents[3]
    / "infra"
    / "keycloak"
    / "realms"
    / "bijmantra-realm.json"
)


def _realm() -> dict[str, Any]:
    return json.loads(REALM_PATH.read_text())


def _client(realm: dict[str, Any], client_id: str) -> dict[str, Any]:
    for client in realm.get("clients", []):
        if client.get("clientId") == client_id:
            return client
    raise AssertionError(f"Missing Keycloak client {client_id!r}")


def test_bijmantra_web_access_token_carries_stable_subject_claim() -> None:
    client = _client(_realm(), "bijmantra-web")

    subject_mappers = [
        mapper
        for mapper in client.get("protocolMappers", [])
        if mapper.get("protocolMapper") == "oidc-sub-mapper"
    ]

    assert subject_mappers, "bijmantra-web access tokens must include Keycloak subject"
    assert any(
        mapper.get("config", {}).get("access.token.claim") == "true"
        for mapper in subject_mappers
    )


def test_bijmantra_web_access_token_targets_api_audience() -> None:
    realm = _realm()
    client = _client(realm, "bijmantra-web")

    assert "bijmantra-api-audience" in client.get("defaultClientScopes", [])

    audience_scope = next(
        scope
        for scope in realm.get("clientScopes", [])
        if scope.get("name") == "bijmantra-api-audience"
    )
    audience_mapper = next(
        mapper
        for mapper in audience_scope.get("protocolMappers", [])
        if mapper.get("protocolMapper") == "oidc-audience-mapper"
    )

    assert audience_mapper.get("config", {}).get("included.client.audience") == "bijmantra-api"
    assert audience_mapper.get("config", {}).get("access.token.claim") == "true"
