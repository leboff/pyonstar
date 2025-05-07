"""Tests for the CommandFactory."""
import pytest

from pyonstar.commands import CommandFactory
from pyonstar.types import (
    AlertRequestAction,
    AlertRequestOverride,
    ChargeOverrideMode,
    ChargingProfileChargeMode,
    ChargingProfileRateType,
)


class TestCommandFactory:
    """Tests for the CommandFactory."""

    def test_lock_door(self):
        """Test lock_door command generation."""
        # Test with default options
        result = CommandFactory.lock_door()
        assert result == {"lockDoorRequest": {"delay": 0}}
        
        # Test with custom options
        options = {"delay": 10}
        result = CommandFactory.lock_door(options)
        assert result == {"lockDoorRequest": {"delay": 10}}
    
    def test_unlock_door(self):
        """Test unlock_door command generation."""
        # Test with default options
        result = CommandFactory.unlock_door()
        assert result == {"unlockDoorRequest": {"delay": 0}}
        
        # Test with custom options
        options = {"delay": 5}
        result = CommandFactory.unlock_door(options)
        assert result == {"unlockDoorRequest": {"delay": 5}}
    
    def test_lock_trunk(self):
        """Test lock_trunk command generation."""
        # Test with default options
        result = CommandFactory.lock_trunk()
        assert result == {"lockTrunkRequest": {"delay": 0}}
        
        # Test with custom options
        options = {"delay": 3}
        result = CommandFactory.lock_trunk(options)
        assert result == {"lockTrunkRequest": {"delay": 3}}
    
    def test_unlock_trunk(self):
        """Test unlock_trunk command generation."""
        # Test with default options
        result = CommandFactory.unlock_trunk()
        assert result == {"unlockTrunkRequest": {"delay": 0}}
        
        # Test with custom options
        options = {"delay": 7}
        result = CommandFactory.unlock_trunk(options)
        assert result == {"unlockTrunkRequest": {"delay": 7}}
    
    def test_alert(self):
        """Test alert command generation."""
        # Test with default options
        result = CommandFactory.alert()
        assert result["alertRequest"]["action"] == [AlertRequestAction.HONK.value, AlertRequestAction.FLASH.value]
        assert result["alertRequest"]["delay"] == 0
        assert result["alertRequest"]["duration"] == 1
        assert set(result["alertRequest"]["override"]) == {
            AlertRequestOverride.DOOR_OPEN.value,
            AlertRequestOverride.IGNITION_ON.value
        }
        
        # Test with custom options
        options = {
            "action": [AlertRequestAction.FLASH.value],
            "delay": 2,
            "duration": 3,
            "override": [AlertRequestOverride.DOOR_OPEN.value]
        }
        result = CommandFactory.alert(options)
        assert result["alertRequest"]["action"] == [AlertRequestAction.FLASH.value]
        assert result["alertRequest"]["delay"] == 2
        assert result["alertRequest"]["duration"] == 3
        assert result["alertRequest"]["override"] == [AlertRequestOverride.DOOR_OPEN.value]
    
    def test_charge_override(self):
        """Test charge_override command generation."""
        # Test with default options
        result = CommandFactory.charge_override()
        assert result["chargeOverrideRequest"]["mode"] == ChargeOverrideMode.CHARGE_NOW.value
        
        # Test with custom options
        options = {"mode": ChargeOverrideMode.CANCEL_OVERRIDE}
        result = CommandFactory.charge_override(options)
        assert result["chargeOverrideRequest"]["mode"] == ChargeOverrideMode.CANCEL_OVERRIDE.value
    
    def test_set_charging_profile(self):
        """Test set_charging_profile command generation."""
        # Test with default options
        result = CommandFactory.set_charging_profile()
        assert result["chargingProfile"]["chargeMode"] == ChargingProfileChargeMode.IMMEDIATE.value
        assert result["chargingProfile"]["rateType"] == ChargingProfileRateType.MIDPEAK.value
        
        # Test with custom options
        options = {
            "charge_mode": ChargingProfileChargeMode.DEPARTURE_BASED,
            "rate_type": ChargingProfileRateType.OFFPEAK
        }
        result = CommandFactory.set_charging_profile(options)
        assert result["chargingProfile"]["chargeMode"] == ChargingProfileChargeMode.DEPARTURE_BASED.value
        assert result["chargingProfile"]["rateType"] == ChargingProfileRateType.OFFPEAK.value
    
    def test_diagnostics(self):
        """Test diagnostics command generation."""
        diagnostic_items = ["ODOMETER", "TIRE_PRESSURE"]
        result = CommandFactory.diagnostics(diagnostic_items)
        assert result["diagnosticsRequest"]["diagnosticItem"] == diagnostic_items
    
    def test_set_hvac_settings(self):
        """Test set_hvac_settings command generation."""
        # Test with empty settings
        result = CommandFactory.set_hvac_settings()
        assert result["hvacSettings"] == {}
        
        # Test with AC mode only
        result = CommandFactory.set_hvac_settings(ac_mode="AC_NORM_ACTIVE")
        assert result["hvacSettings"]["acClimateSetting"] == "AC_NORM_ACTIVE"
        assert "heatedSteeringWheelEnabled" not in result["hvacSettings"]
        
        # Test with heated steering wheel only
        result = CommandFactory.set_hvac_settings(heated_steering_wheel=True)
        assert "acClimateSetting" not in result["hvacSettings"]
        assert result["hvacSettings"]["heatedSteeringWheelEnabled"] == "true"
        
        # Test with both settings
        result = CommandFactory.set_hvac_settings(
            ac_mode="AC_MAX_ACTIVE",
            heated_steering_wheel=False
        )
        assert result["hvacSettings"]["acClimateSetting"] == "AC_MAX_ACTIVE"
        assert result["hvacSettings"]["heatedSteeringWheelEnabled"] == "false" 