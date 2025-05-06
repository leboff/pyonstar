"""Minimal asynchronous OnStar client built around :pyclass:`onstar.auth.GMAuth`.

Only the *get_account_vehicles* endpoint is implemented for demonstration
purposes.  It is straightforward to add additional endpoints using the generic
``_api_request`` helper.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Literal, cast, List, TypedDict
from enum import Enum, auto
import json
from urllib.parse import urlparse

import httpx

from .auth import GMAuth, DecodedPayload, get_gm_api_jwt

__all__ = ["OnStar"]


API_BASE = "https://na-mobile-api.gm.com/api/v1"
TOKEN_REFRESH_WINDOW_SECONDS = 5 * 60
logger = logging.getLogger(__name__)


class CommandResponseStatus(Enum):
    """Command response status values."""
    SUCCESS = "success"
    FAILURE = "failure"
    IN_PROGRESS = "inProgress"
    PENDING = "pending"


class AlertRequestAction(Enum):
    """Alert request actions."""
    HONK = "Honk"
    FLASH = "Flash"


class AlertRequestOverride(Enum):
    """Alert request overrides."""
    DOOR_OPEN = "DoorOpen"
    IGNITION_ON = "IgnitionOn"


class ChargeOverrideMode(Enum):
    """Charge override modes."""
    CHARGE_NOW = "ChargeNow"


class ChargingProfileChargeMode(Enum):
    """Charging profile charge modes."""
    IMMEDIATE = "Immediate"


class ChargingProfileRateType(Enum):
    """Charging profile rate types."""
    MIDPEAK = "Midpeak"


class DiagnosticRequestItem(Enum):
    """Diagnostic request items."""
    ODOMETER = "Odometer"
    TIRE_PRESSURE = "TirePressure"
    AMBIENT_AIR_TEMPERATURE = "AmbientAirTemperature"
    LAST_TRIP_DISTANCE = "LastTripDistance"


class DoorRequestOptions(TypedDict, total=False):
    """Door request options."""
    delay: int


class TrunkRequestOptions(TypedDict, total=False):
    """Trunk request options."""
    delay: int


class AlertRequestOptions(TypedDict, total=False):
    """Alert request options."""
    action: List[AlertRequestAction]
    delay: int
    duration: int
    override: List[AlertRequestOverride]


class ChargeOverrideOptions(TypedDict, total=False):
    """Charge override options."""
    mode: ChargeOverrideMode


class SetChargingProfileRequestOptions(TypedDict, total=False):
    """Set charging profile request options."""
    charge_mode: ChargingProfileChargeMode
    rate_type: ChargingProfileRateType


class DiagnosticsRequestOptions(TypedDict, total=False):
    """Diagnostics request options."""
    diagnostic_item: List[DiagnosticRequestItem]


class OnStar:
    """Simple async OnStar client.

    Parameters
    ----------
    username
        GM / OnStar account email.
    password
        Account password.
    device_id
        UUID used by the official app (can be random UUID4).
    vin
        Vehicle VIN – will be upper-cased automatically.
    onstar_pin
        Numeral account PIN (currently *unused* but kept for future endpoints).
    totp_secret
        16-char secret used for MFA (Third-party authenticator).
    token_location
        Directory where ``microsoft_tokens.json`` / ``gm_tokens.json`` will be
        cached (default: current working directory).
    check_request_status
        When *True* follows up on command requests until they complete (default: True).
    request_polling_timeout_seconds
        Maximum time in seconds to poll for command status (default: 90).
    request_polling_interval_seconds
        Time in seconds to wait between status polling requests (default: 6).
    debug
        When *True* emits verbose debug output from both *GMAuth* and the high-
        level client.
    """

    def __init__(
        self,
        *,
        username: str,
        password: str,
        device_id: str,
        vin: str,
        onstar_pin: str,
        totp_secret: str,
        token_location: str | None = None,
        check_request_status: bool = True,
        request_polling_timeout_seconds: int = 90,
        request_polling_interval_seconds: int = 6,
        debug: bool = False,
    ) -> None:
        self._vin = vin.upper()
        self._setup_logging(debug)
        self._auth = self._create_auth(
            username=username,
            password=password,
            device_id=device_id,
            totp_secret=totp_secret,
            token_location=token_location or "./",
            debug=debug,
        )
        # cached token info
        self._token_resp: Optional[Dict[str, Any]] = None
        self._decoded_payload: Optional[DecodedPayload] = None
        
        # Command status tracking
        self._check_request_status = check_request_status
        self._request_polling_timeout_seconds = request_polling_timeout_seconds
        self._request_polling_interval_seconds = request_polling_interval_seconds

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _setup_logging(self, debug: bool) -> None:
        """Initialize logging configuration."""
        if debug:
            # Initialize basic logging config if debug is enabled.
            # This will only have an effect the first time it's called.
            logging.basicConfig(
                level=logging.DEBUG, 
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def _create_auth(
        self,
        *,
        username: str,
        password: str,
        device_id: str,
        totp_secret: str,
        token_location: str,
        debug: bool,
    ) -> GMAuth:
        """Create and configure GMAuth instance."""
        return GMAuth(
            {
                "username": username,
                "password": password,
                "device_id": device_id,
                "totp_key": totp_secret,
                "token_location": token_location,
            },
            debug=debug,
        )

    def _needs_token_refresh(self, token: Dict[str, Any] | None) -> bool:
        """Check if the token needs to be refreshed."""
        if not token:
            return True
        return token.get("expires_at", 0) < int(time.time()) + TOKEN_REFRESH_WINDOW_SECONDS

    async def _ensure_token(self) -> None:
        """Ensure a valid token is available, refreshing if necessary."""
        if self._needs_token_refresh(self._token_resp):
            logger.debug("Retrieving new GM auth token…")
            # blocking – run in executor
            res = await asyncio.to_thread(
                get_gm_api_jwt,
                self._auth.config,  # Pass GMAuth's config directly
                self._auth.config.get("debug", False), 
            )
            self._token_resp = cast(Dict[str, Any], res["token"])
            self._decoded_payload = cast(DecodedPayload, res["decoded_payload"])
            self._validate_vin_authorization()

    def _validate_vin_authorization(self) -> None:
        """Validate that the configured VIN is authorized for this account."""
        if not self._decoded_payload:
            raise RuntimeError("Token payload not available")
            
        vins = [v["vin"].upper() for v in self._decoded_payload["vehs"]]
        if self._vin not in vins:
            raise RuntimeError(
                f"Provided VIN {self._vin} is not authorized – available: {vins}"
            )

    async def _check_request_pause(self) -> None:
        """Pause between status check requests."""
        await asyncio.sleep(self._request_polling_interval_seconds)

    async def _api_request(
        self, 
        method: Literal["GET", "POST", "PUT", "DELETE"],
        path: str, 
        *, 
        json_body: Any | None = None,
        max_retries: int = 1,
        retry_delay: float = 2.0,
        current_retry: int = 0,
        check_request_status: bool | None = None,
        is_status_check: bool = False
    ) -> Dict[str, Any]:
        """Make an authenticated request to the OnStar API.
        
        Parameters
        ----------
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
            
        Returns
        -------
        Dict[str, Any]
            JSON response from the API
        """
        await self._ensure_token()
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token_resp['access_token']}",
        }
        
        # Determine if path is a full URL or just a path
        if path.startswith("http"):
            url = path
        else:
            url = f"{API_BASE}{path}"
            
        logger.debug("%s %s", method, url)
        
        # Debug body
        if json_body:
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
                            return await self._api_request(
                                method, path, json_body=json_body, 
                                max_retries=max_retries, retry_delay=retry_delay,
                                current_retry=current_retry + 1,
                                check_request_status=check_request_status,
                                is_status_check=is_status_check
                            )
                    except Exception as e:
                        logger.error(f"Error parsing error response: {e}")
                
                response.raise_for_status()
                response_data = response.json()

                # Handle command status polling if enabled and not already a status check
                should_check_status = check_request_status if check_request_status is not None else self._check_request_status
                if should_check_status and not is_status_check and isinstance(response_data, dict):
                    command_response = response_data.get("commandResponse")
                    
                    if command_response:
                        request_time = command_response.get("requestTime")
                        status = command_response.get("status")
                        status_url = command_response.get("url")
                        command_type = command_response.get("type")
                        
                        request_timestamp = time.mktime(time.strptime(request_time, "%Y-%m-%dT%H:%M:%S.%fZ")) if request_time else 0
                        
                        # Check for command failure
                        if status == CommandResponseStatus.FAILURE.value:
                            logger.error("Command failed: %s", response_data)
                            raise RuntimeError(f"Command failed: {response_data}")
                        
                        # Check for command timeout
                        current_time = time.time()
                        if current_time >= request_timestamp + self._request_polling_timeout_seconds:
                            logger.error("Command timed out after %s seconds", self._request_polling_timeout_seconds)
                            raise RuntimeError(f"Command timed out after {self._request_polling_timeout_seconds} seconds")
                        
                        # Follow up on in-progress commands
                        if status == CommandResponseStatus.IN_PROGRESS.value and command_type != "connect" and status_url:
                            logger.debug("Command in progress. Polling status from: %s", status_url)
                            await self._check_request_pause()
                            
                            # Use the full status URL directly instead of trying to extract parts
                            return await self._api_request(
                                "GET", 
                                status_url,
                                check_request_status=should_check_status,
                                is_status_check=True
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

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def get_account_vehicles(self) -> Dict[str, Any]:
        """Return JSON payload of vehicles associated with the account."""
        return await self._api_request("GET", "/account/vehicles")

    async def start(self) -> Dict[str, Any]:
        """Start the vehicle."""
        return await self._api_request("POST", f"/account/vehicles/{self._vin}/commands/start")

    async def cancel_start(self) -> Dict[str, Any]:
        """Cancel the start command."""
        return await self._api_request("POST", f"/account/vehicles/{self._vin}/commands/cancelStart")

    async def lock_door(self, options: DoorRequestOptions = None) -> Dict[str, Any]:
        """Lock the vehicle doors.
        
        Parameters
        ----------
        options
            Optional parameters for the lock command
        """
        body = {
            "lockDoorRequest": {
                "delay": 0,
                **(options or {})
            }
        }
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/lockDoor",
            json_body=body
        )

    async def unlock_door(self, options: DoorRequestOptions = None) -> Dict[str, Any]:
        """Unlock the vehicle doors.
        
        Parameters
        ----------
        options
            Optional parameters for the unlock command
        """
        body = {
            "unlockDoorRequest": {
                "delay": 0,
                **(options or {})
            }
        }
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/unlockDoor",
            json_body=body
        )

    async def lock_trunk(self, options: TrunkRequestOptions = None) -> Dict[str, Any]:
        """Lock the vehicle trunk.
        
        Parameters
        ----------
        options
            Optional parameters for the lock trunk command
        """
        body = {
            "lockTrunkRequest": {
                "delay": 0,
                **(options or {})
            }
        }
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/lockTrunk",
            json_body=body
        )

    async def unlock_trunk(self, options: TrunkRequestOptions = None) -> Dict[str, Any]:
        """Unlock the vehicle trunk.
        
        Parameters
        ----------
        options
            Optional parameters for the unlock trunk command
        """
        body = {
            "unlockTrunkRequest": {
                "delay": 0,
                **(options or {})
            }
        }
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/unlockTrunk",
            json_body=body
        )

    async def alert(self, options: AlertRequestOptions = None) -> Dict[str, Any]:
        """Trigger the vehicle alert (honk/flash).
        
        Parameters
        ----------
        options
            Optional parameters for the alert command
        """
        body = {
            "alertRequest": {
                "action": [AlertRequestAction.HONK.value, AlertRequestAction.FLASH.value],
                "delay": 0,
                "duration": 1,
                "override": [
                    AlertRequestOverride.DOOR_OPEN.value, 
                    AlertRequestOverride.IGNITION_ON.value
                ],
                **(options or {})
            }
        }
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/alert",
            json_body=body
        )

    async def cancel_alert(self) -> Dict[str, Any]:
        """Cancel the alert command."""
        return await self._api_request("POST", f"/account/vehicles/{self._vin}/commands/cancelAlert")

    async def charge_override(self, options: ChargeOverrideOptions = None) -> Dict[str, Any]:
        """Override vehicle charging settings.
        
        Parameters
        ----------
        options
            Optional parameters for the charge override command
        """
        body = {
            "chargeOverrideRequest": {
                "mode": ChargeOverrideMode.CHARGE_NOW.value,
                **(options or {})
            }
        }
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/chargeOverride",
            json_body=body
        )

    async def get_charging_profile(self) -> Dict[str, Any]:
        """Get the vehicle charging profile."""
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/getChargingProfile"
        )

    async def set_charging_profile(self, options: SetChargingProfileRequestOptions = None) -> Dict[str, Any]:
        """Set the vehicle charging profile.
        
        Parameters
        ----------
        options
            Optional parameters for setting the charging profile
        """
        body = {
            "chargingProfile": {
                "chargeMode": ChargingProfileChargeMode.IMMEDIATE.value,
                "rateType": ChargingProfileRateType.MIDPEAK.value,
                **(options or {})
            }
        }
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/setChargingProfile",
            json_body=body
        )

    async def diagnostics(self, options: DiagnosticsRequestOptions = None) -> Dict[str, Any]:
        """Get vehicle diagnostics.
        
        Parameters
        ----------
        options
            Optional parameters for the diagnostics command
        """
        # Try with original UPPERCASE value
        body = {
            "diagnosticsRequest": {
                "diagnosticItem": [
                    "ODOMETER"
                ]
            }
        }
        
        # Handle any additional options if provided
        if options and "diagnostic_item" in options:
            items = options["diagnostic_item"]
            diagnostic_items = []
            for item in items:
                if isinstance(item, DiagnosticRequestItem):
                    diagnostic_items.append(item.value)
                else:
                    diagnostic_items.append(item)
            body["diagnosticsRequest"]["diagnosticItem"] = diagnostic_items
        
        # Log the exact request we're sending
        logger.debug("Diagnostics request body: %s", json.dumps(body, indent=2))
        
        # Introduce a small delay before the request
        # This can help with "duplicate request" issues
        await asyncio.sleep(1.0)
            
        try:
            return await self._api_request(
                "POST", 
                f"/account/vehicles/{self._vin}/commands/diagnostics",
                json_body=body,
                max_retries=3,
                retry_delay=5.0
            )
        except httpx.HTTPStatusError as e:
            # Extract error information if possible
            try:
                error_data = e.response.json()
                error_code = error_data.get("error", {}).get("code")
                error_desc = error_data.get("error", {}).get("description", "")
                
                # Special handling for certain error codes
                if error_code == "ONS-300" and "Duplicate vehicle request" in error_desc:
                    logger.warning("Received duplicate request error, this is expected. The request may still have been processed.")
                    # Return a constructed response for the client
                    return {
                        "status": "pending",
                        "message": "Request sent to vehicle. Status pending due to duplicate request limitation.",
                        "commandId": None
                    }
            except Exception:
                pass
            
            # Re-raise the original error if no special handling applied
            raise

    async def location(self) -> Dict[str, Any]:
        """Get the vehicle location."""
        return await self._api_request(
            "POST", 
            f"/account/vehicles/{self._vin}/commands/location"
        ) 