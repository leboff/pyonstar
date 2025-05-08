"""Tests for the API module."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from pyonstar.auth.api import get_gm_api_jwt


class TestApiModule:
    """Tests for the API module."""
    
    @pytest.mark.asyncio
    async def test_get_gm_api_jwt_missing_config(self):
        """Test get_gm_api_jwt with missing configuration."""
        # Test with empty config
        with pytest.raises(ValueError, match="Missing required configuration key:"):
            await get_gm_api_jwt({})
        
        # Test with partial config
        partial_config = {
            "username": "test@example.com",
            "password": "password123",
            # Missing device_id and totp_key
        }
        with pytest.raises(ValueError, match="Missing required configuration key:"):
            await get_gm_api_jwt(partial_config)
    
    @pytest.mark.asyncio
    @patch('pyonstar.auth.api.GMAuth')
    @patch('pyonstar.auth.api.jwt.decode')
    async def test_get_gm_api_jwt_success(self, mock_jwt_decode, mock_auth_class):
        """Test get_gm_api_jwt with successful authentication."""
        # Setup mock auth instance
        mock_auth = AsyncMock()
        mock_auth_class.return_value = mock_auth
        
        # Mock the async load token method
        mock_auth._load_current_gm_api_token = AsyncMock()
        
        # Configure mock authenticate method
        mock_auth.authenticate.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "expires_at": 1609459200,
        }
        
        # Configure mock jwt.decode
        mock_jwt_decode.return_value = {
            "vehs": [{"vin": "TEST12345678901234"}]
        }
        
        # Test with complete config
        config = {
            "username": "test@example.com",
            "password": "password123",
            "device_id": "test-device-id",
            "totp_key": "testsecret",
            "token_location": "./",
        }
        
        result = await get_gm_api_jwt(config)
        
        # Verify GMAuth was constructed with correct arguments
        mock_auth_class.assert_called_once_with(config, debug=False, http_client=None)
        
        # Verify authenticate was called
        mock_auth.authenticate.assert_called_once()
        
        # Verify jwt.decode was called with correct arguments
        mock_jwt_decode.assert_called_once_with(
            "test_access_token", 
            options={"verify_signature": False, "verify_aud": False}
        )
        
        # Verify result structure
        assert "token" in result
        assert "auth" in result
        assert "decoded_payload" in result
        
        # Verify token contents
        assert result["token"]["access_token"] == "test_access_token"
        assert result["token"]["refresh_token"] == "test_refresh_token"
        
        # Verify auth is the mock instance
        assert result["auth"] == mock_auth
        
        # Verify decoded payload
        assert result["decoded_payload"]["vehs"][0]["vin"] == "TEST12345678901234"
    
    @pytest.mark.asyncio
    @patch('pyonstar.auth.api.GMAuth')
    async def test_get_gm_api_jwt_debug_mode(self, mock_auth_class):
        """Test get_gm_api_jwt with debug mode enabled."""
        # Setup mock auth instance
        mock_auth = AsyncMock()
        mock_auth_class.return_value = mock_auth
        
        # Mock the async load token method
        mock_auth._load_current_gm_api_token = AsyncMock()
        
        # Configure authenticate to return a token
        mock_auth.authenticate.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "expires_at": 1609459200,
        }
        
        # Test with debug=True
        config = {
            "username": "test@example.com",
            "password": "password123",
            "device_id": "test-device-id",
            "totp_key": "testsecret",
            "token_location": "./",
        }
        
        # We don't need to validate the full result again, just verify debug flag was passed
        with patch('pyonstar.auth.api.jwt.decode') as mock_jwt_decode:
            mock_jwt_decode.return_value = {"vehs": [{"vin": "TEST12345678901234"}]}
            await get_gm_api_jwt(config, debug=True)
        
        # Verify GMAuth was constructed with debug=True
        mock_auth_class.assert_called_once_with(config, debug=True, http_client=None) 