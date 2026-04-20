# BIJMANTRA JULES JOB CARD: D13
import sys
import unittest
from unittest.mock import MagicMock, patch
import types
import os

# Mock dependencies
sys.modules["geoalchemy2"] = MagicMock()
sys.modules["jose"] = MagicMock()
sys.modules["passlib"] = MagicMock()
sys.modules["passlib.context"] = MagicMock()

# Configure mock settings
try:
    from app.core import config
    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    mock_settings.ENVIRONMENT = "development"
    config.settings = mock_settings
except ImportError:
    pass

# Patch create_async_engine
with patch("sqlalchemy.ext.asyncio.create_async_engine") as mock_create_engine:
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine

    # Pre-populate app.models to avoid loading app/models/__init__.py
    app_models_path = os.path.join(os.getcwd(), "backend", "app", "models")
    if not os.path.exists(app_models_path):
        app_models_path = os.path.join(os.getcwd(), "app", "models")

    m = types.ModuleType("app.models")
    m.__path__ = [app_models_path]
    sys.modules["app.models"] = m

    # Import app modules
    try:
        from app.models.audit import AuditLog
        from app.core.database import Base
    except ImportError:
        raise

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker

# Define dummy models to satisfy ForeignKeys
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)

# We also need Roles for RolePermission if imported?
# AuditLog imports Permission and RolePermission too.
# RolePermission has foreign key to roles.id and permissions.id
# Permission is defined in audit.py so it's fine.
# Role is missing.

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)

class TestAuditLogImmutability(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_audit_log_creation(self):
        """Test that an audit log can be created."""
        log = AuditLog(
            action="CREATE",
            target_type="TEST",
            method="POST",
            request_path="/test",
            ip="127.0.0.1"
        )
        self.session.add(log)
        self.session.commit()

        self.assertIsNotNone(log.id)

        # Verify it exists in DB
        fetched_log = self.session.query(AuditLog).filter_by(id=log.id).first()
        self.assertIsNotNone(fetched_log)
        self.assertEqual(fetched_log.action, "CREATE")

    def test_audit_log_update_failure(self):
        """Test that updating an audit log raises ValueError."""
        log = AuditLog(
            action="CREATE",
            target_type="TEST",
            method="POST"
        )
        self.session.add(log)
        self.session.commit()

        log.action = "UPDATE"
        self.session.add(log)

        # The validation happens at flush/commit time
        with self.assertRaises(ValueError) as context:
            self.session.commit()

        self.assertIn("Audit logs are immutable", str(context.exception))
        self.session.rollback()

    def test_audit_log_delete_failure(self):
        """Test that deleting an audit log raises ValueError."""
        log = AuditLog(
            action="CREATE",
            target_type="TEST",
            method="POST"
        )
        self.session.add(log)
        self.session.commit()

        self.session.delete(log)

        # The validation happens at flush/commit time
        with self.assertRaises(ValueError) as context:
            self.session.commit()

        self.assertIn("Audit logs are immutable", str(context.exception))
        self.session.rollback()

if __name__ == '__main__':
    unittest.main()
