# OnStar Python Quick Start Guide

This guide will help you get started with the OnStar Python library quickly.

## Installation

Install the package using pip:

```bash
pip install onstar
```

## Basic Setup

1. First, import the required modules:

```python
import asyncio
from onstar import OnStar
```

2. Create an OnStar client instance:

```python
onstar = OnStar(
    username="your_email@example.com",
    password="your_password",
    device_id="your_device_id",  # Must be a UUID4 (generate at https://www.uuidgenerator.net/version4)
    vin="YOUR_VEHICLE_VIN",
    onstar_pin="1234",           # Your OnStar PIN
    totp_secret="TOTP_SECRET"    # Your MFA secret
)
```

3. Create an async function to perform operations:

```python
async def main():
    # Get all vehicles associated with your account
    vehicles = await onstar.get_account_vehicles()
    print(f"Found {len(vehicles['vehicles'])} vehicles")
    
    # Lock the doors
    lock_result = await onstar.lock_door()
    print(f"Lock doors result: {lock_result['status']}")
    
    # Get vehicle location
    location = await onstar.location()
    print(f"Vehicle location: {location}")
    
    # Get vehicle diagnostics
    diagnostics = await onstar.diagnostics()
    print(f"Vehicle diagnostics: {diagnostics}")

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
```

## Complete Example

Here's a complete example that puts it all together:

```python
import asyncio
import uuid
import os
from onstar import OnStar
from onstar.client import DiagnosticRequestItem, AlertRequestAction

# Generate a random device ID if you don't have one
# Note: It's better to keep using the same device ID once generated
device_id = str(uuid.uuid4())

async def main():
    # Get credentials from environment variables for security
    onstar = OnStar(
        username=os.environ.get("ONSTAR_USERNAME"),
        password=os.environ.get("ONSTAR_PASSWORD"),
        device_id=os.environ.get("ONSTAR_DEVICE_ID", device_id),
        vin=os.environ.get("ONSTAR_VIN"),
        onstar_pin=os.environ.get("ONSTAR_PIN"),
        totp_secret=os.environ.get("ONSTAR_TOTP_SECRET"),
        debug=True  # Set to False in production
    )
    
    # Get account vehicles
    print("Getting account vehicles...")
    vehicles = await onstar.get_account_vehicles()
    print(f"Found {len(vehicles['vehicles'])} vehicles")
    
    # Display available commands
    vehicle_data = onstar.get_vehicle_data()
    available_commands = vehicle_data.get("commands", {})
    print("\nAvailable commands:")
    for cmd_name in available_commands.keys():
        print(f"- {cmd_name}")
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Lock doors")
    print("2. Unlock doors")
    print("3. Start vehicle")
    print("4. Get vehicle location")
    print("5. Run vehicle diagnostics")
    
    choice = input("Enter your choice (1-5): ")
    
    try:
        if choice == "1":
            result = await onstar.lock_door()
            print(f"Lock result: {result}")
        elif choice == "2":
            result = await onstar.unlock_door()
            print(f"Unlock result: {result}")
        elif choice == "3":
            result = await onstar.start()
            print(f"Start result: {result}")
        elif choice == "4":
            result = await onstar.location()
            print(f"Location: {result}")
        elif choice == "5":
            result = await onstar.diagnostics()
            print(f"Diagnostics: {result}")
        else:
            print("Invalid choice")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Environment Variables

For security, it's recommended to use environment variables for your credentials:

```bash
# Add to your .env file (do not commit this file to source control)
ONSTAR_USERNAME=your_email@example.com
ONSTAR_PASSWORD=your_password
ONSTAR_DEVICE_ID=your_device_id
ONSTAR_VIN=YOUR_VEHICLE_VIN
ONSTAR_PIN=1234
ONSTAR_TOTP_SECRET=YOUR_TOTP_SECRET
```

Then load them in your Python script:

```python
from dotenv import load_dotenv
load_dotenv()  # Load variables from .env file
```

## Next Steps

- Explore the full [API Documentation](./DOCUMENTATION.md) for more advanced features
- Check out the [Examples](./examples/) directory for more usage scenarios
- Join the community to share your experiences and improvements 