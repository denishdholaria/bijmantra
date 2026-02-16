
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
import uuid

from app.api.brapi.germplasm import (
    list_germplasm,
    get_germplasm,
    create_germplasm,
    update_germplasm,
    GermplasmCreate,  # Import the actual Pydantic model
)
from app.models.germplasm import Germplasm as GermplasmModel
from app.models.core import User

# Mock the dependencies
mock_db = AsyncMock()
mock_user = User(id=1, organization_id=1, full_name="Test User", email="test@example.com")

# Fixture for the mock database
@pytest.fixture
def db():
    return mock_db

# Fixture for the mock user
@pytest.fixture
def current_user():
    return mock_user

# Auto-patch the dependency functions
@pytest.fixture(autouse=True)
def auto_patch_deps():
    with patch('app.api.brapi.germplasm.get_db', return_value=mock_db), \
         patch('app.api.brapi.germplasm.get_current_user', return_value=mock_user), \
         patch('app.api.brapi.germplasm.get_optional_user', return_value=mock_user):
        yield

# Reset mocks before each test
@pytest.fixture(autouse=True)
def reset_mocks():
    mock_db.reset_mock()
    # Resetting the execute mock to be a fresh AsyncMock for each test
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()


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

    mock_db.execute.side_effect = [mock_count_result, mock_data_result]

    # Call the endpoint function
    result = await list_germplasm(page=0, pageSize=10, db=mock_db, current_user=mock_user)

    # Assertions
    assert result['metadata']['pagination']['totalCount'] == 2
    assert len(result['result']['data']) == 2
    assert result['result']['data'][0]['germplasmDbId'] == "test_id_1"
    assert result['result']['data'][1]['germplasmName'] == "Test Germplasm 2"
    
    # Check that the query was called with offset and limit
    query_str = str(mock_db.execute.call_args_list[1].args[0])
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

    mock_db.execute.side_effect = [mock_count_result, mock_data_result]

    # Call the endpoint function with specific page and pageSize
    result = await list_germplasm(page=1, pageSize=5, db=mock_db, current_user=mock_user)

    # Assertions
    assert result['metadata']['pagination']['currentPage'] == 1
    assert result['metadata']['pagination']['pageSize'] == 5
    
    query_str = str(mock_db.execute.call_args_list[1].args[0])
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
    mock_db.execute.return_value = mock_result

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
    mock_db.execute.return_value = mock_result

    # Call the endpoint function and expect an HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await get_germplasm(germplasmDbId="not_found_id", db=mock_db, current_user=mock_user)

    # Assertions
    assert excinfo.value.status_code == 404


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
    with patch('uuid.uuid4') as mock_uuid:
        mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')
        result = await create_germplasm(germplasm=germplasm_data, db=mock_db, current_user=mock_user)

    # Assertions
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    created_germplasm = mock_db.add.call_args[0][0]
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
    mock_db.execute.return_value = mock_result

    # New data using the correct model
    update_data = GermplasmCreate(
        germplasmName="Updated Name",
        accessionNumber="ACC456"
    )

    # Call the endpoint function
    result = await update_germplasm(germplasmDbId="test_id_1", germplasm=update_data, db=mock_db, current_user=mock_user)

    # Assertions
    mock_db.commit.assert_called_once()
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
    mock_db.execute.return_value = mock_result

    # New data
    update_data = GermplasmCreate(germplasmName="Updated Name")

    # Call the endpoint function and expect an HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await update_germplasm(germplasmDbId="not_found_id", germplasm=update_data, db=mock_db, current_user=mock_user)

    # Assertions
    assert excinfo.value.status_code == 404
