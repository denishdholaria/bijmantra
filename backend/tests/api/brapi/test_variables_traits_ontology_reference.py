from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.brapi.v2.traits import TraitCreate, create_trait, get_trait, update_trait
from app.api.brapi.v2.variables import (
    VariableCreate,
    VariableUpdate,
    create_variable,
    get_variable,
    update_variable,
)
from app.models.phenotyping import ObservationVariable


@pytest.fixture(autouse=True)
async def create_observation_variable_table(async_db_session: AsyncSession):
    engine = async_db_session.bind
    async with engine.begin() as conn:
        await conn.run_sync(ObservationVariable.metadata.create_all)
    yield


def _current_user(test_user):
    return SimpleNamespace(organization_id=test_user.organization_id)


def _ontology_reference(term_id: str, version: str = "v2.1") -> dict:
    return {
        "ontologyDbId": "CO_320",
        "ontologyName": "Rice Ontology",
        "ontologyTermId": term_id,
        "version": version,
        "documentationLinks": [
            {
                "URL": f"https://cropontology.org/term/{term_id}",
                "type": "OBO",
            }
        ],
    }


def _assert_ontology_reference(payload: dict, term_id: str, version: str = "v2.1") -> None:
    ontology = payload["ontologyReference"]
    assert ontology["ontologyDbId"] == "CO_320"
    assert ontology["ontologyName"] == "Rice Ontology"
    assert ontology["ontologyTermId"] == term_id
    assert ontology["version"] == version
    assert ontology["documentationLinks"] == [
        {
            "URL": f"https://cropontology.org/term/{term_id}",
            "type": "OBO",
        }
    ]


@pytest.mark.asyncio
async def test_variable_create_update_and_get_preserve_ontology_reference(
    async_db_session: AsyncSession,
    test_user,
):
    created = await create_variable(
        VariableCreate(
            observationVariableName="Grain Yield",
            commonCropName="Rice",
            traitName="Grain Yield",
            ontologyReference=_ontology_reference("CO_320:0000001"),
        ),
        db=async_db_session,
        current_user=_current_user(test_user),
    )

    result = created["result"]
    variable_id = result["observationVariableDbId"]
    _assert_ontology_reference(result, "CO_320:0000001")

    stored = await async_db_session.scalar(
        select(ObservationVariable).where(
            ObservationVariable.observation_variable_db_id == variable_id
        )
    )
    assert stored is not None
    assert stored.ontology_term_id == "CO_320:0000001"
    assert stored.ontology_version == "v2.1"

    updated = await update_variable(
        variable_id,
        VariableUpdate(
            ontologyReference=_ontology_reference("CO_320:0000002", version="v2.2"),
        ),
        db=async_db_session,
        current_user=_current_user(test_user),
    )
    _assert_ontology_reference(updated["result"], "CO_320:0000002", version="v2.2")

    fetched = await get_variable(
        variable_id,
        db=async_db_session,
        current_user=_current_user(test_user),
    )
    _assert_ontology_reference(fetched["result"], "CO_320:0000002", version="v2.2")


@pytest.mark.asyncio
async def test_trait_create_update_and_get_preserve_ontology_reference(
    async_db_session: AsyncSession,
    test_user,
):
    created = await create_trait(
        TraitCreate(
            observationVariableName="Days to Flowering",
            traitName="Days to Flowering",
            traitClass="phenological",
            ontologyReference=_ontology_reference("CO_320:0000003"),
        ),
        db=async_db_session,
        current_user=_current_user(test_user),
    )

    result = created["result"]
    trait_id = result["observationVariableDbId"]
    _assert_ontology_reference(result, "CO_320:0000003")

    updated = await update_trait(
        trait_id,
        TraitCreate(
            observationVariableName="Days to Flowering",
            traitName="Days to Flowering",
            traitClass="phenological",
            ontologyReference=_ontology_reference("CO_320:0000004", version="v2.2"),
        ),
        db=async_db_session,
        current_user=_current_user(test_user),
    )
    _assert_ontology_reference(updated["result"], "CO_320:0000004", version="v2.2")

    fetched = await get_trait(
        trait_id,
        db=async_db_session,
        current_user=_current_user(test_user),
    )
    _assert_ontology_reference(fetched["result"], "CO_320:0000004", version="v2.2")
