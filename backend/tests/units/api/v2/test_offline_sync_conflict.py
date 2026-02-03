import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.offline_sync import resolve_conflict
from app.models.collaboration import SyncItem, SyncStatus
from app.models.core import Trial, User


@pytest.mark.asyncio
class TestResolveConflict:
    """Unit tests for the resolve_conflict endpoint logic."""

    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Set up mocks for each test."""
        self.db = AsyncMock(spec=AsyncSession)
        self.current_user = User(id=1, organization_id=1)
        self.sync_item = SyncItem(
            id=101,
            user_id=1,
            entity_type="Trial",
            entity_id="1",
            local_data={"trial_name": "Client Name"},
            status=SyncStatus.CONFLICT,
        )

        # Mock the database result object
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.sync_item
        # Configure the awaitable db.execute to return the mock_result
        self.db.execute.return_value = mock_result

    async def test_setup_is_correct(self):
        """Sanity check to ensure the test setup is working as expected."""
        assert self.db is not None
        assert self.current_user is not None
        assert self.sync_item is not None
        assert self.sync_item.status == SyncStatus.CONFLICT

    @patch("app.api.v2.offline_sync.get_model_class", return_value=Trial)
    async def test_resolve_conflict_server_wins(self, mock_get_model):
        """Test the 'server_wins' resolution strategy."""
        # Act
        result = await resolve_conflict(
            item_id=self.sync_item.id,
            resolution="server_wins",
            db=self.db,
            current_user=self.current_user,
        )

        # Assert
        mock_get_model.assert_called_once_with("Trial")
        assert self.sync_item.status == SyncStatus.SYNCED
        assert self.sync_item.error_message == "Resolved: Server wins"
        self.db.commit.assert_awaited_once()
        assert result["success"] is True
        assert result["resolution"] == "server_wins"

    @patch("app.api.v2.offline_sync.get_model_class", return_value=Trial)
    async def test_resolve_conflict_client_wins_updates_existing(self, mock_get_model):
        """Test 'client_wins' when the server record exists."""
        # Arrange
        existing_trial = Trial(id=1, trial_name="Server Name")
        self.db.get.return_value = existing_trial
        self.sync_item.local_data = {"trial_name": "Updated Client Name"}

        # Act
        await resolve_conflict(
            item_id=self.sync_item.id,
            resolution="client_wins",
            db=self.db,
            current_user=self.current_user,
        )

        # Assert
        self.db.get.assert_awaited_once_with(Trial, 1)
        assert existing_trial.trial_name == "Updated Client Name"
        assert self.sync_item.status == SyncStatus.SYNCED
        self.db.commit.assert_awaited_once()

    @patch("app.api.v2.offline_sync.get_model_class", return_value=Trial)
    async def test_resolve_conflict_client_wins_creates_new(self, mock_get_model):
        """Test 'client_wins' when the server record does not exist."""
        # Arrange
        self.db.get.return_value = None
        self.sync_item.local_data = {
            "trial_name": "New Trial",
            "organization_id": 1,
            "program_id": 1,
        }

        # Act
        await resolve_conflict(
            item_id=self.sync_item.id,
            resolution="client_wins",
            db=self.db,
            current_user=self.current_user,
        )

        # Assert
        self.db.add.assert_called_once()
        added_object = self.db.add.call_args[0][0]
        assert isinstance(added_object, Trial)
        assert added_object.trial_name == "New Trial"
        assert self.sync_item.status == SyncStatus.SYNCED
        self.db.commit.assert_awaited_once()

    @patch("app.api.v2.offline_sync.get_model_class", return_value=Trial)
    async def test_resolve_conflict_merge_simple_fields(self, mock_get_model):
        """Test 'merge' strategy for simple scalar fields."""
        # Arrange
        existing_trial = Trial(
            id=1,
            trial_name="Server Name",
            trial_description="Original Description",
        )
        self.db.get.return_value = existing_trial
        self.sync_item.local_data = {"trial_name": "Merged Client Name"}

        # Act
        await resolve_conflict(
            item_id=self.sync_item.id,
            resolution="merge",
            db=self.db,
            current_user=self.current_user,
        )

        # Assert
        assert existing_trial.trial_name == "Merged Client Name"
        assert existing_trial.trial_description == "Original Description"
        assert self.sync_item.status == SyncStatus.SYNCED
        self.db.commit.assert_awaited_once()

    @patch("app.api.v2.offline_sync.get_model_class", return_value=Trial)
    async def test_resolve_conflict_merge_deep_merge_json(self, mock_get_model):
        """Test 'merge' strategy for deep merging JSON fields."""
        # Arrange
        existing_trial = Trial(
            id=1,
            trial_name="Server Name",
            additional_info={"a": 1, "b": {"c": 2}},
        )
        self.db.get.return_value = existing_trial
        self.sync_item.local_data = {
            "additional_info": {"b": {"d": 3}, "e": 4}
        }

        # Act
        await resolve_conflict(
            item_id=self.sync_item.id,
            resolution="merge",
            db=self.db,
            current_user=self.current_user,
        )

        # Assert
        assert existing_trial.additional_info == {
            "a": 1,
            "b": {"c": 2, "d": 3},
            "e": 4,
        }
        assert self.sync_item.status == SyncStatus.SYNCED
        self.db.commit.assert_awaited_once()

    @patch("app.api.v2.offline_sync.get_model_class", return_value=Trial)
    async def test_resolve_conflict_unknown_strategy_raises_error(self, mock_get_model):
        """Test that an unknown resolution strategy raises an HTTPException."""
        # Assert
        with pytest.raises(HTTPException) as exc_info:
            await resolve_conflict(
                item_id=self.sync_item.id,
                resolution="unknown_strategy",
                db=self.db,
                current_user=self.current_user,
            )
        assert exc_info.value.status_code == 400
        assert "Unknown resolution strategy" in exc_info.value.detail
