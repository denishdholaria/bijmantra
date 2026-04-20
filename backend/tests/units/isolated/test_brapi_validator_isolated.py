import json
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to sys.path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "backend"))

# Also add scripts directory to sys.path to import the script module
SCRIPTS_DIR = PROJECT_ROOT / "backend" / "scripts"
sys.path.append(str(SCRIPTS_DIR))

# Mock httpx and app dependencies if missing
import sys
from unittest.mock import MagicMock

if "httpx" not in sys.modules:
    sys.modules["httpx"] = MagicMock()

if "pydantic" not in sys.modules:
    mock_pydantic = MagicMock()

    class MockBaseModel:
        def __init__(self, **kwargs):
            pass
        @classmethod
        def model_validate(cls, data):
            pass

    mock_pydantic.BaseModel = MockBaseModel
    mock_pydantic.Field = MagicMock(return_value=None)
    mock_pydantic.ConfigDict = MagicMock()

    class MockValidationError(Exception):
        @classmethod
        def from_exception_data(cls, msg, errors):
            return cls(msg)

    mock_pydantic.ValidationError = MockValidationError

    sys.modules["pydantic"] = mock_pydantic

# Now import the validator
try:
    import brapi_v2_1_compliance_validator as validator
except ImportError:
    # If the above fails (e.g. running from different context), try relative
    sys.path.append(str(Path(__file__).resolve().parents[3] / "scripts"))
    import brapi_v2_1_compliance_validator as validator

# Define a minimal BrAPIResponse mock for testing logic
class MockBrAPIResponse(MagicMock):
    @classmethod
    def model_validate(cls, data):
            # Minimal validation logic for test
            if "metadata" not in data:
                raise validator.ValidationError.from_exception_data("Missing metadata", [])
            if "result" not in data:
                # In real pydantic this might pass or fail depending on Generic
                pass
            return cls()

    def __class_getitem__(cls, item):
        # Return a new class that knows about the item (model)
        class ParameterizedResponse(MockBrAPIResponse):
            _result_model = item

            @classmethod
            def model_validate(cls, data):
                # Call parent validation first
                super().model_validate(data)
                # Now validate result if possible
                if hasattr(cls, '_result_model') and cls._result_model and "result" in data:
                     if hasattr(cls._result_model, 'model_validate'):
                         cls._result_model.model_validate(data["result"])
                return cls()
        return ParameterizedResponse

class TestBrAPIValidator(unittest.TestCase):
    def setUp(self):
        # Force use of MockBrAPIResponse and ensure APP_SCHEMAS_AVAILABLE is True
        self.original_brapi_response = validator.BrAPIResponse
        self.original_schemas_available = validator.APP_SCHEMAS_AVAILABLE

        validator.BrAPIResponse = MockBrAPIResponse
        validator.APP_SCHEMAS_AVAILABLE = True

        self.valid_metadata = {
            "pagination": {
                "currentPage": 0,
                "pageSize": 10,
                "totalCount": 100,
                "totalPages": 10
            },
            "status": [],
            "datafiles": []
        }
        self.valid_server_info = {
            "serverName": "Test Server",
            "apiVersion": "2.1",
            "calls": []
        }

    def tearDown(self):
        validator.BrAPIResponse = self.original_brapi_response
        validator.APP_SCHEMAS_AVAILABLE = self.original_schemas_available

    def test_validate_response_structure_success(self):
        """Test that a valid BrAPI response structure passes validation."""
        data = {
            "metadata": self.valid_metadata,
            "result": {"some": "data"}
        }
        # Generic validation
        self.assertTrue(validator.validate_brapi_response(data))

    def test_validate_response_structure_failure_missing_metadata(self):
        """Test that missing metadata fails validation."""
        data = {
            "result": {"some": "data"}
        }
        self.assertFalse(validator.validate_brapi_response(data))

    def test_validate_response_specific_model_success(self):
        """Test validation against a specific model (ServerInfo)."""
        data = {
            "metadata": self.valid_metadata,
            "result": self.valid_server_info
        }
        self.assertTrue(validator.validate_brapi_response(data, validator.ServerInfo))

    def test_validate_response_specific_model_failure(self):
        """Test validation failure against a specific model (invalid ServerInfo)."""
        invalid_server_info = self.valid_server_info.copy()
        del invalid_server_info["serverName"] # Required field

        data = {
            "metadata": self.valid_metadata,
            "result": invalid_server_info
        }

        # We need to ensure ServerInfo.model_validate raises ValidationError when mocked
        # Since ServerInfo inherits from MockBaseModel which does nothing, we must patch it.
        original_validate = validator.ServerInfo.model_validate

        def side_effect(data):
            if "serverName" not in data:
                raise validator.ValidationError.from_exception_data("Missing serverName", [])

        validator.ServerInfo.model_validate = MagicMock(side_effect=side_effect)

        try:
            self.assertFalse(validator.validate_brapi_response(data, validator.ServerInfo))
        finally:
            validator.ServerInfo.model_validate = original_validate

    @patch("httpx.Client")
    def test_cli_url_success(self, mock_client_cls):
        """Test CLI execution with URL argument."""
        # Mock generic response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "metadata": self.valid_metadata,
            "result": self.valid_server_info
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        # Mock sys.argv
        test_args = ["script", "--url", "http://example.com/brapi/v2/serverinfo", "--type", "serverinfo"]
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                validator.main()
            self.assertEqual(cm.exception.code, 0)

    @patch("builtins.open")
    def test_cli_file_success(self, mock_open):
        """Test CLI execution with file argument."""
        # Mock file content
        file_content = json.dumps({
            "metadata": self.valid_metadata,
            "result": self.valid_server_info
        })
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_file.read.return_value = file_content
        mock_open.return_value = mock_file

        # Mock sys.argv
        test_args = ["script", "--file", "test.json", "--type", "serverinfo"]
        with patch.object(sys, 'argv', test_args):
             with self.assertRaises(SystemExit) as cm:
                validator.main()
             self.assertEqual(cm.exception.code, 0)

if __name__ == "__main__":
    unittest.main()
