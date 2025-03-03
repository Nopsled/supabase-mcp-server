from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from supabase_mcp.exceptions import PythonSDKError
from supabase_mcp.sdk_client.auth_admin_models import PARAM_MODELS
from supabase_mcp.sdk_client.python_client import SupabaseSDKClient


@pytest_asyncio.fixture
async def mock_supabase_client():
    """Mock the Supabase client"""
    mock_client = MagicMock()
    mock_client.auth = MagicMock()
    mock_client.auth.admin = MagicMock()

    # Mock all the admin methods
    for method_name in PARAM_MODELS.keys():
        setattr(mock_client.auth.admin, method_name, AsyncMock(return_value={"success": True}))

    return mock_client


@pytest_asyncio.fixture
async def sdk_client(mock_supabase_client):
    """Create a test instance of the SDK client with a mocked Supabase client"""
    # Reset singleton before test
    SupabaseSDKClient._instance = None

    # Create client with test project info and mocked create_async_client
    with patch("supabase_mcp.sdk_client.python_client.create_async_client", return_value=mock_supabase_client):
        client = await SupabaseSDKClient.create("test-project", "test-key")
        yield client

    # Reset singleton after test
    SupabaseSDKClient._instance = None


@pytest.mark.asyncio
class TestSDKClient:
    """Test the Supabase SDK client focusing on core functionality"""

    async def test_url_construction(self):
        """Test URL construction from project reference"""
        client = SupabaseSDKClient("my-project", "my-key")
        url = client.get_supabase_url()
        assert url == "https://my-project.supabase.co"

    async def test_singleton_pattern(self, sdk_client):
        """Test that get_instance returns the singleton instance"""
        # First call to get_instance should return the existing instance
        instance1 = await SupabaseSDKClient.get_instance()
        assert instance1 is sdk_client

        # Second call should return the same instance
        instance2 = await SupabaseSDKClient.get_instance()
        assert instance2 is instance1

    async def test_return_sdk_spec(self, sdk_client):
        """Test that return_python_sdk_spec returns the SDK spec"""
        with patch("supabase_mcp.sdk_client.python_client.get_auth_admin_methods_spec") as mock_get_spec:
            mock_get_spec.return_value = {"test": "spec"}
            result = sdk_client.return_python_sdk_spec()
            assert result == {"test": "spec"}

    async def test_client_init_error(self):
        """Test error handling during client initialization"""
        with patch("supabase_mcp.sdk_client.python_client.create_async_client") as mock_create:
            mock_create.side_effect = Exception("Connection error")

            with pytest.raises(PythonSDKError) as excinfo:
                await SupabaseSDKClient.create("error-project", "error-key")

            assert "Error creating Supabase SDK client" in str(excinfo.value)

    async def test_call_auth_admin_method_validation(self, sdk_client):
        """Test parameter validation when calling auth admin methods"""
        # Valid parameters
        valid_params = {"uid": "test-user-id"}
        result = await sdk_client.call_auth_admin_method("get_user_by_id", valid_params)
        assert result == {"success": True}

        # Invalid parameters (missing required field)
        invalid_params = {}
        with pytest.raises(PythonSDKError) as excinfo:
            await sdk_client.call_auth_admin_method("get_user_by_id", invalid_params)
        assert "Invalid parameters" in str(excinfo.value)

        # Unknown method
        with pytest.raises(PythonSDKError) as excinfo:
            await sdk_client.call_auth_admin_method("unknown_method", {})
        assert "Unknown method" in str(excinfo.value)

    async def test_method_exception_handling(self, sdk_client, mock_supabase_client):
        """Test exception handling when auth admin methods raise errors"""
        # Mock the get_user_by_id method to raise an exception
        error_message = "User not found"
        mock_supabase_client.auth.admin.get_user_by_id.side_effect = Exception(error_message)

        # Call the method and check that the exception is properly wrapped
        with pytest.raises(PythonSDKError) as excinfo:
            await sdk_client.call_auth_admin_method("get_user_by_id", {"uid": "nonexistent-id"})

        assert error_message in str(excinfo.value)
        assert "Error calling get_user_by_id" in str(excinfo.value)
