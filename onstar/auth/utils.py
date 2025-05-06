"""Utility functions for the OnStar authentication process."""

import base64


def urlsafe_b64encode(data: bytes) -> str:
    """Return base64url-encoded string **without** padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode() 