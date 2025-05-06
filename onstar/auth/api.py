"""API functions for OnStar authentication."""

import jwt

from .types import GMAuthConfig, DecodedPayload
from .gm_auth import GMAuth


def get_gm_api_jwt(config: GMAuthConfig, debug: bool = False):
    """Convenience wrapper to get a GM API JWT token.
    
    Args:
        config: Configuration for authentication
        debug: Enable debug logging
        
    Returns:
        dict: Contains token, auth instance, and decoded payload
    
    Raises:
        ValueError: If required configuration keys are missing
    """
    required = ["username", "password", "device_id", "totp_key"]
    for key in required:
        if not config.get(key):
            raise ValueError(f"Missing required configuration key: {key}")

    auth = GMAuth(config, debug=debug)
    token_resp = auth.authenticate()
    decoded: DecodedPayload = jwt.decode(
        token_resp["access_token"], options={"verify_signature": False, "verify_aud": False}
    )  # type: ignore[arg-type]
    return {
        "token": token_resp,
        "auth": auth,
        "decoded_payload": decoded,
    } 