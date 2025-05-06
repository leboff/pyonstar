#!/usr/bin/env python3
"""
OnStar Python - Electric Vehicle Example
This example demonstrates the EV-specific functionality of the OnStar Python library.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from onstar import OnStar
from onstar.client import ChargeOverrideMode, ChargingProfileChargeMode, ChargingProfileRateType

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function demonstrating OnStar API usage for electric vehicles."""
    # Create OnStar client from environment variables
    onstar = OnStar(
        username=os.environ.get("ONSTAR_USERNAME"),
        password=os.environ.get("ONSTAR_PASSWORD"),
        device_id=os.environ.get("ONSTAR_DEVICE_ID"),  # Must be a UUID4 (generate at https://www.uuidgenerator.net/version4)
        vin=os.environ.get("ONSTAR_VIN"),
        onstar_pin=os.environ.get("ONSTAR_PIN"),
        totp_secret=os.environ.get("ONSTAR_TOTP_SECRET"),
        debug=os.environ.get("ONSTAR_DEBUG", "false").lower() == "true"
    )
    
    try:
        # Get account vehicles
        logger.info("Getting account vehicles...")
        vehicles = await onstar.get_account_vehicles()
        
        # Check if we have an EV
        vehicle_data = onstar.get_vehicle_data()
        if not vehicle_data:
            logger.error("Failed to get vehicle data")
            return
        
        # Check for EV-specific commands
        commands = vehicle_data.get("commands", {})
        ev_commands = [
            "chargeOverride",
            "getChargingProfile", 
            "setChargingProfile",
            "getChargerPowerLevel"
        ]
        
        # Check which EV commands are available
        available_ev_commands = []
        for cmd in ev_commands:
            if cmd in commands:
                available_ev_commands.append(cmd)
        
        if not available_ev_commands:
            logger.info("No EV-specific commands available for this vehicle.")
            return
        
        logger.info(f"Available EV commands: {', '.join(available_ev_commands)}")
        
        # --------------------
        # Get Charging Profile
        # --------------------
        if "getChargingProfile" in available_ev_commands:
            logger.info("\nGetting charging profile...")
            profile = await onstar.get_charging_profile()
            logger.info(f"Charging profile: {profile}")
        
        # --------------------
        # Get Charger Power Level
        # --------------------
        if "getChargerPowerLevel" in available_ev_commands:
            logger.info("\nGetting charger power level...")
            power_level = await onstar.get_charger_power_level()
            logger.info(f"Charger power level: {power_level}")
        
        # --------------------
        # Set Charging Profile (uncomment to use)
        # --------------------
        if "setChargingProfile" in available_ev_commands:
            # logger.info("\nSetting charging profile to immediate/midpeak...")
            # profile_result = await onstar.set_charging_profile({
            #     "charge_mode": ChargingProfileChargeMode.IMMEDIATE,
            #     "rate_type": ChargingProfileRateType.MIDPEAK
            # })
            # logger.info(f"Set charging profile result: {profile_result}")
            pass
        
        # --------------------
        # Charge Override (uncomment to use)
        # --------------------
        if "chargeOverride" in available_ev_commands:
            # logger.info("\nOverriding charge to charge now...")
            # override_result = await onstar.charge_override({
            #     "mode": ChargeOverrideMode.CHARGE_NOW
            # })
            # logger.info(f"Charge override result: {override_result}")
            # 
            # # To cancel an override, use:
            # # override_result = await onstar.charge_override({
            # #     "mode": ChargeOverrideMode.CANCEL_OVERRIDE
            # # })
            pass
        
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 