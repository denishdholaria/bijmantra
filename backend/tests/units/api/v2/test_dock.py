"""
Unit tests for Dock Persistence API
Tests for Mahasarthi navigation dock endpoints

@see backend/app/api/v2/dock.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from fastapi import HTTPException
from app.api.v2.dock import (
    get_dock_state,
    update_dock_state,
    pin_item,
    unpin_item,
    reorder_pinned,
    record_visit,
    clear_recent,
    update_preferences,
    get_default_dock_for_role,
    reset_dock_to_defaults,
    PinItemRequest,
    RecordVisitRequest,
    UpdateDockRequest,
    DockItem,
    DockPreferences,
    DEFAULT_DOCKS,
)
from app.models.core import User
from app.models.user_management import UserDockPreference


class TestDockApi:
    """Test suite for Dock Persistence API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for db and user dependencies for each test."""
        self.mock_db = AsyncMock()
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = 1
        self.mock_user.organization_id = 1
        self.mock_user.email = "test@bijmantra.org"

        # Mock database execution results
        self.mock_execute = self.mock_db.execute
        self.mock_scalar_one_or_none = MagicMock()
        self.mock_execute.return_value.scalar_one_or_none = self.mock_scalar_one_or_none


    # ============================================
    # GET /dock - Get Dock State Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_get_dock_state_returns_defaults_for_new_user(self):
        """Test that a new user without preferences gets default dock items."""
        # Arrange - User exists but no dock preferences
        self.mock_scalar_one_or_none.side_effect = [self.mock_user, None]

        # Act
        response = await get_dock_state(user_id=1, db=self.mock_db)

        # Assert
        assert response["status"] == "success"
        data = response["data"]
        assert data["userId"] == 1
        assert len(data["pinnedItems"]) == len(DEFAULT_DOCKS["default"])
        assert data["recentItems"] == []
        assert data["preferences"]["maxPinned"] == 8
        assert data["preferences"]["maxRecent"] == 4

    @pytest.mark.asyncio
    async def test_get_dock_state_returns_existing_preferences(self):
        """Test that existing dock preferences are returned correctly."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.user_id = 1
        mock_dock_prefs.pinned_items = [
            {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard", "isPinned": True}
        ]
        mock_dock_prefs.recent_items = [
            {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat", "isPinned": False}
        ]
        mock_dock_prefs.max_pinned = 10
        mock_dock_prefs.max_recent = 5
        mock_dock_prefs.show_labels = True
        mock_dock_prefs.compact_mode = False
        mock_dock_prefs.updated_at = datetime.now(timezone.utc)

        self.mock_scalar_one_or_none.side_effect = [self.mock_user, mock_dock_prefs]

        # Act
        response = await get_dock_state(user_id=1, db=self.mock_db)

        # Assert
        assert response["status"] == "success"
        data = response["data"]
        assert data["userId"] == 1
        assert len(data["pinnedItems"]) == 1
        assert data["pinnedItems"][0]["path"] == "/dashboard"
        assert len(data["recentItems"]) == 1
        assert data["preferences"]["maxPinned"] == 10
        assert data["preferences"]["showLabels"] is True

    @pytest.mark.asyncio
    async def test_get_dock_state_user_not_found(self):
        """Test that 404 is returned when user doesn't exist."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await get_dock_state(user_id=999, db=self.mock_db)
        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail


    # ============================================
    # PUT /dock - Update Dock State Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_update_dock_state_creates_new_preferences(self):
        """Test that dock state is created for user without existing preferences."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None  # No existing preferences
        
        update_data = UpdateDockRequest(
            pinnedItems=[
                DockItem(id="dashboard", path="/dashboard", label="Dashboard", icon="LayoutDashboard", isPinned=True)
            ],
            recentItems=[],
            preferences=DockPreferences(maxPinned=8, maxRecent=4, showLabels=False, compactMode=False)
        )

        # Mock refresh to set updated_at
        async def mock_refresh(obj):
            obj.updated_at = datetime.now(timezone.utc)
        self.mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Act
        response = await update_dock_state(
            data=update_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Dock state updated"
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_dock_state_updates_existing_preferences(self):
        """Test that existing dock preferences are updated correctly."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = []
        mock_dock_prefs.updated_at = datetime.now(timezone.utc)
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        update_data = UpdateDockRequest(
            pinnedItems=[
                DockItem(id="trials", path="/trials", label="Trials", icon="FlaskConical", isPinned=True)
            ],
            preferences=DockPreferences(maxPinned=12, showLabels=True)
        )

        async def mock_refresh(obj):
            obj.updated_at = datetime.now(timezone.utc)
        self.mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Act
        response = await update_dock_state(
            data=update_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert mock_dock_prefs.max_pinned == 12
        assert mock_dock_prefs.show_labels is True
        self.mock_db.commit.assert_called_once()


    # ============================================
    # POST /dock/pin - Pin Item Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_pin_item_success(self):
        """Test successfully pinning a new item."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = [
            {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat"}
        ]
        mock_dock_prefs.max_pinned = 8
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        pin_data = PinItemRequest(
            id="programs",
            path="/programs",
            label="Programs",
            icon="Wheat"
        )

        # Act
        response = await pin_item(
            data=pin_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Item pinned"
        assert len(mock_dock_prefs.pinned_items) == 1
        # Item should be removed from recent
        assert len(mock_dock_prefs.recent_items) == 0
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_pin_item_already_pinned(self):
        """Test that pinning an already pinned item returns success without changes."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat"}
        ]
        mock_dock_prefs.recent_items = []
        mock_dock_prefs.max_pinned = 8
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        pin_data = PinItemRequest(
            id="programs",
            path="/programs",
            label="Programs",
            icon="Wheat"
        )

        # Act
        response = await pin_item(
            data=pin_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Item already pinned"

    @pytest.mark.asyncio
    async def test_pin_item_max_limit_reached(self):
        """Test that pinning fails when max pinned limit is reached."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": f"item{i}", "path": f"/item{i}", "label": f"Item {i}", "icon": "Icon"}
            for i in range(8)
        ]
        mock_dock_prefs.recent_items = []
        mock_dock_prefs.max_pinned = 8
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        pin_data = PinItemRequest(
            id="new-item",
            path="/new-item",
            label="New Item",
            icon="Plus"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await pin_item(
                data=pin_data,
                user_id=1,
                organization_id=1,
                db=self.mock_db
            )
        assert exc.value.status_code == 400
        assert "Maximum pinned items (8) reached" in exc.value.detail

    @pytest.mark.asyncio
    async def test_pin_item_creates_preferences_if_not_exist(self):
        """Test that pinning creates dock preferences for new user.
        
        Note: This test verifies that when no dock preferences exist,
        the code creates a new UserDockPreference. The actual model
        has default=8 for max_pinned, but since we're not persisting
        to a real database, we need to mock the object creation behavior.
        """
        # Arrange - Create a mock that simulates a newly created UserDockPreference
        # with default values (as would happen after db.add and before commit)
        new_dock_prefs = MagicMock(spec=UserDockPreference)
        new_dock_prefs.pinned_items = []
        new_dock_prefs.recent_items = []
        new_dock_prefs.max_pinned = 8  # Default value from model
        
        # First call returns None (no existing prefs), subsequent calls return the new object
        self.mock_scalar_one_or_none.return_value = None
        
        # Mock db.add to capture the created object and set its defaults
        def mock_add(obj):
            # Simulate SQLAlchemy setting defaults when object is added
            if hasattr(obj, 'max_pinned') and obj.max_pinned is None:
                obj.max_pinned = 8
            if hasattr(obj, 'max_recent') and obj.max_recent is None:
                obj.max_recent = 4
        self.mock_db.add = MagicMock(side_effect=mock_add)

        pin_data = PinItemRequest(
            id="dashboard",
            path="/dashboard",
            label="Dashboard",
            icon="LayoutDashboard"
        )

        # Act
        response = await pin_item(
            data=pin_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()


    # ============================================
    # DELETE /dock/pin - Unpin Item Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_unpin_item_success(self):
        """Test successfully unpinning an item."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard"},
            {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat"}
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act
        response = await unpin_item(
            path="/dashboard",
            user_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Item unpinned"
        assert len(mock_dock_prefs.pinned_items) == 1
        assert mock_dock_prefs.pinned_items[0]["path"] == "/programs"
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_unpin_item_no_preferences(self):
        """Test unpinning when user has no dock preferences."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        # Act
        response = await unpin_item(
            path="/dashboard",
            user_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "No dock preferences found"

    @pytest.mark.asyncio
    async def test_unpin_item_not_in_pinned(self):
        """Test unpinning an item that isn't pinned."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "dashboard", "path": "/dashboard", "label": "Dashboard", "icon": "LayoutDashboard"}
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act
        response = await unpin_item(
            path="/nonexistent",
            user_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        # Pinned items unchanged
        assert len(mock_dock_prefs.pinned_items) == 1


    # ============================================
    # POST /dock/reorder - Reorder Pinned Items Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_reorder_pinned_success(self):
        """Test successfully reordering pinned items."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "item0", "path": "/item0", "label": "Item 0", "icon": "Icon"},
            {"id": "item1", "path": "/item1", "label": "Item 1", "icon": "Icon"},
            {"id": "item2", "path": "/item2", "label": "Item 2", "icon": "Icon"},
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act - Move item from index 0 to index 2
        response = await reorder_pinned(
            from_index=0,
            to_index=2,
            user_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Items reordered"
        # After moving item0 from 0 to 2: [item1, item2, item0]
        assert mock_dock_prefs.pinned_items[0]["id"] == "item1"
        assert mock_dock_prefs.pinned_items[2]["id"] == "item0"
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reorder_pinned_invalid_from_index(self):
        """Test that invalid from_index raises 400 error."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "item0", "path": "/item0", "label": "Item 0", "icon": "Icon"},
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await reorder_pinned(
                from_index=5,  # Invalid - out of bounds
                to_index=0,
                user_id=1,
                db=self.mock_db
            )
        assert exc.value.status_code == 400
        assert "Invalid from_index" in exc.value.detail

    @pytest.mark.asyncio
    async def test_reorder_pinned_invalid_to_index(self):
        """Test that invalid to_index raises 400 error."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "item0", "path": "/item0", "label": "Item 0", "icon": "Icon"},
            {"id": "item1", "path": "/item1", "label": "Item 1", "icon": "Icon"},
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await reorder_pinned(
                from_index=0,
                to_index=10,  # Invalid - out of bounds
                user_id=1,
                db=self.mock_db
            )
        assert exc.value.status_code == 400
        assert "Invalid to_index" in exc.value.detail

    @pytest.mark.asyncio
    async def test_reorder_pinned_negative_index(self):
        """Test that negative indices raise 400 error."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "item0", "path": "/item0", "label": "Item 0", "icon": "Icon"},
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await reorder_pinned(
                from_index=-1,
                to_index=0,
                user_id=1,
                db=self.mock_db
            )
        assert exc.value.status_code == 400
        assert "Invalid from_index" in exc.value.detail

    @pytest.mark.asyncio
    async def test_reorder_pinned_no_preferences(self):
        """Test that reordering fails when no dock preferences exist."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await reorder_pinned(
                from_index=0,
                to_index=1,
                user_id=1,
                db=self.mock_db
            )
        assert exc.value.status_code == 404
        assert "No dock preferences found" in exc.value.detail


    # ============================================
    # POST /dock/visit - Record Visit Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_record_visit_adds_to_recent(self):
        """Test that visiting a page adds it to recent items."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = []
        mock_dock_prefs.max_recent = 4
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        visit_data = RecordVisitRequest(
            id="programs",
            path="/programs",
            label="Programs",
            icon="Wheat"
        )

        # Act
        response = await record_visit(
            data=visit_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Visit recorded"
        assert len(mock_dock_prefs.recent_items) == 1
        assert mock_dock_prefs.recent_items[0]["path"] == "/programs"
        assert mock_dock_prefs.recent_items[0]["visitCount"] == 1
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_visit_does_not_add_if_pinned(self):
        """Test that visiting a pinned page doesn't add to recent."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat"}
        ]
        mock_dock_prefs.recent_items = []
        mock_dock_prefs.max_recent = 4
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        visit_data = RecordVisitRequest(
            id="programs",
            path="/programs",
            label="Programs",
            icon="Wheat"
        )

        # Act
        response = await record_visit(
            data=visit_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert "pinned" in response["message"].lower()
        assert len(mock_dock_prefs.recent_items) == 0

    @pytest.mark.asyncio
    async def test_record_visit_updates_existing_recent(self):
        """Test that revisiting a page updates its visit count and moves to front."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = [
            {"id": "other", "path": "/other", "label": "Other", "icon": "Icon", "visitCount": 1},
            {"id": "programs", "path": "/programs", "label": "Programs", "icon": "Wheat", "visitCount": 2}
        ]
        mock_dock_prefs.max_recent = 4
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        visit_data = RecordVisitRequest(
            id="programs",
            path="/programs",
            label="Programs",
            icon="Wheat"
        )

        # Act
        response = await record_visit(
            data=visit_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        # Programs should now be first with incremented visit count
        assert mock_dock_prefs.recent_items[0]["path"] == "/programs"
        assert mock_dock_prefs.recent_items[0]["visitCount"] == 3

    @pytest.mark.asyncio
    async def test_record_visit_trims_to_max_recent(self):
        """Test that recent items are trimmed to max_recent limit."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = [
            {"id": f"item{i}", "path": f"/item{i}", "label": f"Item {i}", "icon": "Icon", "visitCount": 1}
            for i in range(4)
        ]
        mock_dock_prefs.max_recent = 4
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        visit_data = RecordVisitRequest(
            id="new-item",
            path="/new-item",
            label="New Item",
            icon="Plus"
        )

        # Act
        response = await record_visit(
            data=visit_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        # Should still be max 4 items
        assert len(mock_dock_prefs.recent_items) == 4
        # New item should be first
        assert mock_dock_prefs.recent_items[0]["path"] == "/new-item"

    @pytest.mark.asyncio
    async def test_record_visit_creates_preferences_if_not_exist(self):
        """Test that visiting creates dock preferences for new user."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        visit_data = RecordVisitRequest(
            id="dashboard",
            path="/dashboard",
            label="Dashboard",
            icon="LayoutDashboard"
        )

        # Act
        response = await record_visit(
            data=visit_data,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()


    # ============================================
    # DELETE /dock/recent - Clear Recent Items Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_clear_recent_success(self):
        """Test successfully clearing recent items."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.recent_items = [
            {"id": "item1", "path": "/item1", "label": "Item 1", "icon": "Icon"},
            {"id": "item2", "path": "/item2", "label": "Item 2", "icon": "Icon"},
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act
        response = await clear_recent(user_id=1, db=self.mock_db)

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Recent items cleared"
        assert mock_dock_prefs.recent_items == []
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_recent_no_preferences(self):
        """Test clearing recent when no dock preferences exist."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        # Act
        response = await clear_recent(user_id=1, db=self.mock_db)

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Recent items cleared"
        # No commit should happen since there's nothing to clear
        self.mock_db.commit.assert_not_called()


    # ============================================
    # PATCH /dock/preferences - Update Preferences Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_update_preferences_success(self):
        """Test successfully updating dock preferences."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.max_pinned = 8
        mock_dock_prefs.max_recent = 4
        mock_dock_prefs.show_labels = False
        mock_dock_prefs.compact_mode = False
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        new_prefs = DockPreferences(
            maxPinned=12,
            maxRecent=6,
            showLabels=True,
            compactMode=True
        )

        # Act
        response = await update_preferences(
            data=new_prefs,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["message"] == "Preferences updated"
        assert mock_dock_prefs.max_pinned == 12
        assert mock_dock_prefs.max_recent == 6
        assert mock_dock_prefs.show_labels is True
        assert mock_dock_prefs.compact_mode is True
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_preferences_creates_if_not_exist(self):
        """Test that updating preferences creates dock preferences for new user."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        new_prefs = DockPreferences(
            maxPinned=10,
            maxRecent=5,
            showLabels=True,
            compactMode=False
        )

        # Act
        response = await update_preferences(
            data=new_prefs,
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()


    # ============================================
    # GET /dock/defaults/{role} - Get Role Defaults Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_get_default_dock_for_valid_role(self):
        """Test getting default dock for a valid role."""
        # Act
        response = await get_default_dock_for_role(role="breeder")

        # Assert
        assert response["status"] == "success"
        assert response["data"]["role"] == "breeder"
        assert len(response["data"]["items"]) == len(DEFAULT_DOCKS["breeder"])
        # Verify first item matches expected breeder default
        assert response["data"]["items"][0]["path"] == "/dashboard"

    @pytest.mark.asyncio
    async def test_get_default_dock_for_seed_company(self):
        """Test getting default dock for seed_company role."""
        # Act
        response = await get_default_dock_for_role(role="seed_company")

        # Assert
        assert response["status"] == "success"
        assert response["data"]["role"] == "seed_company"
        # Seed company should have seed operations pages
        paths = [item["path"] for item in response["data"]["items"]]
        assert "/seed-operations/samples" in paths

    @pytest.mark.asyncio
    async def test_get_default_dock_for_genebank_curator(self):
        """Test getting default dock for genebank_curator role."""
        # Act
        response = await get_default_dock_for_role(role="genebank_curator")

        # Assert
        assert response["status"] == "success"
        assert response["data"]["role"] == "genebank_curator"
        # Genebank curator should have seed bank pages
        paths = [item["path"] for item in response["data"]["items"]]
        assert "/seed-bank/vault" in paths

    @pytest.mark.asyncio
    async def test_get_default_dock_for_researcher(self):
        """Test getting default dock for researcher role."""
        # Act
        response = await get_default_dock_for_role(role="researcher")

        # Assert
        assert response["status"] == "success"
        assert response["data"]["role"] == "researcher"
        # Researcher should have genomics/research pages
        paths = [item["path"] for item in response["data"]["items"]]
        assert "/genomic-selection" in paths

    @pytest.mark.asyncio
    async def test_get_default_dock_for_invalid_role_falls_back(self):
        """Test that invalid role falls back to default dock."""
        # Act
        response = await get_default_dock_for_role(role="nonexistent_role")

        # Assert
        assert response["status"] == "success"
        assert response["data"]["role"] == "default"
        assert len(response["data"]["items"]) == len(DEFAULT_DOCKS["default"])

    @pytest.mark.asyncio
    async def test_get_default_dock_items_are_pinned(self):
        """Test that all default dock items have isPinned=True."""
        # Act
        response = await get_default_dock_for_role(role="breeder")

        # Assert
        for item in response["data"]["items"]:
            assert item["isPinned"] is True


    # ============================================
    # POST /dock/reset - Reset to Defaults Tests
    # ============================================

    @pytest.mark.asyncio
    async def test_reset_dock_to_defaults_success(self):
        """Test successfully resetting dock to role defaults."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = [
            {"id": "custom", "path": "/custom", "label": "Custom", "icon": "Star"}
        ]
        mock_dock_prefs.recent_items = [
            {"id": "recent", "path": "/recent", "label": "Recent", "icon": "Clock"}
        ]
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act
        response = await reset_dock_to_defaults(
            role="breeder",
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert "breeder" in response["message"]
        assert len(mock_dock_prefs.pinned_items) == len(DEFAULT_DOCKS["breeder"])
        assert mock_dock_prefs.recent_items == []
        # Commit called twice: once for dock update, once for activity log
        assert self.mock_db.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_reset_dock_creates_preferences_if_not_exist(self):
        """Test that reset creates dock preferences for new user."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        # Act
        response = await reset_dock_to_defaults(
            role="researcher",
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert "researcher" in response["message"]
        self.mock_db.add.assert_called()  # Called for both dock prefs and activity log

    @pytest.mark.asyncio
    async def test_reset_dock_with_invalid_role_uses_default(self):
        """Test that reset with invalid role uses default dock."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = []
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act
        response = await reset_dock_to_defaults(
            role="invalid_role",
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        # Should use default dock items
        assert len(mock_dock_prefs.pinned_items) == len(DEFAULT_DOCKS["default"])

    @pytest.mark.asyncio
    async def test_reset_dock_logs_activity(self):
        """Test that reset logs an activity entry."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = []
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act
        response = await reset_dock_to_defaults(
            role="breeder",
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        # db.add should be called for activity log
        add_calls = self.mock_db.add.call_args_list
        # At least one call should be for ActivityLog
        assert len(add_calls) >= 1

    @pytest.mark.asyncio
    async def test_reset_dock_returns_pinned_count(self):
        """Test that reset returns the count of pinned items."""
        # Arrange
        mock_dock_prefs = MagicMock(spec=UserDockPreference)
        mock_dock_prefs.pinned_items = []
        mock_dock_prefs.recent_items = []
        self.mock_scalar_one_or_none.return_value = mock_dock_prefs

        # Act
        response = await reset_dock_to_defaults(
            role="seed_company",
            user_id=1,
            organization_id=1,
            db=self.mock_db
        )

        # Assert
        assert response["status"] == "success"
        assert response["data"]["pinnedCount"] == len(DEFAULT_DOCKS["seed_company"])

