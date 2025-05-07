"""Pytest configuration file."""
import json
import pytest
from unittest.mock import MagicMock, patch
from pyonstar.auth import GMAuth

@pytest.fixture
def mock_gm_auth():
    """Create a mock GMAuth instance."""
    mock_auth = MagicMock()
    mock_auth.config = {
        "username": "test@example.com",
        "password": "password123",
        "device_id": "test-device-id",
        "totp_key": "testsecret",
        "token_location": "./",
    }
    return mock_auth

@pytest.fixture
def mock_token_response():
    """Create a mock token response."""
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "expires_at": 1609459200,
    }

@pytest.fixture
def mock_vehicles_response():
    """Create a mock vehicles response."""
    return {
        "vehicles": {
            "vehicle": [
                {
                    "vin": "TEST12345678901234",
                    "commands": {
                        "command": [
                            {
                                "name": "start",
                                "url": "https://api.example.com/api/v1/account/vehicles/TEST12345678901234/commands/start",
                                "description": "Start the vehicle",
                                "isPrivSessionRequired": "false"
                            },
                            {
                                "name": "diagnostics",
                                "url": "https://api.example.com/api/v1/account/vehicles/TEST12345678901234/commands/diagnostics",
                                "description": "Get vehicle diagnostics",
                                "isPrivSessionRequired": "false",
                                "commandData": {
                                    "supportedDiagnostics": {
                                        "supportedDiagnostic": [
                                            "ODOMETER",
                                            "TIRE_PRESSURE",
                                            "FUEL_LEVEL",
                                            "BATTERY_LEVEL",
                                            "OIL_LIFE"
                                        ]
                                    }
                                }
                            }
                        ]
                    },
                    "entitlements": {
                        "entitlement": [
                            {
                                "id": "REMOTE_START",
                                "eligible": "true"
                            },
                            {
                                "id": "LOCATE_VEHICLE",
                                "eligible": "true"
                            }
                        ]
                    }
                }
            ]
        }
    }

@pytest.fixture
def mock_diagnostics_response():
    """Create a mock diagnostics response."""
    return {
        "commandResponse": {
            "status": "success",
            "type": "diagnostics",
            "requestTime": "2023-01-01T00:00:00.000Z",
            "body": {
                "diagnosticsStatus": {
                    "ODOMETER": {
                        "value": "12345",
                        "unit": "km"
                    },
                    "TIRE_PRESSURE": {
                        "frontLeft": {
                            "value": "35",
                            "unit": "psi"
                        },
                        "frontRight": {
                            "value": "35",
                            "unit": "psi"
                        },
                        "rearLeft": {
                            "value": "35",
                            "unit": "psi"
                        },
                        "rearRight": {
                            "value": "35",
                            "unit": "psi"
                        }
                    }
                }
            }
        }
    } 