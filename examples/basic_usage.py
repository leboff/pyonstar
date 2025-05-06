#!/usr/bin/env python3
"""
OnStar Python - Basic Usage Example
This example demonstrates the basic usage of the OnStar Python library.
"""

import asyncio
import os
import logging
from dotenv import load_dotenv
from onstar import OnStar

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function demonstrating OnStar API usage."""
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
        logger.info(f"Found {len(vehicles['vehicles'])} vehicles")
        
        # Show vehicle information
        for vehicle in vehicles.get("vehicles", []):
            logger.info(f"Vehicle: {vehicle.get('year')} {vehicle.get('make')} {vehicle.get('model')}")
            logger.info(f"VIN: {vehicle.get('vin')}")
        
        # Get vehicle data
        vehicle_data = onstar.get_vehicle_data()
        if vehicle_data:
            available_commands = vehicle_data.get("commands", {})
            logger.info("\nAvailable commands:")
            for cmd_name, cmd_data in available_commands.items():
                logger.info(f"- {cmd_name}")
        
        # --------------------
        # Vehicle Status/Location
        # --------------------
        logger.info("\nGetting vehicle location...")
        location = await onstar.location()
        logger.info(f"Vehicle location: {location}")
        
        # --------------------
        # Vehicle Diagnostics
        # --------------------
        logger.info("\nGetting vehicle diagnostics...")
        diagnostics = await onstar.diagnostics()
        logger.info(f"Vehicle diagnostics received. Status: {diagnostics.get('status')}")
        
        # --------------------
        # Door Locks
        # --------------------
        # Uncomment to actually lock/unlock the vehicle
        
        # logger.info("\nLocking doors...")
        # lock_result = await onstar.lock_door()
        # logger.info(f"Lock result: {lock_result}")
        
        # # Wait a moment before unlocking
        # await asyncio.sleep(5)
        
        # logger.info("\nUnlocking doors...")
        # unlock_result = await onstar.unlock_door()
        # logger.info(f"Unlock result: {unlock_result}")
        
        # --------------------
        # Vehicle Remote Start
        # --------------------
        # Uncomment to actually start/stop the vehicle
        
        # logger.info("\nStarting vehicle...")
        # start_result = await onstar.start()
        # logger.info(f"Start result: {start_result}")
        
        # # Wait a moment before canceling start
        # await asyncio.sleep(10)
        
        # logger.info("\nCanceling vehicle start...")
        # cancel_result = await onstar.cancel_start()
        # logger.info(f"Cancel result: {cancel_result}")
        
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 