from typing import Optional
from .request_service import RequestService
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

class OnStar:
    def __init__(self, request_service: RequestService):
        self.request_service = request_service

    @classmethod
    def create(cls, config: OnStarConfig) -> 'OnStar':
        request_service = RequestService(config)
        return cls(request_service)

    async def get_account_vehicles(self) -> Result:
        return await self.request_service.get_account_vehicles()

    async def start(self) -> Result:
        return await self.request_service.start()

    async def cancel_start(self) -> Result:
        return await self.request_service.cancel_start()

    async def lock_door(self, options: Optional[DoorRequestOptions] = None) -> Result:
        return await self.request_service.lock_door(options)

    async def unlock_door(self, options: Optional[DoorRequestOptions] = None) -> Result:
        return await self.request_service.unlock_door(options)

    async def lock_trunk(self, options: Optional[TrunkRequestOptions] = None) -> Result:
        return await self.request_service.lock_trunk(options)

    async def unlock_trunk(self, options: Optional[TrunkRequestOptions] = None) -> Result:
        return await self.request_service.unlock_trunk(options)

    async def alert(self, options: Optional[AlertRequestOptions] = None) -> Result:
        return await self.request_service.alert(options)

    async def cancel_alert(self) -> Result:
        return await self.request_service.cancel_alert()

    async def charge_override(self, options: Optional[ChargeOverrideOptions] = None) -> Result:
        return await self.request_service.charge_override(options)

    async def get_charging_profile(self) -> Result:
        return await self.request_service.get_charging_profile()

    async def set_charging_profile(
        self, options: Optional[SetChargingProfileRequestOptions] = None
    ) -> Result:
        return await self.request_service.set_charging_profile(options)

    async def diagnostics(self, options: Optional[DiagnosticsRequestOptions] = None) -> Result:
        return await self.request_service.diagnostics(options)

    async def location(self) -> Result:
        return await self.request_service.location()

    def set_check_request_status(self, check_status: bool) -> None:
        self.request_service.set_check_request_status(check_status) 