import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from app.api.v2.rbac import (
    list_roles,
    create_role,
    get_user_roles,
    assign_role_to_user,
    remove_role_from_user,
    RoleCreate,
    AssignRoleRequest,
)
from app.api.deps import get_current_superuser
from app.models.core import User
from app.models.user_management import Role, UserRole

class TestRbacApi:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """This fixture sets up mocks for db, and user dependencies for each test."""
        self.mock_db = AsyncMock()
        self.mock_user = MagicMock()
        self.mock_user.id = 1
        self.mock_user.organization_id = 1
        self.mock_user.email = "test@user.com"
        self.mock_user.is_superuser = False
        
        self.mock_superuser = MagicMock()
        self.mock_superuser.id = 2
        self.mock_superuser.organization_id = 1
        self.mock_superuser.email = "super@user.com"
        self.mock_superuser.is_superuser = True

        # Mock database execution results
        self.mock_execute = self.mock_db.execute
        self.mock_scalar_one_or_none = MagicMock()
        self.mock_scalars = MagicMock()
        self.mock_execute.return_value.scalar_one_or_none = self.mock_scalar_one_or_none
        self.mock_execute.return_value.scalars = self.mock_scalars

        # Keep a reference to the mocks to modify them in tests
        self.mocks = {
            "db": self.mock_db,
            "user": self.mock_user,
            "superuser": self.mock_superuser,
        }

    # ============================================
    # AUTHORIZATION TESTS
    # ============================================

    @pytest.mark.asyncio
    async def test_get_current_superuser_success(self):
        """Test that a superuser is correctly identified."""
        user = await get_current_superuser(self.mock_superuser)
        assert user == self.mock_superuser

    @pytest.mark.asyncio
    async def test_get_current_superuser_fails_for_regular_user(self):
        """Test that a regular user is blocked."""
        with pytest.raises(HTTPException) as exc:
            await get_current_superuser(self.mock_user)
        assert exc.value.status_code == 403

    # ============================================
    # ENDPOINT LOGIC TESTS
    # ============================================

    @pytest.mark.asyncio
    async def test_list_roles_success(self):
        """Test that a regular user can successfully list roles."""
        # Arrange
        mock_roles = [
            Role(id=1, role_id='admin', name='Admin', permissions=['*:*'], is_system=True, organization_id=1),
            Role(id=2, role_id='viewer', name='Viewer', permissions=['read:*'], is_system=False, organization_id=1)
        ]
        # First call to db.execute fetches the roles
        self.mock_scalars.return_value.all.return_value = mock_roles

        # Subsequent calls to db.execute are for user counts
        mock_count_1 = MagicMock()
        mock_count_1.scalars.return_value.all.return_value = [UserRole(), UserRole()] # 2 users
        mock_count_2 = MagicMock()
        mock_count_2.scalars.return_value.all.return_value = [UserRole()] # 1 user

        self.mock_execute.side_effect = [
            # First call for the roles list
            self.mock_execute.return_value,
            # Second call for the user count of the first role
            mock_count_1,
            # Third call for the user count of the second role
            mock_count_2
        ]

        # Act
        response = await list_roles(db=self.mock_db, current_user=self.mock_user)

        # Assert
        assert len(response) == 2
        assert response[0].role_id == 'admin'
        assert response[0].user_count == 2
        assert response[0].is_system is True
        assert response[1].role_id == 'viewer'
        assert response[1].user_count == 1
        assert response[1].is_system is False
        assert self.mock_execute.call_count == 3

    @pytest.mark.asyncio
    async def test_create_role_success_by_superuser(self):
        """Test that a superuser can create a new role."""
        # Arrange
        role_data = RoleCreate(
            role_id="new_role",
            name="New Role",
            description="A test role",
            permissions=["read:plant_sciences", "write:plant_sciences"]
        )
        self.mock_scalar_one_or_none.return_value = None  # No existing role
        
        # Mock db.refresh to set the id on the role object (simulating DB auto-increment)
        async def mock_refresh(obj):
            obj.id = 99  # Simulate DB-assigned ID
        self.mock_db.refresh = AsyncMock(side_effect=mock_refresh)

        # Act
        response = await create_role(
            role_data=role_data,
            db=self.mock_db,
            current_user=self.mock_superuser
        )

        # Assert
        assert response.role_id == role_data.role_id
        assert response.name == role_data.name
        assert response.is_system is False
        assert response.user_count == 0
        assert response.id == 99  # Verify the mocked ID was used
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_role_fails_on_duplicate_id(self):
        """Test that creating a role with a duplicate role_id fails."""
        # Arrange
        role_data = RoleCreate(role_id="existing_role", name="New Name")
        self.mock_scalar_one_or_none.return_value = Role(id=1, role_id="existing_role", name="Old Name")

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await create_role(
                role_data=role_data,
                db=self.mock_db,
                current_user=self.mock_superuser
            )
        assert exc.value.status_code == 400
        assert "Role ID already exists" in exc.value.detail

    @pytest.mark.asyncio
    async def test_create_role_fails_on_invalid_permissions(self):
        """Test that creating a role with invalid permissions fails."""
        # Arrange
        role_data = RoleCreate(
            role_id="invalid_perm_role",
            name="Invalid Perms",
            permissions=["read:plant_sciences", "fake:permission"]
        )
        self.mock_scalar_one_or_none.return_value = None  # No existing role

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await create_role(
                role_data=role_data,
                db=self.mock_db,
                current_user=self.mock_superuser
            )
        assert exc.value.status_code == 400
        assert "Invalid permissions" in exc.value.detail

    @pytest.mark.asyncio
    async def test_get_user_roles_success(self):
        """Test retrieving roles for a specific user successfully."""
        # Arrange - Use MagicMock to avoid User model validation issues
        target_user = MagicMock()
        target_user.id = 3
        target_user.email = "target@user.com"
        target_user.full_name = "Target User"
        target_user.organization_id = 1
        target_user.is_superuser = False  # Required by UserRoleResponse
        
        # Create mock roles
        mock_role1 = MagicMock()
        mock_role1.id = 1
        mock_role1.role_id = 'admin'
        mock_role1.name = 'Admin'
        mock_role1.description = None
        mock_role1.permissions = ['*:*']
        mock_role1.color = None
        mock_role1.is_system = True
        
        mock_role2 = MagicMock()
        mock_role2.id = 2
        mock_role2.role_id = 'viewer'
        mock_role2.name = 'Viewer'
        mock_role2.description = None
        mock_role2.permissions = ['read:*']
        mock_role2.color = None
        mock_role2.is_system = False
        
        # Create mock user_roles
        mock_ur1 = MagicMock()
        mock_ur1.role = mock_role1
        mock_ur2 = MagicMock()
        mock_ur2.role = mock_role2
        
        target_user.user_roles = [mock_ur1, mock_ur2]
        self.mock_scalar_one_or_none.return_value = target_user

        # Act
        response = await get_user_roles(
            user_id=3,
            db=self.mock_db,
            current_user=self.mock_user
        )

        # Assert
        assert response.user_id == 3
        assert response.email == "target@user.com"
        assert response.is_superuser is False
        assert len(response.roles) == 2
        assert response.roles[0].role_id == 'admin'
        assert response.roles[1].role_id == 'viewer'

    @pytest.mark.asyncio
    async def test_get_user_roles_not_found(self):
        """Test that a 404 is returned when the user is not found."""
        # Arrange
        self.mock_scalar_one_or_none.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await get_user_roles(
                user_id=999,
                db=self.mock_db,
                current_user=self.mock_user
            )
        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_assign_role_success_by_superuser(self):
        """Test that a superuser can successfully assign a role."""
        # Arrange
        request = AssignRoleRequest(user_id=3, role_id="new_role")
        target_user = User(id=3, organization_id=1)
        target_role = Role(id=5, role_id="new_role", organization_id=1)

        # First call to find the user, second to find the role, third to check for existing assignment
        self.mock_scalar_one_or_none.side_effect = [target_user, target_role, None]

        # Act
        response = await assign_role_to_user(
            user_id=3,
            request=request,
            db=self.mock_db,
            current_user=self.mock_superuser
        )

        # Assert
        assert response == {"message": "Role 'new_role' assigned to user"}
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        assert self.mock_scalar_one_or_none.call_count == 3

    @pytest.mark.asyncio
    async def test_assign_role_fails_if_user_not_found(self):
        """Test that assigning a role fails if the target user is not found."""
        # Arrange
        request = AssignRoleRequest(user_id=999, role_id="new_role")
        self.mock_scalar_one_or_none.return_value = None  # User not found

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await assign_role_to_user(
                user_id=999,
                request=request,
                db=self.mock_db,
                current_user=self.mock_superuser
            )
        assert exc.value.status_code == 404
        assert "User not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_assign_role_fails_if_role_not_found(self):
        """Test that assigning a role fails if the role is not found."""
        # Arrange
        request = AssignRoleRequest(user_id=3, role_id="non_existent_role")
        target_user = User(id=3, organization_id=1)

        # First call finds the user, second does not find the role
        self.mock_scalar_one_or_none.side_effect = [target_user, None]

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await assign_role_to_user(
                user_id=3,
                request=request,
                db=self.mock_db,
                current_user=self.mock_superuser
            )
        assert exc.value.status_code == 404
        assert "Role not found" in exc.value.detail

    @pytest.mark.asyncio
    async def test_assign_role_fails_if_already_assigned(self):
        """Test that assigning a role fails if it's already assigned."""
        # Arrange
        request = AssignRoleRequest(user_id=3, role_id="existing_role")
        target_user = User(id=3, organization_id=1)
        target_role = Role(id=5, role_id="existing_role", organization_id=1)
        existing_assignment = UserRole(user_id=3, role_id=5)

        # User found, role found, existing assignment found
        self.mock_scalar_one_or_none.side_effect = [target_user, target_role, existing_assignment]

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await assign_role_to_user(
                user_id=3,
                request=request,
                db=self.mock_db,
                current_user=self.mock_superuser
            )
        assert exc.value.status_code == 400
        assert "Role already assigned to user" in exc.value.detail

    @pytest.mark.asyncio
    async def test_remove_role_success_by_superuser(self):
        """Test that a superuser can successfully remove a role from a user."""
        # Arrange
        target_user = User(id=3, organization_id=1)
        target_role = Role(id=5, role_id="role_to_remove", organization_id=1)
        assignment = UserRole(user_id=3, role_id=5)

        # User found, role found, assignment found
        self.mock_scalar_one_or_none.side_effect = [target_user, target_role, assignment]

        # Act
        response = await remove_role_from_user(
            user_id=3,
            role_id="role_to_remove",
            db=self.mock_db,
            current_user=self.mock_superuser
        )

        # Assert
        assert response == {"message": "Role 'role_to_remove' removed from user"}
        self.mock_db.delete.assert_called_once_with(assignment)
        self.mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_role_fails_if_assignment_not_found(self):
        """Test that removing a role fails if the user does not have that role."""
        # Arrange
        target_user = User(id=3, organization_id=1)
        target_role = Role(id=5, role_id="role_to_remove", organization_id=1)

        # User found, role found, but no assignment
        self.mock_scalar_one_or_none.side_effect = [target_user, target_role, None]

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await remove_role_from_user(
                user_id=3,
                role_id="role_to_remove",
                db=self.mock_db,
                current_user=self.mock_superuser
            )
        assert exc.value.status_code == 404
        assert "Role not assigned to user" in exc.value.detail

    @pytest.mark.asyncio
    async def test_remove_role_fails_if_role_not_found(self):
        """Test that removing a role fails if the role itself is not found."""
        # Arrange
        target_user = User(id=3, organization_id=1)

        # User found, but role is not
        self.mock_scalar_one_or_none.side_effect = [target_user, None]

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await remove_role_from_user(
                user_id=3,
                role_id="non_existent_role",
                db=self.mock_db,
                current_user=self.mock_superuser
            )
        assert exc.value.status_code == 404
        assert "Role not found" in exc.value.detail
