import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v2 import import_api
from app.models import BioQTL
from app.models.germplasm import Germplasm
from app.models.core import User, Organization
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_import_germplasm_upload_uses_user_org_id(
    authenticated_client: AsyncClient,
    async_db_session: AsyncSession,
    test_user: User,
    monkeypatch,
):
    org_id = test_user.organization_id
    assert org_id is not None

    org_in_db = await async_db_session.get(Organization, org_id)
    assert org_in_db is not None, f"Organization {org_id} not found in Async Session!"

    session_factory = async_sessionmaker(
        bind=async_db_session.bind,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    monkeypatch.setattr(import_api, "AsyncSessionLocal", session_factory)

    payload = {
        "data": [
            {
                "germplasm_name": "UniqueGermplasm123",
                "accession_number": "A123",
                "genus": "Zea",
                "species": "mays",
                "common_crop_name": "Maize",
            }
        ]
    }

    response = await authenticated_client.post(
        "/api/v2/import/upload",
        data={"import_type": "germplasm"},
        files={
            "file": (
                "germplasm.json",
                json.dumps(payload),
                "application/json",
            )
        },
    )
    assert response.status_code == 200, f"Response: {response.text}"
    body = response.json()
    assert body["status"] == "queued"
    assert body["mapping_suggestions"]["germplasm_name"] == "germplasm_name"

    query = select(Germplasm).where(Germplasm.germplasm_name == "UniqueGermplasm123")
    result = await async_db_session.execute(query)
    germplasm = result.scalars().first()

    assert germplasm is not None
    assert germplasm.organization_id == org_id, (
        f"Expected {org_id}, got {germplasm.organization_id}"
    )


@pytest.mark.asyncio
async def test_import_qtl_upload_uses_user_org_id(
    authenticated_client: AsyncClient,
    async_db_session: AsyncSession,
    test_user: User,
    monkeypatch,
):
    org_id = test_user.organization_id
    assert org_id is not None

    session_factory = async_sessionmaker(
        bind=async_db_session.bind,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    monkeypatch.setattr(import_api, "AsyncSessionLocal", session_factory)

    payload = {
        "data": [
            {
                "qtl_db_id": "QTL-ORG-001",
                "qtl_name": "Yield Stability QTL",
                "trait": "Yield",
                "chromosome": "1A",
                "start_position": "10.5",
                "end_position": "20.5",
                "peak_position": "15.5",
                "lod": "6.1",
                "pve": "12.4",
                "marker_name": "AX-12345",
                "candidate_genes": [
                    {"gene_id": "TraesCS1A01G000100", "gene_name": "Rht-A1"}
                ],
            }
        ]
    }

    response = await authenticated_client.post(
        "/api/v2/import/upload",
        data={"import_type": "qtl"},
        files={
            "file": (
                "qtl.json",
                json.dumps(payload),
                "application/json",
            )
        },
    )
    assert response.status_code == 200, f"Response: {response.text}"
    body = response.json()
    assert body["status"] == "queued"
    assert body["mapping_suggestions"]["qtl_db_id"] == "qtl_db_id"
    assert body["mapping_suggestions"]["trait"] == "trait"
    assert body["mapping_suggestions"]["chromosome"] == "chromosome"

    result = await async_db_session.execute(select(BioQTL).where(BioQTL.qtl_db_id == "QTL-ORG-001"))
    qtl = result.scalars().one_or_none()

    assert qtl is not None
    assert qtl.organization_id == org_id
    assert qtl.qtl_name == "Yield Stability QTL"
    assert qtl.lod == pytest.approx(6.1)
    assert qtl.pve == pytest.approx(12.4)
    assert qtl.candidate_genes_json == [
        {"gene_id": "TraesCS1A01G000100", "gene_name": "Rht-A1"}
    ]
