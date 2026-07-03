import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.brapi.v2.germplasm import (
    GermplasmCreate,
    create_germplasm,
    delete_germplasm,
    get_germplasm,
    list_germplasm,
    update_germplasm,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.api.access import (
    ACCESSION_PASSPORT_CAPABILITY_ID,
)
from app.models.germplasm import Germplasm as GermplasmModel

from .support import (
    capability_installation_absent_result as _capability_installation_absent_result,
)
from .support import mock_db, mock_user


@pytest.mark.asyncio
async def test_list_germplasm():
    """Test GET /germplasm endpoint with pagination."""
    # Mock data
    mock_germplasm_1 = GermplasmModel(
        id=1,
        germplasm_db_id="test_id_1",
        germplasm_name="Test Germplasm 1",
        default_display_name="Test 1",
        synonyms=[],
        additional_info={},
        external_references=[]
    )
    mock_germplasm_2 = GermplasmModel(
        id=2,
        germplasm_db_id="test_id_2",
        germplasm_name="Test Germplasm 2",
        default_display_name="Test 2",
        synonyms=[],
        additional_info={},
        external_references=[]
    )
    mock_germplasm_list = [mock_germplasm_1, mock_germplasm_2]

    # Mock the return value of db.execute for count and data queries
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 2

    mock_data_result = MagicMock()
    mock_data_result.scalars().all.return_value = mock_germplasm_list

    mock_db.execute.side_effect = [_capability_installation_absent_result(), mock_count_result, mock_data_result]

    # Call the endpoint function
    result = await list_germplasm(page=0, pageSize=10, db=mock_db, current_user=mock_user)

    # Assertions
    assert result['metadata']['pagination']['totalCount'] == 2
    assert len(result['result']['data']) == 2
    assert result['result']['data'][0]['germplasmDbId'] == "test_id_1"
    assert result['result']['data'][1]['germplasmName'] == "Test Germplasm 2"

    # Check that the query was called with offset and limit
    query_str = str(mock_db.execute.call_args_list[2].args[0])
    assert "LIMIT" in query_str.upper()
    assert "OFFSET" in query_str.upper()

@pytest.mark.asyncio
async def test_list_germplasm_pagination():
    """Test GET /germplasm endpoint with specific pagination."""
    # Mock data
    mock_germplasm_1 = GermplasmModel(
        id=1,
        germplasm_db_id="test_id_1",
        germplasm_name="Test Germplasm 1",
        default_display_name="Test 1",
        synonyms=[],
        additional_info={},
        external_references=[]
    )

    # Mock the return value of db.execute
    mock_count_result = MagicMock()
    mock_count_result.scalar.return_value = 1

    mock_data_result = MagicMock()
    mock_data_result.scalars().all.return_value = [mock_germplasm_1]

    mock_db.execute.side_effect = [_capability_installation_absent_result(), mock_count_result, mock_data_result]

    # Call the endpoint function with specific page and pageSize
    result = await list_germplasm(page=1, pageSize=5, db=mock_db, current_user=mock_user)

    # Assertions
    assert result['metadata']['pagination']['currentPage'] == 1
    assert result['metadata']['pagination']['pageSize'] == 5

    query_str = str(mock_db.execute.call_args_list[2].args[0])
    assert "LIMIT" in query_str.upper()
    assert "OFFSET" in query_str.upper()

@pytest.mark.asyncio
async def test_get_germplasm_by_id():
    """Test GET /germplasm/{germplasmDbId} endpoint."""
    # Mock data
    mock_germplasm = GermplasmModel(
        id=1,
        germplasm_db_id="test_id_1",
        germplasm_name="Test Germplasm",
        default_display_name="Test",
        synonyms=[],
        additional_info={},
        external_references=[]
    )

    # Mock db.execute to return the mock germplasm
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_germplasm
    mock_db.execute.side_effect = [_capability_installation_absent_result(), mock_result]

    # Call the endpoint function
    result = await get_germplasm(germplasmDbId="test_id_1", db=mock_db, current_user=mock_user)

    # Assertions
    assert result['result']['germplasmDbId'] == "test_id_1"
    assert result['result']['germplasmName'] == "Test Germplasm"

@pytest.mark.asyncio
async def test_get_germplasm_not_found():
    """Test GET /germplasm/{germplasmDbId} for 404 response."""
    # Mock db.execute to return None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [_capability_installation_absent_result(), mock_result]

    # Call the endpoint function and expect an HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await get_germplasm(germplasmDbId="not_found_id", db=mock_db, current_user=mock_user)

    # Assertions
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_brapi_germplasm_get_rejects_missing_read_permission_before_lookup():
    """Test GET /germplasm/{id} rejects before DB lookup when read permission is missing."""

    class NoLookupDb:
        pass

    denied_user = SimpleNamespace(
        id=2,
        organization_id=1,
        installed_capabilities=(ACCESSION_PASSPORT_CAPABILITY_ID,),
        permissions=("germplasm.passport.manage",),
        data_scopes=("organization", "accession"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await get_germplasm(
            germplasmDbId="germplasm-denied",
            db=NoLookupDb(),
            current_user=denied_user,
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail["reason"] == "missing_permission"
    assert excinfo.value.detail["missingPermissions"] == ["germplasm.read"]

@pytest.mark.asyncio
async def test_brapi_germplasm_list_rejects_missing_read_permission_before_query():
    """Test GET /germplasm rejects before DB lookup when read permission is missing."""

    class NoQueryDb:
        pass

    denied_user = SimpleNamespace(
        id=2,
        organization_id=1,
        installed_capabilities=(ACCESSION_PASSPORT_CAPABILITY_ID,),
        permissions=("germplasm.passport.manage",),
        data_scopes=("organization", "accession"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await list_germplasm(
            page=0,
            pageSize=10,
            db=NoQueryDb(),
            current_user=denied_user,
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail["reason"] == "missing_permission"
    assert excinfo.value.detail["missingPermissions"] == ["germplasm.read"]

@pytest.mark.asyncio
async def test_create_germplasm():
    """Test POST /germplasm endpoint."""
    # Input data using the correct model
    germplasm_data = GermplasmCreate(
        germplasmName="New Germplasm",
        accessionNumber="ACC123",
        # Add other optional fields as needed or let them default to None
    )

    # Call the endpoint function
    mock_db.execute.return_value = _capability_installation_absent_result()
    with patch('uuid.uuid4') as mock_uuid:
        mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')
        result = await create_germplasm(germplasm=germplasm_data, db=mock_db, current_user=mock_user)

    # Assertions
    assert mock_db.add.call_count == 2  # Germplasm + AuditLog
    mock_db.commit.assert_called()
    mock_db.refresh.assert_called_once()

    # Check that germplasm was added
    germplasm_call = mock_db.add.call_args_list[0]
    created_germplasm = germplasm_call[0][0]
    assert created_germplasm.germplasm_name == "New Germplasm"
    assert created_germplasm.accession_number == "ACC123"
    assert created_germplasm.organization_id == 1
    assert created_germplasm.germplasm_db_id == "germplasm_12345678"

    assert result['result']['germplasmName'] == "New Germplasm"
    assert result['result']['germplasmDbId'] == "germplasm_12345678"

@pytest.mark.asyncio
async def test_update_germplasm():
    """Test PUT /germplasm/{germplasmDbId} endpoint."""
    # Mock existing germplasm
    mock_existing_germplasm = GermplasmModel(
        id=1,
        germplasm_db_id="test_id_1",
        germplasm_name="Old Name",
    )

    # Mock db.execute to return the existing germplasm
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_existing_germplasm
    mock_db.execute.side_effect = [_capability_installation_absent_result(), mock_result]

    # New data using the correct model
    update_data = GermplasmCreate(
        germplasmName="Updated Name",
        accessionNumber="ACC456"
    )

    # Call the endpoint function
    result = await update_germplasm(germplasmDbId="test_id_1", germplasm=update_data, db=mock_db, current_user=mock_user)

    # Assertions
    assert mock_db.commit.call_count == 2  # Update commit + AuditLog commit
    mock_db.refresh.assert_called_once_with(mock_existing_germplasm)
    assert mock_existing_germplasm.germplasm_name == "Updated Name"
    assert mock_existing_germplasm.accession_number == "ACC456"
    assert result['result']['germplasmName'] == "Updated Name"

@pytest.mark.asyncio
async def test_update_germplasm_not_found():
    """Test PUT /germplasm/{germplasmDbId} for 404 response."""
    # Mock db.execute to return None
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [_capability_installation_absent_result(), mock_result]

    # New data
    update_data = GermplasmCreate(germplasmName="Updated Name")

    # Call the endpoint function and expect an HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await update_germplasm(germplasmDbId="not_found_id", germplasm=update_data, db=mock_db, current_user=mock_user)

    # Assertions
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_brapi_germplasm_create_rejects_missing_manage_permission_before_db_mutation():
    """Test POST /germplasm rejects before DB writes when capability permission is missing."""

    class NoMutationDb:
        def add(self, item):
            raise AssertionError("db.add should not be called before access is allowed")

        async def commit(self):
            raise AssertionError("db.commit should not be called before access is allowed")

    denied_user = SimpleNamespace(
        id=2,
        organization_id=1,
        installed_capabilities=(ACCESSION_PASSPORT_CAPABILITY_ID,),
        permissions=("germplasm.read",),
        data_scopes=("organization", "accession"),
    )
    germplasm_data = GermplasmCreate(germplasmName="Denied Germplasm")

    with pytest.raises(HTTPException) as excinfo:
        await create_germplasm(
            germplasm=germplasm_data,
            db=NoMutationDb(),
            current_user=denied_user,
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail["reason"] == "missing_permission"
    assert excinfo.value.detail["missingPermissions"] == ["germplasm.passport.manage"]

@pytest.mark.asyncio
async def test_brapi_germplasm_delete_rejects_missing_manage_permission_before_lookup():
    """Test DELETE /germplasm/{id} rejects before DB lookup when manage permission is missing."""

    class NoLookupDb:
        async def delete(self, item):
            raise AssertionError("db.delete should not be called before access is allowed")

        async def commit(self):
            raise AssertionError("db.commit should not be called before access is allowed")

    denied_user = SimpleNamespace(
        id=2,
        organization_id=1,
        installed_capabilities=(ACCESSION_PASSPORT_CAPABILITY_ID,),
        permissions=("germplasm.read",),
        data_scopes=("organization", "accession"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await delete_germplasm(
            germplasmDbId="germplasm-denied",
            db=NoLookupDb(),
            current_user=denied_user,
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail["reason"] == "missing_permission"
    assert excinfo.value.detail["missingPermissions"] == ["germplasm.passport.manage"]
