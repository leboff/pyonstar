# OnStar Python

Unofficial Python package for making OnStar API requests. This is a Python port of the original OnStarJS package.

## Installation

```bash
pip install onstar
```

## Usage

```python
import asyncio
from onstar import OnStar

async def main():
    # Create OnStar instance
    onstar = OnStar.create({
        "username": "your_username",
        "password": "your_password",
        "device_id": "your_device_id",
        "vin": "your_vin",
        "onstar_pin": "your_pin",  # Optional
        "totp_secret": "your_totp_secret"  # Optional
    })

    # Get account vehicles
    result = await onstar.get_account_vehicles()
    print(result)

    # Start vehicle
    result = await onstar.start()
    print(result)

    # Lock doors
    result = await onstar.lock_door()
    print(result)

    # Get vehicle location
    result = await onstar.location()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- Account vehicle information
- Remote start/stop
- Door lock/unlock
- Trunk lock/unlock
- Vehicle alerts
- Charging profile management
- Vehicle diagnostics
- Location tracking

## Requirements

- Python 3.8 or higher
- Required packages (automatically installed):
  - requests
  - pyjwt
  - python-dotenv
  - uuid
  - pyotp

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
