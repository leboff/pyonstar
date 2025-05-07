"""Tests for the utility functions in the auth module."""
import pytest
import time
from unittest.mock import patch

from pyonstar.auth.utils import regex_extract, build_custlogin_url, is_token_valid, urlsafe_b64encode


class TestUtils:
    """Tests for the utility functions."""
    
    def test_regex_extract_with_match(self):
        """Test regex_extract with a matching pattern."""
        text = "The value is: 12345 and more text"
        pattern = r"value is: (\d+)"
        result = regex_extract(text, pattern)
        assert result == "12345"
    
    def test_regex_extract_no_match(self):
        """Test regex_extract with no match."""
        text = "There is no number here"
        pattern = r"value is: (\d+)"
        result = regex_extract(text, pattern)
        assert result is None
    
    def test_regex_extract_multiple_groups(self):
        """Test regex_extract with multiple groups."""
        text = "The values are: 123 and 456"
        pattern = r"values are: (\d+) and (\d+)"
        # Should only return the first group
        result = regex_extract(text, pattern)
        assert result == "123"
    
    def test_build_custlogin_url_no_params(self):
        """Test build_custlogin_url with no parameters."""
        url = build_custlogin_url("test/path")
        assert url == "https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/test/path"
    
    def test_build_custlogin_url_with_params(self):
        """Test build_custlogin_url with parameters."""
        params = {
            "param1": "value1",
            "param2": "value2"
        }
        url = build_custlogin_url("test/path", params)
        assert "https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/test/path?" in url
        assert "param1=value1" in url
        assert "param2=value2" in url
        assert "&" in url
    
    def test_is_token_valid(self):
        """Test is_token_valid function."""
        current_time = int(time.time())
        
        # Test with valid token (expires in future)
        valid_token = {"expires_at": current_time + 600}  # expires in 10 minutes
        assert is_token_valid(valid_token) is True
        
        # Test with invalid token (expires in past)
        invalid_token = {"expires_at": current_time - 600}  # expired 10 minutes ago
        assert is_token_valid(invalid_token) is False
        
        # Test with token that expires soon (within buffer)
        expiring_soon_token = {"expires_at": current_time + 200}  # expires in less than default buffer
        assert is_token_valid(expiring_soon_token) is False
        
        # Test with custom buffer
        assert is_token_valid(expiring_soon_token, buffer_seconds=100) is True
        
        # Test with missing expires_at
        missing_expires_token = {}
        assert is_token_valid(missing_expires_token) is False
    
    def test_urlsafe_b64encode(self):
        """Test urlsafe_b64encode function."""
        # Test basic encoding
        data = b"test data"
        encoded = urlsafe_b64encode(data)
        
        # Should be base64 encoded without padding
        assert "=" not in encoded
        
        # Should decode back to original data when padding is added back
        padding_len = (4 - len(encoded) % 4) % 4
        padded = encoded + ("=" * padding_len)
        import base64
        decoded = base64.urlsafe_b64decode(padded.encode())
        assert decoded == data 