"""Add user_roles association table for RBAC

Revision ID: 022_user_roles_rbac
Revises: 021_devguru_phases_3_4_5
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('granted_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
    )
    
    # Create indexes
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'])
    
    # Add is_system flag to roles table to distinguish system roles from custom
    op.add_column('roles', sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False))
    
    # Seed default system roles
    op.execute("""
        INSERT INTO roles (organization_id, role_id, name, description, permissions, color, is_system, created_at, updated_at)
        SELECT 
            o.id,
            r.role_id,
            r.name,
            r.description,
            r.permissions::jsonb,
            r.color,
            true,
            NOW(),
            NOW()
        FROM organizations o
        CROSS JOIN (VALUES
            ('viewer', 'Viewer', 'Read-only access to data', '["read:plant_sciences","read:seed_bank","read:earth_systems"]', '#6b7280'),
            ('breeder', 'Breeder', 'Can manage breeding programs and trials', '["read:plant_sciences","write:plant_sciences","read:seed_bank","read:earth_systems"]', '#10b981'),
            ('researcher', 'Researcher', 'Full research access including integrations', '["read:plant_sciences","write:plant_sciences","read:seed_bank","write:seed_bank","read:earth_systems","write:earth_systems","read:integrations"]', '#3b82f6'),
            ('data_manager', 'Data Manager', 'Can manage data and integrations', '["read:plant_sciences","write:plant_sciences","admin:plant_sciences","read:seed_bank","write:seed_bank","read:earth_systems","read:integrations","manage:integrations"]', '#8b5cf6'),
            ('admin', 'Administrator', 'Full administrative access', '["read:plant_sciences","write:plant_sciences","admin:plant_sciences","read:seed_bank","write:seed_bank","admin:seed_bank","read:earth_systems","write:earth_systems","read:commercial","write:commercial","read:integrations","manage:integrations","read:users","manage:users","view:audit_log"]', '#ef4444')
        ) AS r(role_id, name, description, permissions, color)
        WHERE NOT EXISTS (
            SELECT 1 FROM roles WHERE roles.organization_id = o.id AND roles.role_id = r.role_id
        )
    """)
    
    # Assign default 'viewer' role to all existing users who don't have roles
    op.execute("""
        INSERT INTO user_roles (user_id, role_id, granted_at)
        SELECT u.id, r.id, NOW()
        FROM users u
        JOIN roles r ON r.organization_id = u.organization_id AND r.role_id = 'viewer'
        WHERE NOT EXISTS (
            SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
        )
        AND u.is_superuser = false
    """)


def downgrade() -> None:
    op.drop_index('ix_user_roles_role_id', table_name='user_roles')
    op.drop_index('ix_user_roles_user_id', table_name='user_roles')
    op.drop_table('user_roles')
    op.drop_column('roles', 'is_system')
