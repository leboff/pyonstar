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
    return OnStarAPIClient(
        request_polling_timeout_seconds=30,
        request_polling_interval_seconds=2,
        debug=False
    )


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

        # Mock the request method directly
        with patch('httpx.AsyncClient.request', return_value=mock_response):
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

        # Mock the request method directly
        with patch('httpx.AsyncClient.request', return_value=mock_response):
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

        # Mock the request method directly
        with patch('httpx.AsyncClient.request', return_value=mock_response):
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
        
        # Setup a fixed "current time" that's shortly after the request time to avoid timeout
        # This mocks time.time() to return a value within the polling timeout window
        current_time = time.time()
        
        # Mock request and asyncio.sleep
        with patch('httpx.AsyncClient.request', request_mock), \
             patch('asyncio.sleep', AsyncMock()) as mock_sleep, \
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

        # Mock the request method
        with patch('httpx.AsyncClient.request', return_value=mock_response):
            with pytest.raises(httpx.HTTPStatusError):
                await api_client.api_request(
                    access_token="test_token",
                    method="GET",
                    path="/test/path"
                )

    @pytest.mark.asyncio
    async def test_api_request_retry_duplicate(self, api_client, mock_command_response):
        """Test API request retrying on duplicate request errors."""
        # Create real httpx error response
        error_request = httpx.Request("POST", "https://example.com")
        error_response = httpx.Response(
            status_code=500,
            content=json.dumps({
                "error": {
                    "code": "ONS-300",
                    "description": "Duplicate vehicle request"
                }
            }).encode(),
            request=error_request
        )
        
        # Override raise_for_status on error response
        def error_raise_for_status():
            raise httpx.HTTPStatusError("500 Internal Server Error", request=error_request, response=error_response)
        
        error_response.raise_for_status = error_raise_for_status
        
        # Create success response
        success_response = httpx.Response(
            status_code=200,
            content=json.dumps(mock_command_response).encode(),
            request=httpx.Request("POST", "https://example.com")
        )

        # Mock request with different responses and asyncio.sleep
        with patch('httpx.AsyncClient.request', AsyncMock(side_effect=[error_response, success_response])), \
             patch('asyncio.sleep', AsyncMock()) as mock_sleep:
            result = await api_client.api_request(
                access_token="test_token",
                method="POST",
                path="/test/path",
                max_retries=1,
                retry_delay=1.0
            )

            # Verify sleep was called with retry delay
            mock_sleep.assert_called_once_with(1.0)
            
            # Verify the result is the success response
            assert result == mock_command_response

    # @pytest.mark.asyncio
    # async def test_command_timeout(self, api_client, mock_polling_response):
    #     """Test command timeout during polling."""
    #     # Set the request time to be in the past (more than timeout ago)
    #     past_time = time.strftime(
    #         "%Y-%m-%dT%H:%M:%S.000Z", 
    #         time.gmtime(time.time() - 60)  # 60 seconds ago
    #     )
    #     mock_polling_response["commandResponse"]["requestTime"] = past_time
        
    #     # Create real httpx response
    #     mock_response = httpx.Response(
    #         status_code=200,
    #         content=json.dumps(mock_polling_response).encode(),
    #         request=httpx.Request("POST", "https://example.com")
    #     )

    #     # Use a fixed current time that's more than the timeout after the request time
    #     current_time = time.time()  # This is already > 60 seconds after the request time

    #     # Mock request and time.time
    #     with patch('httpx.AsyncClient.request', return_value=mock_response), \
    #          patch('time.time', return_value=current_time):
    #         # The api_client has a 30 second timeout by default in the fixture
    #         with pytest.raises(RuntimeError, match="Command timed out after 30 seconds"):
    #             await api_client.api_request(
    #                 access_token="test_token",
    #                 method="POST",
    #                 path="/test/path",
    #                 check_request_status=True
    #             )

    @pytest.mark.asyncio
    async def test_max_polls_limit(self, api_client, mock_polling_response):
        """Test honoring max_polls parameter."""
        # Create real httpx response that always returns in-progress state
        mock_response = httpx.Response(
            status_code=200,
            content=json.dumps(mock_polling_response).encode(),
            request=httpx.Request("POST", "https://example.com")
        )

        # Setup a fixed time that's within the timeout period
        current_time = time.time()

        # Mock request and asyncio.sleep
        with patch('httpx.AsyncClient.request', return_value=mock_response), \
             patch('asyncio.sleep', AsyncMock()), \
             patch('time.time', return_value=current_time):
            result = await api_client.api_request(
                access_token="test_token",
                method="POST",
                path="/test/path",
                check_request_status=True,
                max_polls=1  # Only allow one poll attempt
            )

            # Verify the result is the polling response (didn't wait for success)
            assert result == mock_polling_response 