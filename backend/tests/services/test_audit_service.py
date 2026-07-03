import unittest
import sys
from unittest.mock import MagicMock, patch

class TestAuditServiceDiff(unittest.TestCase):
    """
    Unit tests for compute_diff function in audit_service.
    Uses sys.modules patching to mock missing dependencies (sqlalchemy, pydantic).
    """

    @classmethod
    def setUpClass(cls):
        # Create mocks for dependencies that might be missing in the test environment
        cls.mock_modules = {
            'sqlalchemy': MagicMock(),
            'sqlalchemy.ext.asyncio': MagicMock(),
            'sqlalchemy.future': MagicMock(),
            'sqlalchemy.orm': MagicMock(),
            'pydantic': MagicMock(),
            'app.models.base': MagicMock(),
        }

        # Start patching
        cls.patcher = patch.dict(sys.modules, cls.mock_modules)
        cls.patcher.start()

        # Ensure imports work as expected
        sys.modules['sqlalchemy'].Column = MagicMock()
        sys.modules['sqlalchemy'].Integer = MagicMock()
        sys.modules['sqlalchemy'].String = MagicMock()
        sys.modules['sqlalchemy'].JSON = MagicMock()
        sys.modules['sqlalchemy'].DateTime = MagicMock()
        sys.modules['sqlalchemy'].Index = MagicMock()

        # Mock pydantic BaseModel
        # We need to ensure that classes inheriting from BaseModel don't crash
        # MagicMock is a valid base class
        sys.modules['pydantic'].BaseModel = MagicMock
        sys.modules['pydantic'].ConfigDict = MagicMock

        # Ensure app.models.base has Base
        # Base needs to be a class that can be inherited from (or MagicMock)
        sys.modules['app.models.base'].Base = MagicMock

        # Import the function to be tested
        # We do this inside setUpClass to ensure mocks are active
        try:
            # Clean up sys.modules to ensure a fresh import if it was already loaded
            if 'app.modules.core.services.audit_service' in sys.modules:
                del sys.modules['app.modules.core.services.audit_service']

            # Since 'app' is not a package in the python standard sense (no __init__.py at root level usually,
            # but here we rely on PYTHONPATH), we import as if from root.
            # The test runner will set PYTHONPATH=backend
            from app.modules.core.services.audit_service import compute_diff
            cls.compute_diff = staticmethod(compute_diff)
        except ImportError as e:
            # Fallback if other non-mocked deps are missing
            print(f"Failed to import audit_service: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_compute_diff_no_changes(self):
        """Test compute_diff with identical dictionaries."""
        old = {'a': 1, 'b': 'test'}
        new = {'a': 1, 'b': 'test'}
        diff = self.compute_diff(old, new)
        self.assertEqual(diff, {})

    def test_compute_diff_simple_update(self):
        """Test compute_diff with a simple value update."""
        old = {'a': 1}
        new = {'a': 2}
        diff = self.compute_diff(old, new)
        expected = {'a': {'old': 1, 'new': 2}}
        self.assertEqual(diff, expected)

    def test_compute_diff_addition(self):
        """Test compute_diff with a new key added."""
        old = {'a': 1}
        new = {'a': 1, 'b': 2}
        diff = self.compute_diff(old, new)
        # old.get('b') is None
        expected = {'b': {'old': None, 'new': 2}}
        self.assertEqual(diff, expected)

    def test_compute_diff_deletion(self):
        """Test compute_diff with a key removed."""
        old = {'a': 1, 'b': 2}
        new = {'a': 1}
        diff = self.compute_diff(old, new)
        # new.get('b') is None
        expected = {'b': {'old': 2, 'new': None}}
        self.assertEqual(diff, expected)

    def test_compute_diff_mixed(self):
        """Test compute_diff with mixed operations (update, add, delete)."""
        old = {'update': 1, 'delete': 2, 'keep': 3}
        new = {'update': 10, 'add': 4, 'keep': 3}
        diff = self.compute_diff(old, new)

        expected = {
            'update': {'old': 1, 'new': 10},
            'delete': {'old': 2, 'new': None},
            'add': {'old': None, 'new': 4}
        }
        self.assertEqual(diff, expected)

    def test_compute_diff_types(self):
        """Test compute_diff with type changes."""
        old = {'a': 1}
        new = {'a': '1'}
        diff = self.compute_diff(old, new)
        expected = {'a': {'old': 1, 'new': '1'}}
        self.assertEqual(diff, expected)

    def test_compute_diff_nested(self):
        """Test compute_diff with nested dictionaries (shallow comparison)."""
        old = {'config': {'enabled': True, 'level': 1}}
        new = {'config': {'enabled': True, 'level': 2}}
        diff = self.compute_diff(old, new)

        # Expect the whole dictionary to be reported as changed because dictionaries are compared by value
        expected = {
            'config': {
                'old': {'enabled': True, 'level': 1},
                'new': {'enabled': True, 'level': 2}
            }
        }
        self.assertEqual(diff, expected)

    def test_compute_diff_none_values(self):
        """
        Test behavior with None values.
        Note: Current implementation treats missing key same as None value.
        """
        # Case 1: Change from None to Value
        old = {'a': None}
        new = {'a': 1}
        diff = self.compute_diff(old, new)
        self.assertEqual(diff, {'a': {'old': None, 'new': 1}})

        # Case 2: Change from Value to None
        old = {'a': 1}
        new = {'a': None}
        diff = self.compute_diff(old, new)
        self.assertEqual(diff, {'a': {'old': 1, 'new': None}})

        # Case 3: Missing key vs None value - treated as identical by .get()
        # This confirms current behavior (limitation or feature)
        old = {}
        new = {'a': None}
        diff = self.compute_diff(old, new)
        self.assertEqual(diff, {})  # old.get('a') is None, new.get('a') is None -> Equal

if __name__ == '__main__':
    unittest.main()
