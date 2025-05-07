#!/usr/bin/env python3
"""
OnStar Python - Vehicle Diagnostics Example
This example demonstrates getting detailed diagnostic information from a vehicle.
"""

import asyncio
import os
import logging
import json
from dotenv import load_dotenv
from pyonstar import OnStar
from pyonstar.client import DiagnosticRequestItem

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_diagnostics(diagnostics):
    """Format diagnostics data for better readability."""
    if not diagnostics or "diagnosticsStatus" not in diagnostics:
        return "No diagnostic data available"
    
    status = diagnostics.get("diagnosticsStatus")
    
    # Pretty-print the full diagnostics to a JSON string with indentation
    full_data = json.dumps(diagnostics, indent=2)
    
    # Extract key metrics for a summary
    summary = []
    
    # Get diagnostic items
    items = diagnostics.get("diagnosticItems", [])
    for item in items:
        name = item.get("name", "Unknown")
        value = item.get("value")
        unit = item.get("unit", "")
        
        if value is not None:
            # Format the line
            if unit:
                summary.append(f"{name}: {value} {unit}")
            else:
                summary.append(f"{name}: {value}")
    
    result = f"Diagnostics Status: {status}\n\n"
    result += "=== Summary ===\n"
    result += "\n".join(summary)
    result += "\n\n=== Full Data ===\n"
    result += full_data
    
    return result


async def main():
    """Main function demonstrating OnStar API usage for diagnostics."""
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
        # Get available diagnostics
        logger.info("Getting supported diagnostics...")
        supported_diagnostics = onstar.get_supported_diagnostics()
        logger.info(f"Supported diagnostics: {', '.join(supported_diagnostics)}")
        
        # Request specific diagnostics
        logger.info("\nRequesting specific diagnostic items...")
        specific_diagnostics = await onstar.diagnostics({
            "diagnostic_item": [
                DiagnosticRequestItem.ODOMETER,
                DiagnosticRequestItem.TIRE_PRESSURE,
                DiagnosticRequestItem.AMBIENT_AIR_TEMPERATURE,
                DiagnosticRequestItem.LAST_TRIP_DISTANCE
            ]
        })
        
        logger.info("\n" + format_diagnostics(specific_diagnostics))
        
        # Request all diagnostics
        logger.info("\nRequesting all diagnostic items (this may take longer)...")
        all_diagnostics = await onstar.diagnostics()
        
        # Save diagnostics to file for reference
        with open("all_diagnostics.json", "w") as f:
            json.dump(all_diagnostics, f, indent=2)
            
        logger.info("\n" + format_diagnostics(all_diagnostics))
        logger.info("\nComplete diagnostics data saved to all_diagnostics.json")
        
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 