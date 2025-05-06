# OnStar Python Documentation

## Overview

OnStar Python is an unofficial Python package that provides a client for interacting with the OnStar API. The library allows you to perform various remote operations on your OnStar-equipped vehicle, including starting/stopping the engine, locking/unlocking doors, locating the vehicle, retrieving diagnostics, and managing charging for electric vehicles.

## Installation

```bash
pip install onstar
```

## Authentication

The library handles the complex authentication flow required to interact with the OnStar API, including:

- Microsoft B2C authentication
- GM token exchange
- JWT token management
- Automatic token refresh

### Required Credentials

To use this library, you'll need:

| Credential | Description |
|------------|-------------|
| `username` | Your GM/OnStar account email |
| `password` | Your account password |
| `device_id` | A unique identifier (must be a UUID4 - can be generated at https://www.uuidgenerator.net/version4) |
| `vin` | Your vehicle's VIN number |
| `onstar_pin` | Your OnStar PIN (optional for some operations) |
| `totp_secret` | 16-character secret used for multi-factor authentication |

## Basic Usage

```python
import asyncio
from onstar import OnStar

async def main():
    # Create OnStar instance
    onstar = OnStar(
        username="your_email@example.com",
        password="your_password",
        device_id="your_device_id", # Must be a UUID4 (e.g., generated at https://www.uuidgenerator.net/version4)
        vin="YOUR_VEHICLE_VIN",
        onstar_pin="1234",          # Your OnStar PIN
        totp_secret="TOTP_SECRET",  # Your MFA secret
        debug=False                 # Set to True for verbose logging
    )
    
    # Get account vehicles
    vehicles = await onstar.get_account_vehicles()
    print(vehicles)
    
    # Start the vehicle
    result = await onstar.start()
    print(result)
    
    # Lock the doors
    result = await onstar.lock_door()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### Creating an OnStar Client

You can create an OnStar client instance in two ways:

#### Direct Instantiation

```python
onstar = OnStar(
    username="your_email@example.com",
    password="your_password",
    device_id="your_device_id",
    vin="YOUR_VEHICLE_VIN",
    onstar_pin="1234",
    totp_secret="TOTP_SECRET",
    token_location="./",                   # Optional: directory to store token files
    check_request_status=True,             # Optional: follow up on command requests
    request_polling_timeout_seconds=90,    # Optional: max time to poll for command status
    request_polling_interval_seconds=6,    # Optional: time between status polling
    debug=False                            # Optional: enable verbose logging
)
```

#### Factory Method

```python
onstar = OnStar.create({
    "username": "your_email@example.com",
    "password": "your_password",
    "device_id": "your_device_id",
    "vin": "YOUR_VEHICLE_VIN",
    "onstar_pin": "1234",          # Optional
    "totp_secret": "TOTP_SECRET",  # Optional
    "token_location": "./",        # Optional
    "check_request_status": True,  # Optional
    "request_polling_timeout_seconds": 90,  # Optional
    "request_polling_interval_seconds": 6,  # Optional
    "debug": False                 # Optional
})
```

### Vehicle Information

#### Get Account Vehicles

Retrieves all vehicles associated with your OnStar account.

```python
vehicles = await onstar.get_account_vehicles()
```

Response includes vehicle details such as VIN, year, make, model, and available commands.

#### Get Vehicle Data

Returns cached data about your vehicle after a successful API call.

```python
vehicle_data = onstar.get_vehicle_data()
```

### Remote Commands

#### Start Vehicle

Start your vehicle's engine remotely.

```python
result = await onstar.start()
```

#### Cancel Start

Cancel a previously issued start command.

```python
result = await onstar.cancel_start()
```

#### Lock/Unlock Doors

Lock or unlock your vehicle's doors.

```python
# Lock doors
result = await onstar.lock_door()

# Lock doors with delay
result = await onstar.lock_door({"delay": 5})  # 5 second delay

# Unlock doors
result = await onstar.unlock_door()

# Unlock doors with delay
result = await onstar.unlock_door({"delay": 5})  # 5 second delay
```

#### Lock/Unlock Trunk

Lock or unlock your vehicle's trunk.

```python
# Lock trunk
result = await onstar.lock_trunk()

# Lock trunk with delay
result = await onstar.lock_trunk({"delay": 5})  # 5 second delay

# Unlock trunk
result = await onstar.unlock_trunk()

# Unlock trunk with delay
result = await onstar.unlock_trunk({"delay": 5})  # 5 second delay
```

#### Alert

Trigger vehicle alerts (horn, lights, etc.)

```python
# Default alert
result = await onstar.alert()

# Custom alert with options
from onstar.client import AlertRequestAction, AlertRequestOverride

result = await onstar.alert({
    "action": [AlertRequestAction.HONK, AlertRequestAction.FLASH],
    "delay": 0,
    "duration": 3,
    "override": [AlertRequestOverride.DOOR_OPEN]
})
```

#### Cancel Alert

Cancel an in-progress alert.

```python
result = await onstar.cancel_alert()
```

### Vehicle Location

Get your vehicle's current location.

```python
location = await onstar.location()
```

### Vehicle Diagnostics

#### Supported Diagnostics

Get a list of diagnostics supported by your vehicle.

```python
diagnostics = onstar.get_supported_diagnostics()
```

#### Request Diagnostics

Request specific diagnostic information from your vehicle.

```python
from onstar.client import DiagnosticRequestItem

# Request specific diagnostics
result = await onstar.diagnostics({
    "diagnostic_item": [
        DiagnosticRequestItem.ODOMETER,
        DiagnosticRequestItem.TIRE_PRESSURE,
        DiagnosticRequestItem.AMBIENT_AIR_TEMPERATURE,
        DiagnosticRequestItem.LAST_TRIP_DISTANCE
    ]
})

# For EVs, you might want these specific diagnostics
result = await onstar.diagnostics({
    "diagnostic_item": [
        DiagnosticRequestItem.EV_BATTERY_LEVEL,
        DiagnosticRequestItem.EV_CHARGE_STATE,
        DiagnosticRequestItem.EV_ESTIMATED_CHARGE_END,
        DiagnosticRequestItem.VEHICLE_RANGE
    ]
})

# Request all available diagnostics
result = await onstar.diagnostics()
```

### Electric Vehicle Features

#### Charge Override

Override the charging schedule for your electric vehicle.

```python
from onstar.client import ChargeOverrideMode

result = await onstar.charge_override({
    "mode": ChargeOverrideMode.CHARGE_NOW
})

# To cancel an override
result = await onstar.charge_override({
    "mode": ChargeOverrideMode.CANCEL_OVERRIDE
})
```

#### Get Charging Profile

Get the current charging profile for your electric vehicle.

```python
profile = await onstar.get_charging_profile()
```

#### Set Charging Profile

Set a new charging profile for your electric vehicle.

```python
from onstar.client import ChargingProfileChargeMode, ChargingProfileRateType

# Use IMMEDIATE mode
result = await onstar.set_charging_profile({
    "charge_mode": ChargingProfileChargeMode.IMMEDIATE,
    "rate_type": ChargingProfileRateType.MIDPEAK
})

# Use RATE_BASED mode with OFFPEAK rate
result = await onstar.set_charging_profile({
    "charge_mode": ChargingProfileChargeMode.RATE_BASED,
    "rate_type": ChargingProfileRateType.OFFPEAK
})

# Additional available modes:
# - ChargingProfileChargeMode.DEFAULT_IMMEDIATE
# - ChargingProfileChargeMode.DEPARTURE_BASED
# - ChargingProfileChargeMode.PHEV_AFTER_MIDNIGHT
# 
# Additional available rate types:
# - ChargingProfileRateType.PEAK
```

#### Get Charger Power Level

Get the current power level of your vehicle's charger.

```python
power_level = await onstar.get_charger_power_level()
```

### Account Information

#### Get Entitlements

Get a list of services (entitlements) available for your account.

```python
entitlements = onstar.get_entitlements()
```

#### Check Entitlement

Check if a specific entitlement/service is available.

```python
is_entitled = onstar.is_entitled("REMOTE_START")
```

### HVAC Controls

#### Get Supported HVAC Settings

Get the HVAC settings supported by your vehicle.

```python
hvac_settings = onstar.get_supported_hvac_settings()
```

#### Set HVAC Settings

Set HVAC settings for your vehicle.

```python
result = await onstar.set_hvac_settings(
    ac_mode="on",
    heated_steering_wheel=True
)
```

### Generic Command Execution

If you need to execute a specific command that doesn't have a dedicated method:

```python
# Check if command is available first
if onstar.is_command_available("SOME_COMMAND"):
    result = await onstar.execute_command("SOME_COMMAND", {
        "key": "value",
        # Additional parameters as needed
    })
```

## Error Handling

The library uses standard Python exceptions for error handling. Errors from the OnStar API will be propagated with details about what went wrong.

```python
try:
    result = await onstar.start()
except Exception as e:
    print(f"Error starting vehicle: {e}")
```

## Command Status Tracking

By default, the library will poll the API for command status until completion or timeout. You can configure:

- `check_request_status`: Enable/disable status tracking (default: True)
- `request_polling_timeout_seconds`: Maximum time to poll (default: 90 seconds)
- `request_polling_interval_seconds`: Time between polls (default: 6 seconds)

## Debugging

Enable debug logging for troubleshooting:

```python
onstar = OnStar(
    # Other parameters...
    debug=True
)
```

## Security Considerations

- Token files are stored in the current directory by default
- Your credentials should be kept secure
- Consider using environment variables for sensitive information

## Requirements

- Python 3.8 or higher
- Dependencies:
  - httpx
  - requests
  - pyjwt
  - pyotp
  - uuid 