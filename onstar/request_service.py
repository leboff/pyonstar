import json
import uuid
from typing import Optional, Dict, Any
import aiohttp
import jwt
import pyotp
from .types import (
    OnStarConfig,
    Result,
    AlertRequestOptions,
    DiagnosticsRequestOptions,
    SetChargingProfileRequestOptions,
    DoorRequestOptions,
    TrunkRequestOptions,
    ChargeOverrideOptions,
)

class RequestService:
    def __init__(self, config: OnStarConfig):
        self.config = config
        self.check_request_status = True
        self.request_polling_interval = 6
        self.request_polling_timeout = 90
        self._session: Optional[aiohttp.ClientSession] = None
        self._token: Optional[str] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _authenticate(self) -> None:
        if self._token is not None:
            return

        session = await self._get_session()
        
        # Generate TOTP if secret is provided
        totp_code = None
        if self.config.get("totp_secret"):
            totp = pyotp.TOTP(self.config["totp_secret"])
            totp_code = totp.now()

        # Authentication request
        auth_data = {
            "username": self.config["username"],
            "password": self.config["password"],
            "deviceId": self.config["device_id"],
            "totpCode": totp_code,
        }

        async with session.post(
            "https://api.gm.com/api/v1/oauth/token",
            json=auth_data,
        ) as response:
            if response.status != 200:
                raise Exception("Authentication failed")
            
            data = await response.json()
            self._token = data["access_token"]

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Result:
        await self._authenticate()
        session = await self._get_session()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        url = f"https://api.gm.com/api/v1/account/vehicles/{self.config['vin']}/{endpoint}"

        async with session.request(method, url, headers=headers, json=data) as response:
            if response.status != 200:
                return {
                    "success": False,
                    "error": f"Request failed with status {response.status}",
                }

            result = await response.json()
            return {
                "success": True,
                "data": result,
            }

    def set_check_request_status(self, check_status: bool) -> None:
        self.check_request_status = check_status

    async def get_account_vehicles(self) -> Result:
        return await self._make_request("GET", "account/vehicles")

    async def start(self) -> Result:
        return await self._make_request("POST", "engine/start")

    async def cancel_start(self) -> Result:
        return await self._make_request("POST", "engine/cancel")

    async def lock_door(self, options: Optional[DoorRequestOptions] = None) -> Result:
        data = {"delay": options.get("delay", 0)} if options else {}
        return await self._make_request("POST", "doors/lock", data)

    async def unlock_door(self, options: Optional[DoorRequestOptions] = None) -> Result:
        data = {"delay": options.get("delay", 0)} if options else {}
        return await self._make_request("POST", "doors/unlock", data)

    async def lock_trunk(self, options: Optional[TrunkRequestOptions] = None) -> Result:
        data = {"delay": options.get("delay", 0)} if options else {}
        return await self._make_request("POST", "trunk/lock", data)

    async def unlock_trunk(self, options: Optional[TrunkRequestOptions] = None) -> Result:
        data = {"delay": options.get("delay", 0)} if options else {}
        return await self._make_request("POST", "trunk/unlock", data)

    async def alert(self, options: Optional[AlertRequestOptions] = None) -> Result:
        data = {
            "duration": options.get("duration", 1),
            "horn": options.get("horn", True),
            "lights": options.get("lights", True),
        } if options else {}
        return await self._make_request("POST", "alerts", data)

    async def cancel_alert(self) -> Result:
        return await self._make_request("POST", "alerts/cancel")

    async def charge_override(self, options: Optional[ChargeOverrideOptions] = None) -> Result:
        data = {"override": options.get("override", True)} if options else {}
        return await self._make_request("POST", "charging/override", data)

    async def get_charging_profile(self) -> Result:
        return await self._make_request("GET", "charging/profile")

    async def set_charging_profile(
        self, options: Optional[SetChargingProfileRequestOptions] = None
    ) -> Result:
        data = {"charging_profile": options.get("charging_profile", {})} if options else {}
        return await self._make_request("POST", "charging/profile", data)

    async def diagnostics(self, options: Optional[DiagnosticsRequestOptions] = None) -> Result:
        data = {"include_odometer": options.get("include_odometer", True)} if options else {}
        return await self._make_request("GET", "diagnostics", data)

    async def location(self) -> Result:
        return await self._make_request("GET", "location")

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None 