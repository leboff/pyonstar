"""Command operations for OnStar client."""
from typing import Any, Dict, List, Optional

from .types import (
    AlertRequestAction,
    AlertRequestOptions,
    AlertRequestOverride,
    ChargeOverrideMode,
    ChargeOverrideOptions,
    ChargingProfileChargeMode,
    ChargingProfileRateType,
    DiagnosticsRequestOptions,
    DoorRequestOptions,
    SetChargingProfileRequestOptions,
    TrunkRequestOptions,
)


class CommandFactory:
    """Factory for creating OnStar API command payloads."""
    
    @staticmethod
    def lock_door(options: Optional[DoorRequestOptions] = None) -> Dict[str, Any]:
        """Create lock door command payload.
        
        Parameters
        ----------
        options
            Optional parameters for the lock command
        """
        return {
            "lockDoorRequest": {
                "delay": 0,
                **(options or {})
            }
        }
    
    @staticmethod
    def unlock_door(options: Optional[DoorRequestOptions] = None) -> Dict[str, Any]:
        """Create unlock door command payload.
        
        Parameters
        ----------
        options
            Optional parameters for the unlock command
        """
        return {
            "unlockDoorRequest": {
                "delay": 0,
                **(options or {})
            }
        }
    
    @staticmethod
    def lock_trunk(options: Optional[TrunkRequestOptions] = None) -> Dict[str, Any]:
        """Create lock trunk command payload.
        
        Parameters
        ----------
        options
            Optional parameters for the lock trunk command
        """
        return {
            "lockTrunkRequest": {
                "delay": 0,
                **(options or {})
            }
        }
    
    @staticmethod
    def unlock_trunk(options: Optional[TrunkRequestOptions] = None) -> Dict[str, Any]:
        """Create unlock trunk command payload.
        
        Parameters
        ----------
        options
            Optional parameters for the unlock trunk command
        """
        return {
            "unlockTrunkRequest": {
                "delay": 0,
                **(options or {})
            }
        }
    
    @staticmethod
    def alert(options: Optional[AlertRequestOptions] = None) -> Dict[str, Any]:
        """Create alert command payload.
        
        Parameters
        ----------
        options
            Optional parameters for the alert command
        """
        return {
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
    
    @staticmethod
    def charge_override(options: Optional[ChargeOverrideOptions] = None) -> Dict[str, Any]:
        """Create charge override command payload.
        
        Parameters
        ----------
        options
            Optional parameters for the charge override command
        """
        options_dict = options or {}
        mode = options_dict.get("mode", ChargeOverrideMode.CHARGE_NOW)
        
        # Make sure we get the string value if an enum is passed
        mode_value = mode.value if hasattr(mode, "value") else mode
        
        return {
            "chargeOverrideRequest": {
                "mode": mode_value
            }
        }
    
    @staticmethod
    def set_charging_profile(options: Optional[SetChargingProfileRequestOptions] = None) -> Dict[str, Any]:
        """Create set charging profile command payload.
        
        Parameters
        ----------
        options
            Optional parameters for setting the charging profile
        """
        options_dict = options or {}
        
        charge_mode = options_dict.get("charge_mode", ChargingProfileChargeMode.IMMEDIATE)
        rate_type = options_dict.get("rate_type", ChargingProfileRateType.MIDPEAK)
        
        # Make sure we get the string values if enums are passed
        charge_mode_value = charge_mode.value if hasattr(charge_mode, "value") else charge_mode
        rate_type_value = rate_type.value if hasattr(rate_type, "value") else rate_type
        
        return {
            "chargingProfile": {
                "chargeMode": charge_mode_value,
                "rateType": rate_type_value
            }
        }
    
    @staticmethod
    def diagnostics(diagnostic_items: List[str]) -> Dict[str, Any]:
        """Create diagnostics command payload.
        
        Parameters
        ----------
        diagnostic_items
            List of diagnostic items to request
        """
        return {
            "diagnosticsRequest": {
                "diagnosticItem": diagnostic_items
            }
        }
    
    @staticmethod
    def set_hvac_settings(ac_mode: Optional[str] = None, heated_steering_wheel: Optional[bool] = None) -> Dict[str, Any]:
        """Create HVAC settings command payload.
        
        Parameters
        ----------
        ac_mode
            AC climate mode setting
        heated_steering_wheel
            Whether to enable heated steering wheel
        """
        hvac_settings = {}
        
        if ac_mode is not None:
            hvac_settings["acClimateSetting"] = ac_mode
            
        if heated_steering_wheel is not None:
            hvac_settings["heatedSteeringWheelEnabled"] = "true" if heated_steering_wheel else "false"
            
        return {"hvacSettings": hvac_settings} 