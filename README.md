# PyOnStar

Unofficial Python package for making OnStar API requests. This is a Python port of the original OnStarJS package.

> **Note:** This project was primarily developed through AI-assisted "vibe-coding" - using AI tools to help port the JavaScript codebase to Python while maintaining the original functionality.

## Installation

```bash
pip install pyonstar
```

## Usage

```python
import asyncio
from pyonstar import OnStar

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

- Python 3.10 or higher
- Required packages (automatically installed):
  - httpx
  - pyjwt
  - pyotp

## Credits

This project is a Python port of:
- [OnStarJS](https://github.com/BigThunderSR/OnStarJS) - NodeJS Library for making OnStar API requests

## License

MIT License - See LICENSE file for details

## Running Tests

This project uses pytest for testing. To run the tests:

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run tests with coverage:
   ```bash
   pytest --cov=pyonstar
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
