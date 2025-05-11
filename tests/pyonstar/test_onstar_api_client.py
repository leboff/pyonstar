"""Tests for the OnStarAPIClient."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

import httpx
import time
import json
import datetime

from pyonstar.api import OnStarAPIClient
from pyonstar.types import CommandResponseStatus


@pytest.fixture
def api_client():
    """Create an OnStarAPIClient instance."""
    # Create the client
    client = OnStarAPIClient(
        request_polling_timeout_seconds=30,
        request_polling_interval_seconds=2,
        debug=False
    )
    return client


@pytest.fixture
def mock_command_response():
    """Create a mock command response."""
    return {
        "commandResponse": {
            "status": "success",
            "type": "command",
            "requestTime": "2023-01-01T00:00:00.000Z",
            "body": {
                "status": "success"
            }
        }
    }


@pytest.fixture
def mock_polling_response():
    """Create a mock polling response that requires further polling."""
    # Use a current timestamp to avoid timeout issues
    try:
        # Python 3.11+ syntax
        current_time = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except AttributeError:
        # Fallback for Python 3.10 and earlier
        current_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    return {
        "commandResponse": {
            "status": "inProgress",
            "type": "command",
            "requestTime": current_time,
            "url": "https://api.example.com/api/v1/polling/status/123"
        }
    }


class TestOnStarAPIClient:
    """Tests for the OnStarAPIClient."""

    @pytest.mark.asyncio
    async def test_api_request_simple_success(self, api_client, mock_command_response):
        """Test a simple successful API request."""
        # Create a real httpx response
        mock_response = httpx.Response(
            status_code=200,
            content=json.dumps(mock_command_response).encode(),
            request=httpx.Request("GET", "https://example.com")
        )

        # Mock the client's request method directly
        api_client._client.request = AsyncMock(return_value=mock_response)
        
        result = await api_client.api_request(
            access_token="test_token",
            method="GET",
            path="/test/path"
        )

        # Verify response was returned
        assert result == mock_command_response

    @pytest.mark.asyncio
    async def test_api_request_absolute_url(self, api_client, mock_command_response):
        """Test API request with an absolute URL."""
        # Create a real httpx response
        mock_response = httpx.Response(
            status_code=200,
            content=json.dumps(mock_command_response).encode(),
            request=httpx.Request("GET", "https://example.com")
        )

        # Mock the client's request method directly
        api_client._client.request = AsyncMock(return_value=mock_response)
        
        result = await api_client.api_request(
            access_token="test_token",
            method="GET",
            path="https://example.com/api/test/path"
        )

        # Verify response was returned
        assert result == mock_command_response

    @pytest.mark.asyncio
    async def test_api_request_with_json_body(self, api_client, mock_command_response):
        """Test API request with a JSON body."""
        # Create a real httpx response
        mock_response = httpx.Response(
            status_code=200,
            content=json.dumps(mock_command_response).encode(),
            request=httpx.Request("POST", "https://example.com")
        )

        # Mock the client's request method directly
        api_client._client.request = AsyncMock(return_value=mock_response)
        
        json_body = {"test": "value"}
        result = await api_client.api_request(
            access_token="test_token",
            method="POST",
            path="/test/path",
            json_body=json_body
        )

        # Verify response was returned
        assert result == mock_command_response

    @pytest.mark.asyncio
    async def test_api_request_polling(self, api_client, mock_polling_response, mock_command_response):
        """Test API request with polling for status."""
        # Create real httpx responses for initial and polling requests
        mock_initial_response = httpx.Response(
            status_code=200,
            content=json.dumps(mock_polling_response).encode(),
            request=httpx.Request("POST", "https://example.com")
        )

        mock_polling_response_obj = httpx.Response(
            status_code=200,
            content=json.dumps(mock_command_response).encode(),
            request=httpx.Request("GET", "https://example.com")
        )

        # Mock the request method with different responses
        request_mock = AsyncMock(side_effect=[mock_initial_response, mock_polling_response_obj])
        api_client._client.request = request_mock
        
        # Setup a fixed "current time" that's shortly after the request time to avoid timeout
        # This mocks time.time() to return a value within the polling timeout window
        current_time = time.time()
        
        # Mock request and asyncio.sleep
        with patch('asyncio.sleep', AsyncMock()) as mock_sleep, \
             patch('time.time', return_value=current_time):
            result = await api_client.api_request(
                access_token="test_token",
                method="POST",
                path="/test/path",
                check_request_status=True
            )

            # Verify request was called twice
            assert request_mock.call_count == 2
            
            # Verify sleep was called with the correct interval
            mock_sleep.assert_called_once_with(2)
            
            # Verify final result is the successful command response
            assert result == mock_command_response

    @pytest.mark.asyncio
    async def test_api_request_http_error(self, api_client):
        """Test API request handling HTTP errors."""
        # Create real httpx error response
        error_request = httpx.Request("GET", "https://example.com")
        mock_response = httpx.Response(
            status_code=404,
            content=b"Not Found",
            request=error_request
        )
        
        # Override raise_for_status to raise an exception
        def raise_for_status():
            raise httpx.HTTPStatusError("404 Not Found", request=error_request, response=mock_response)
        
        mock_response.raise_for_status = raise_for_status

        # Mock the client's request method directly
        api_client._client.request = AsyncMock(return_value=mock_response)
        
        with pytest.raises(httpx.HTTPStatusError):
            await api_client.api_request(
                access_token="test_token",
                method="GET",
                path="/test/path"
            )

    @pytest.mark.asyncio
    async def test_max_polls_limit(self, api_client, mock_polling_response):
        """Test respecting the max_polls limit."""
        # Create a response with the polling response
        mock_response = httpx.Response(
            status_code=200,
            content=json.dumps(mock_polling_response).encode(),
            request=httpx.Request("POST", "https://example.com")
        )
        
        # Mock the client's request method to always return the same polling response
        api_client._client.request = AsyncMock(return_value=mock_response)
        
        # Mock asyncio.sleep
        with patch('asyncio.sleep', AsyncMock()):
            result = await api_client.api_request(
                access_token="test_token",
                method="POST",
                path="/test/path",
                check_request_status=True,
                max_polls=2  # Set max polls to 2
            )
            
            # Verify request was called 3 times (initial + 2 polls)
            assert api_client._client.request.call_count == 3
            
            # Verify result is from the final polling response
            assert result == mock_polling_response

    @pytest.mark.asyncio
    async def test_connect_command_no_polling(self, api_client):
        """Test that connect commands don't trigger polling."""
        # Create response for a connect command
        connect_response = {
            "commandResponse": {
                "status": "inProgress",  # Would normally trigger polling
                "type": "connect",       # But not for connect commands
                "requestTime": "2023-01-01T00:00:00.000Z"
            }
        }
        
        # Create a response with the connect response
        mock_response = httpx.Response(
            status_code=200,
            content=json.dumps(connect_response).encode(),
            request=httpx.Request("POST", "https://example.com")
        )
        
        # Mock the client's request method
        api_client._client.request = AsyncMock(return_value=mock_response)
        
        # Set up a mock time that's within the timeout window for the old request time
        current_time = time.mktime(time.strptime("2023-01-01T00:00:10.000Z", "%Y-%m-%dT%H:%M:%S.%fZ"))
        
        # Mock the time function to avoid timeout
        with patch('time.time', return_value=current_time):
            result = await api_client.api_request(
                access_token="test_token",
                method="POST",
                path="/test/path",
                check_request_status=True
            )
            
            # Verify request was only called once (no polling)
            assert api_client._client.request.call_count == 1
            
            # Verify result is the connect response
            assert result == connect_response 