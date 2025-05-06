"""
Python adaptation of GMAuth.ts from the OnStarJS project.
This module focuses exclusively on performing the Microsoft B2C + GM token
exchange so we can retrieve a valid GM API OAuth token.

This is a compatibility wrapper for the refactored auth module.

Dependencies:
    pip install requests pyotp pyjwt
Optionally ``cryptography`` is required by ``pyjwt`` for some algorithms.

NOTE: *All* network traffic is done synchronously via ``requests`` just like the
TypeScript implementation (which is also blocking).  The surrounding library
can off-load this work to a thread if required.
"""

from .auth.types import Vehicle, DecodedPayload, GMAuthConfig, TokenSet, GMAPITokenResponse
from .auth.gm_auth import GMAuth
from .auth.api import get_gm_api_jwt

__all__ = [
    "GMAuth", 
    "get_gm_api_jwt", 
    "GMAPITokenResponse",
    "Vehicle",
    "DecodedPayload",
    "GMAuthConfig",
    "TokenSet"
] 