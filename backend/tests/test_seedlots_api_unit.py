import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.api.brapi.seedlots import create_transaction, TransactionCreate

@pytest.mark.asyncio
async def test_create_transaction_adds_user_info():
    # Mock the DB session
    mock_db = MagicMock()
    # Mock the async commit and refresh methods
    mock_db.commit = MagicMock()
    # Making these awaitable is tricky with MagicMock without configuring them to return a future
    # But since we are patching the dependencies and probably running the function which is async
    # we need to be careful.

    # Actually, MagicMock supports __await__ in newer versions, or we can use AsyncMock
    from unittest.mock import AsyncMock
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    # Mock the current user
    mock_user = MagicMock()
    mock_user.id = 123
    mock_user.full_name = "Test User"
    mock_user.organization_id = 1

    # Create a request object
    transaction_request = TransactionCreate(
        seedLotDbId="seedlot1",
        amount=10.0,
        transactionDescription="Test transaction"
    )

    # Mock the SeedlotTransaction model
    with patch("app.api.brapi.seedlots.SeedlotTransaction") as MockTransaction:
        # Mock the seedlot lookup
        mock_result = MagicMock()
        mock_scalar = MagicMock()
        mock_scalar.id = 555
        mock_result.scalar_one_or_none.return_value = mock_scalar
        mock_db.execute.return_value = mock_result

        # Call the function
        result = await create_transaction(
            transaction=transaction_request,
            db=mock_db,
            current_user=mock_user
        )

        # Verify SeedlotTransaction was instantiated
        assert MockTransaction.called

        # Get the kwargs passed to the constructor
        call_kwargs = MockTransaction.call_args[1]

        # Verify basic fields
        assert call_kwargs['amount'] == 10.0

        # Verify additionalInfo
        additional_info = call_kwargs.get('additional_info', {})
        assert additional_info.get('user_id') == 123
        assert additional_info.get('user_name') == "Test User"
