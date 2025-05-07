"""Tests for the GMAuth class."""
import pytest
from unittest.mock import MagicMock, patch


class TestGMAuth:
    """Tests for the GMAuth class."""
    
    def test_init(self):
        """Test initialization of GMAuth."""
        from pyonstar.auth import GMAuth
        
        config = {
            "username": "test@example.com",
            "password": "password123",
            "device_id": "test-device-id",
            "totp_key": "testsecret",
            "token_location": "./",
        }
        
        auth = GMAuth(config)
        
        assert auth.config == config


@pytest.fixture
def mock_jwt_decode():
    """Mock jwt.decode to avoid token verification."""
    with patch('jwt.decode') as mock:
        mock.return_value = {
            "vehs": [{"vin": "TEST12345678901234"}]
        }
        yield mock


@pytest.fixture
def mock_gmauth_authenticate():
    """Mock GMAuth.authenticate to avoid actual authentication."""
    with patch('pyonstar.auth.gm_auth.GMAuth.authenticate') as mock:
        mock.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "expires_at": 1609459200,
        }
        yield mock


@pytest.mark.asyncio
async def test_get_gm_api_jwt(mock_jwt_decode, mock_gmauth_authenticate):
    """Test the get_gm_api_jwt function with mocked dependencies."""
    from pyonstar.auth import get_gm_api_jwt
    
    config = {
        "username": "test@example.com",
        "password": "password123",
        "device_id": "test-device-id",
        "totp_key": "testsecret",
        "token_location": "./",
    }
    
    result = await get_gm_api_jwt(config)
    
    # Verify authenticate was called
    mock_gmauth_authenticate.assert_called_once()
    
    # Verify jwt.decode was called with the test_access_token
    # There might be other calls to decode, so we need to check any call with our token
    mock_jwt_decode.assert_any_call(
        "test_access_token", 
        options={"verify_signature": False, "verify_aud": False}
    )
    
    # Verify the structure of the result
    assert "token" in result
    assert "auth" in result
    assert "decoded_payload" in result
    
    # Verify token data
    assert result["token"]["access_token"] == "test_access_token"
    assert result["token"]["refresh_token"] == "test_refresh_token"
    
    # Verify decoded payload
    assert result["decoded_payload"]["vehs"][0]["vin"] == "TEST12345678901234" 