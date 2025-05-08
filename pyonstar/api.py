"""API utilities for OnStar client."""
import asyncio
import logging
import time
from typing import Any, Dict, Literal, Optional

import httpx

from .types import CommandResponseStatus

API_BASE = "https://na-mobile-api.gm.com/api/v1"
logger = logging.getLogger(__name__)


class OnStarAPIClient:
    """Client for making API requests to the OnStar API."""

    def __init__(
        self,
        *,
        request_polling_timeout_seconds: int = 90,
        request_polling_interval_seconds: int = 15,
        debug: bool = False
    ) -> None:
        """Initialize OnStar API client.

        Parameters
        ----------
        request_polling_timeout_seconds
            Maximum time in seconds to poll for command status (default: 90)
        request_polling_interval_seconds
            Time in seconds to wait between status polling requests (default: 6)
        debug
            When *True* emits verbose debug output
        """
        self._request_polling_timeout_seconds = request_polling_timeout_seconds
        self._request_polling_interval_seconds = request_polling_interval_seconds
        self._debug = debug

    async def _check_request_pause(self) -> None:
        """Pause between status check requests."""
        await asyncio.sleep(self._request_polling_interval_seconds)

    async def api_request(
        self, 
        access_token: str,
        method: Literal["GET", "POST", "PUT", "DELETE"],
        path: str, 
        *, 
        json_body: Any | None = None,
        max_retries: int = 1,
        retry_delay: float = 2.0,
        current_retry: int = 0,
        check_request_status: bool = True,
        is_status_check: bool = False,
        poll_count: int = 0,
        max_polls: int | None = None
    ) -> Dict[str, Any]:
        """Make an authenticated request to the OnStar API.
        
        Parameters
        ----------
        access_token
            Valid access token for API authentication
        method
            HTTP method to use
        path
            API endpoint path (will be appended to API_BASE) or full URL
        json_body
            Optional JSON payload to send with the request
        max_retries
            Maximum number of retry attempts
        retry_delay
            Delay in seconds between retries
        current_retry
            Current retry attempt (used internally)
        check_request_status
            Whether to check and poll for command status completion
        is_status_check
            Whether this is a status check request (used internally)
        poll_count
            Current poll attempt count (used internally)
        max_polls
            Maximum number of poll attempts (None = unlimited)
            
        Returns
        -------
        Dict[str, Any]
            JSON response from the API
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        
        # Determine if path is a full URL or just a path
        if path.startswith("http"):
            url = path
        else:
            url = f"{API_BASE}{path}"
            
        logger.debug("%s %s", method, url)
        
        # Debug body
        if json_body and self._debug:
            logger.debug("Request body: %s", json_body)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, headers=headers, json=json_body)
                logger.debug("→ status=%s", response.status_code)
                
                # Log response body on error
                if response.status_code >= 400:
                    logger.error("Response body: %s", response.text)
                
                # Check for duplicate request error
                if response.status_code == 500 and current_retry < max_retries:
                    try:
                        error_body = response.json()
                        if (error_body.get("error", {}).get("code") == "ONS-300" and
                            "Duplicate vehicle request" in error_body.get("error", {}).get("description", "")):
                            logger.warning(f"Duplicate request detected, retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            return await self.api_request(
                                access_token, method, path, json_body=json_body, 
                                max_retries=max_retries, retry_delay=retry_delay,
                                current_retry=current_retry + 1,
                                check_request_status=check_request_status,
                                is_status_check=is_status_check,
                                poll_count=poll_count,
                                max_polls=max_polls
                            )
                    except Exception as e:
                        logger.error(f"Error parsing error response: {e}")
                
                response.raise_for_status()
                response_data = response.json()
                
                if self._debug:
                    logger.debug("Response data: %s", response_data)

                # Handle command status polling if enabled and not already a status check
                if check_request_status and isinstance(response_data, dict):
                    command_response = response_data.get("commandResponse")
                    
                    if command_response:
                        request_time = command_response.get("requestTime")
                        status = command_response.get("status")
                        status_url = command_response.get("url")
                        command_type = command_response.get("type")
                        
                        # Check for command failure
                        if status == CommandResponseStatus.FAILURE.value:
                            logger.error("Command failed: %s", response_data)
                            raise RuntimeError(f"Command failed: {response_data}")
                        
                        # If we have a success status with body data, return it
                        if status == CommandResponseStatus.SUCCESS.value and "body" in command_response:
                            return response_data
                        
                        # Check for maximum polls if specified
                        if max_polls is not None and poll_count >= max_polls:
                            logger.warning(f"Reached maximum poll count ({max_polls}), returning current response")
                            return response_data
                        
                        # Check for command timeout based on request timestamp if available
                        if request_time:
                            request_timestamp = time.mktime(time.strptime(request_time, "%Y-%m-%dT%H:%M:%S.%fZ"))
                            current_time = time.time()
                            if current_time >= request_timestamp + self._request_polling_timeout_seconds:
                                logger.error("Command timed out after %s seconds", self._request_polling_timeout_seconds)
                                raise RuntimeError(f"Command timed out after {self._request_polling_timeout_seconds} seconds")
                        
                        # For "connect" command, we don't continue polling
                        if command_type == "connect":
                            return response_data
                        
                        # For all other commands in non-success states with status URL, continue polling
                        if status_url and status != CommandResponseStatus.SUCCESS.value:
                            logger.debug(f"Command {command_type} in {status} state. Polling status from: {status_url}")
                            await self._check_request_pause()
                            
                            # Continue polling with incremented poll count
                            return await self.api_request(
                                access_token,
                                "GET", 
                                status_url,
                                check_request_status=check_request_status,
                                is_status_check=True,
                                poll_count=poll_count + 1,
                                max_polls=max_polls
                            )
                
                return response_data
            except httpx.HTTPStatusError as e:
                logger.error("HTTP error: %s", e)
                # Try to parse the response JSON if possible
                try:
                    error_body = e.response.json()
                    logger.error("Error details: %s", error_body)
                except Exception:
                    logger.error("Error response text: %s", e.response.text)
                raise
            except Exception as e:
                logger.error("Request failed: %s", e)
                raise 