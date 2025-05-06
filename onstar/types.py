from typing import TypedDict, Optional, Dict, Any, List, Union

class OnStarConfig(TypedDict):
    username: str
    password: str
    device_id: str
    vin: str
    onstar_pin: Optional[str]
    totp_secret: Optional[str]

class Result(TypedDict):
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]

class AlertRequestOptions(TypedDict, total=False):
    duration: int
    horn: bool
    lights: bool

class DiagnosticsRequestOptions(TypedDict, total=False):
    include_odometer: bool

class SetChargingProfileRequestOptions(TypedDict, total=False):
    charging_profile: Dict[str, Any]

class DoorRequestOptions(TypedDict, total=False):
    door: str

class TrunkRequestOptions(TypedDict, total=False):
    trunk: str

class ChargeOverrideOptions(TypedDict, total=False):
    override: bool 