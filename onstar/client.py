"""Minimal asynchronous OnStar client built around :pyclass:`onstar.auth.GMAuth`.

Only the *get_account_vehicles* endpoint is implemented for demonstration
purposes.  It is straightforward to add additional endpoints using the generic
``_api_request`` helper.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from .auth import GMAuth, DecodedPayload, get_gm_api_jwt

__all__ = ["OnStar"]


API_BASE = "https://na-mobile-api.gm.com/api/v1"


class OnStar:
    """Simple async OnStar client.

    Parameters
    ----------
    username
        GM / OnStar account email.
    password
        Account password.
    device_id
        UUID used by the official app (can be random UUID4).
    vin
        Vehicle VIN – will be upper-cased automatically.
    onstar_pin
        Numeral account PIN (currently *unused* but kept for future endpoints).
    totp_secret
        16-char secret used for MFA (Third-party authenticator).
    token_location
        Directory where ``microsoft_tokens.json`` / ``gm_tokens.json`` will be
        cached (default: current working directory).
    debug
        When *True* emits verbose debug output from both *GMAuth* and the high-
        level client.
    """

    def __init__(
        self,
        *,
        username: str,
        password: str,
        device_id: str,
        vin: str,
        onstar_pin: str,
        totp_secret: str,
        token_location: str | None = None,
        debug: bool = False,
    ) -> None:
        self._vin = vin.upper()
        self._debug = debug
        self._auth = GMAuth(
            {
                "username": username,
                "password": password,
                "device_id": device_id,
                "totp_key": totp_secret,
                "token_location": token_location or "./",
            },
            debug=debug,
        )
        # cached token info
        self._token_resp: Optional[Dict[str, Any]] = None
        self._decoded_payload: Optional[DecodedPayload] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_token(self):
        # Refresh token when <5min remaining
        def _needs_refresh(token: Dict[str, Any] | None) -> bool:
            if not token:
                return True
            return token.get("expires_at", 0) < int(time.time()) + 5 * 60

        if _needs_refresh(self._token_resp):
            if self._debug:
                print("[OnStar] Retrieving new GM auth token…")
            # blocking – run in executor
            res = await asyncio.to_thread(
                get_gm_api_jwt,
                {
                    "username": self._auth.config["username"],
                    "password": self._auth.config["password"],
                    "device_id": self._auth.config["device_id"],
                    "totp_key": self._auth.config["totp_key"],
                    "token_location": self._auth.config.get("token_location", "./"),
                },
                self._debug,
            )
            self._token_resp = res["token"]  # type: ignore[index]
            self._decoded_payload = res["decoded_payload"]  # type: ignore[index]
            # sanity check vin authorization
            vins = [v["vin"].upper() for v in self._decoded_payload["vehs"]]  # type: ignore[index]
            if self._vin not in vins:
                raise RuntimeError(
                    f"Provided VIN {self._vin} is not authorized – available: {vins}"
                )

    async def _api_request(self, method: str, path: str, *, json_body: Any | None = None):
        await self._ensure_token()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token_resp['access_token']}",
        }
        url = f"{API_BASE}{path}"
        if self._debug:
            print(f"[OnStar] {method} {url}")
        async with httpx.AsyncClient() as client:
            r = await client.request(method, url, headers=headers, json=json_body)
            if self._debug:
                print(f"[OnStar] → status={r.status_code}")
            r.raise_for_status()
            return r.json()

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    async def get_account_vehicles(self):
        """Return JSON payload of vehicles associated with the account."""
        return await self._api_request("GET", "/account/vehicles") 