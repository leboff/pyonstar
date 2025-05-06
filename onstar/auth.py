"""
Python adaptation of GMAuth.ts from the OnStarJS project.
This module focuses exclusively on performing the Microsoft B2C + GM token
exchange so we can retrieve a valid GM API OAuth token.

It attempts to mimic the original TypeScript implementation as closely as
possible while remaining Pythonic.

Dependencies:
    pip install requests pyotp pyjwt
Optionally ``cryptography`` is required by ``pyjwt`` for some algorithms.

NOTE: *All* network traffic is done synchronously via ``requests`` just like the
TypeScript implementation (which is also blocking).  The surrounding library
can off-load this work to a thread if required.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import secrets
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypedDict, Union

import requests
import pyotp
import jwt  # PyJWT

__all__ = ["GMAuth", "get_gm_api_jwt", "GMAPITokenResponse"]

# ---------------------------------------------------------------------------
# Type-helpers
# ---------------------------------------------------------------------------


class Vehicle(TypedDict):
    vin: str
    per: str


class DecodedPayload(TypedDict, total=False):
    vehs: List[Vehicle]
    uid: str  # user identifier (email)


class GMAuthConfig(TypedDict, total=False):
    username: str
    password: str
    device_id: str
    totp_key: str
    token_location: str


class TokenSet(TypedDict, total=False):
    access_token: str
    id_token: str
    refresh_token: str
    expires_at: int
    expires_in: int


class GMAPITokenResponse(TypedDict, total=False):
    access_token: str
    expires_in: int
    expires_at: int
    token_type: str
    scope: str
    id_token: str
    expiration: int
    upgraded: bool
    onstar_account_info: dict
    user_info: dict


# ---------------------------------------------------------------------------
# Constants ‑ endpoints & configuration taken from the TS implementation
# ---------------------------------------------------------------------------

# Moved constants outside the class
CLIENT_ID = "3ff30506-d242-4bed-835b-422bf992622e"
REDIRECT_URI = "https://my.gm.com/"
AUTH_REDIRECT_URI = "msauth.com.gm.myChevrolet://auth"  # For mobile app flow
SCOPES = [
    "https://gmb2cprod.onmicrosoft.com/3ff30506-d242-4bed-835b-422bf992622e/Test.Read",
    "openid",
    "profile",
    "offline_access",
]
SCOPE_STRING = " ".join(SCOPES)

# OpenID endpoints – we rely on the hard-coded fallback shipped in the original
# implementation.  Discovery will be attempted first but is optional.
OIDC_ISSUER = (
    "https://custlogin.gm.com/"
    "gmb2cprod.onmicrosoft.com/"
    "b2c_1a_seamless_mobile_signuporsignin/v2.0/"
)
# We will attempt dynamic discovery first; these are *fallback* values.
FALLBACK_AUTHORIZATION_ENDPOINT = (
    "https://custlogin.gm.com/"
    "gmb2cprod.onmicrosoft.com/"
    "B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/oauth2/v2.0/authorize"
)

FALLBACK_TOKEN_ENDPOINT = (
    "https://custlogin.gm.com/"
    "gmb2cprod.onmicrosoft.com/"
    "B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/oauth2/v2.0/token"
)

DISCOVERY_URL = (
    "https://custlogin.gm.com/"
    "gmb2cprod.onmicrosoft.com/"
    "B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/v2.0/.well-known/openid-configuration"
)

# GM API endpoint for token exchange
GM_TOKEN_ENDPOINT = "https://na-mobile-api.gm.com/sec/authz/v3/oauth/token"

# User Agent taken from original source (iPhone 15.x Safari)
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.6 "
    "Mobile/15E148 Safari/604.1"
)

# Session level headers common for all requests
COMMON_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": USER_AGENT,
}

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def urlsafe_b64encode(data: bytes) -> str:
    """Return base64url-encoded string **without** padding."""

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


# ---------------------------------------------------------------------------
# GMAuth main implementation
# ---------------------------------------------------------------------------


class GMAuth:
    """Re-implementation of the TypeScript *GMAuth* class in Python."""

    def __init__(self, config: GMAuthConfig, debug: bool = False):
        self.config: GMAuthConfig = config
        # Ensure token_location is set and paths exist
        token_location = Path(self.config.get("token_location", "./"))
        token_location.mkdir(parents=True, exist_ok=True)
        self._ms_token_path = token_location / "microsoft_tokens.json"
        self._gm_token_path = token_location / "gm_tokens.json"

        # HTTP session with cookie persistence
        self._session = requests.Session()
        self._session.headers.update(COMMON_HEADERS)

        # Storage for current GM token
        self._current_gm_token: Optional[GMAPITokenResponse] = None

        self.debug = debug

        # Default token endpoint (may be updated after discovery)
        self._token_endpoint: str = FALLBACK_TOKEN_ENDPOINT

        # Attempt to load an existing GM token from disk immediately
        self._load_current_gm_api_token()

        # OIDC metadata (fetched dynamically)
        self._oidc_metadata: Optional[Dict] = None

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def authenticate(self) -> GMAPITokenResponse:
        """Return a *valid* GM API OAuth token, performing auth flow when required."""

        if self.debug:
            logger.debug("[GMAuth] Starting authentication flow…")

        token_set = self._load_ms_token()
        if token_set is not False:
            if self.debug:
                logger.debug("[GMAuth] Successfully loaded cached MS tokens → exchanging for GM token…")
            return self._get_gm_api_token(token_set)

        # Full authentication required
        if self.debug:
            logger.debug("[GMAuth] Performing full MS B2C authentication…")

        token_set = self._do_full_auth_sequence()
        return self._get_gm_api_token(token_set)

    # ---------------------------------------------------------------------
    # Internal helpers – Microsoft identity platform
    # ---------------------------------------------------------------------

    def _do_full_auth_sequence(self) -> TokenSet:
        auth_url, code_verifier = self._start_ms_authorization_flow()

        # ── GET authorization page – extract CSRF + transaction IDs ──
        resp = self._get_request(auth_url)
        csrf = self._regex_extract(resp.text, r'\"csrf\":\"(.*?)\"')
        trans_id = self._regex_extract(resp.text, r'\"transId\":\"(.*?)\"')
        if not csrf or not trans_id:
            raise RuntimeError("Failed to locate csrf or transId in authorization page")

        if self.debug:
            logger.debug(f"[GMAuth] csrf={csrf}  trans_id={trans_id}")

        # ── Submit user credentials ──
        self._submit_credentials(csrf, trans_id)

        # ── Handle MFA (TOTP only) ──
        csrf, trans_id = self._handle_mfa(csrf, trans_id)

        # ── Retrieve authorization *code* from redirect ──
        auth_code = self._get_authorization_code(csrf, trans_id)
        if not auth_code:
            raise RuntimeError("Failed to get authorization code after login/MFA")

        if self.debug:
            logger.debug(f"[GMAuth] Received authorization code: {auth_code[:6]}…")

        # ── Exchange *code* + *code_verifier* for *tokens* ──
        token_set = self._fetch_ms_token(auth_code, code_verifier)

        # ── Persist ──
        self._save_tokens(token_set)
        return token_set

    # ------------------------------------------------------------------
    # Microsoft OIDC helpers
    # ------------------------------------------------------------------

    def _start_ms_authorization_flow(self) -> Tuple[str, str]:
        """Return (authorization_url, code_verifier) using discovery when possible."""

        # Discover
        auth_ep, token_ep = self._get_oidc_endpoints()
        self._token_endpoint = token_ep  # store for later token/refresh calls

        code_verifier = urlsafe_b64encode(secrets.token_bytes(32))
        code_challenge = urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        state = urlsafe_b64encode(secrets.token_bytes(16))
        # Nonce is generated below but not used in params, similar to TS. Removing self._nonce and its assignment.
        # nonce = urlsafe_b64encode(secrets.token_bytes(16))

        # These instance variables were assigned but not used elsewhere in the class.
        # The local variables code_verifier, code_challenge, and state are used appropriately.
        # self.pkce_code_verifier = code_verifier
        # self.pkce_code_challenge = code_challenge
        # self.pkce_state = state
        # self._nonce = nonce

        params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": AUTH_REDIRECT_URI,
            "scope": SCOPE_STRING,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            # Mobile app specific params (mimic myChevrolet)
            "bundleID": "com.gm.myChevrolet",
            "mode": "dark",
            "evar25": "mobile_mychevrolet_chevrolet_us_app_launcher_sign_in_or_create_account",
            "channel": "lightreg",
            "ui_locales": "en-US",
            "brand": "chevrolet",
            "state": state,
        }

        authorization_url = auth_ep + "?" + requests.compat.urlencode(params)
        if self.debug:
            logger.debug(f"[GMAuth] Authorization endpoint: {auth_ep}")
            logger.debug(f"[GMAuth] Token endpoint: {token_ep}")
            logger.debug(f"[GMAuth] Generated authorization URL: {authorization_url}")
        return authorization_url, code_verifier

    # ------------------------------------------------------------------
    # OpenID configuration discovery
    # ------------------------------------------------------------------

    def _get_oidc_endpoints(self) -> Tuple[str, str]:
        """Return (authorization_endpoint, token_endpoint) using run-time discovery when possible."""

        try:
            if self.debug:
                logger.debug(f"[GMAuth] Fetching OIDC discovery metadata → {DISCOVERY_URL}")
            resp = self._session.get(
                DISCOVERY_URL,
                headers={"Accept": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            auth_ep = data.get("authorization_endpoint", FALLBACK_AUTHORIZATION_ENDPOINT)
            token_ep = data.get("token_endpoint", FALLBACK_TOKEN_ENDPOINT)
            return auth_ep, token_ep
        except Exception as exc:
            if self.debug:
                logger.debug(f"[GMAuth] Discovery failed – falling back to hard-coded endpoints ({exc})")
            return FALLBACK_AUTHORIZATION_ENDPOINT, FALLBACK_TOKEN_ENDPOINT

    # ------------------------------------------------------------------
    # HTTP flow helper methods (GET/POST with debug + cookie mgmt)
    # ------------------------------------------------------------------

    def _get_request(self, url: str) -> requests.Response:
        if self.debug:
            logger.debug(f"[GMAuth][GET ] {url}")
        # COMMON_HEADERS (User-Agent, Accept-Language) are already on self._session.headers.
        # requests library handles Accept-Encoding and Connection by default.
        request_specific_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = self._session.get(
            url,
            headers=request_specific_headers,
            allow_redirects=False,
        )
        resp.raise_for_status()
        return resp

    def _post_request(self, url: str, data: Union[Dict[str, str], str], csrf_token: str, extra_headers: Optional[Dict[str, str]] = None) -> requests.Response:
        if self.debug:
            logger.debug(f"[GMAuth][POST] {url}  data={data}")

        # COMMON_HEADERS (User-Agent, Accept-Language) are already on self._session.headers.
        # requests library handles Accept-Encoding and Connection by default.
        request_specific_headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "https://custlogin.gm.com",
            "x-csrf-token": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            **(extra_headers if extra_headers else {}),
        }
        
        resp = self._session.post(
            url,
            data=data,
            headers=request_specific_headers,
            allow_redirects=False,
            )
        resp.raise_for_status()
        return resp

    def _post_oauth_token_request(self, url: str, data: Dict[str, str]) -> requests.Response:
        """Helper for POST requests to OAuth token endpoints."""
        if self.debug:
            logger.debug(f"[GMAuth][POST-OAuthToken] {url} data={data}")

        request_specific_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        resp = self._session.post(
            url,
            data=data,
            headers=request_specific_headers,
        )
        
        if self.debug:
            logger.debug(f"[GMAuth] OAuth Token Endpoint Response Status ({url}): {resp.status_code}")
        resp.raise_for_status()
        return resp

    # ------------------------------------------------------------------
    # Steps: credentials, MFA, authorization code
    # ------------------------------------------------------------------

    def _submit_credentials(self, csrf: str, trans_id: str) -> None:
        url = (
            "https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/"
            "B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/SelfAsserted"
            f"?tx={trans_id}&p=B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn"
        )
        data = {
            "request_type": "RESPONSE",
            "logonIdentifier": self.config["username"],
            "password": self.config["password"],
        }
        self._post_request(url, data, csrf)

    def _handle_mfa(self, csrf: str, trans_id: str) -> Tuple[str, str]:
        # csrf and trans_id are from the step prior to loading the MFA page.
        # Step 1: load MFA page to grab new csrf / transId for OTP submission
        url = (
            "https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/"
            "B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/api/CombinedSigninAndSignup/confirmed"
            f"?rememberMe=true&csrf_token={csrf}&tx={trans_id}&p=B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn"
        )
        resp = self._get_request(url)
        # These are the new CSRF and TransID to be used for submitting the OTP
        csrf_for_otp = self._regex_extract(resp.text, r"\"csrf\":\"(.*?)\"")
        trans_id_for_otp = self._regex_extract(resp.text, r"\"transId\":\"(.*?)\"")
        if not csrf_for_otp or not trans_id_for_otp:
            raise RuntimeError("Failed to extract csrf/transId during MFA GET step for OTP submission")

        if self.debug:
            logger.debug(f"[GMAuth] csrf_for_otp={csrf_for_otp}, trans_id_for_otp={trans_id_for_otp}")

        # Step 2: Generate TOTP code
        try:
            otp = pyotp.TOTP(self.config["totp_key"].strip()).now()
            if self.debug:
                logger.debug(f"[GMAuth] Generated OTP: {otp}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate OTP: {e}") from e

        # Step 3: Submit OTP code
        post_url = (
            f"https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/"
            f"B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/SelfAsserted?"
            f"tx={trans_id_for_otp}&p=B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn"
        )
        post_data = {
            "otpCode": otp,
            "request_type": "RESPONSE",
        }
        self._post_request(post_url, post_data, csrf_for_otp)

        # Return the CSRF token and TransID that were obtained from the MFA page GET,
        # as these are the ones relevant for the subsequent authorization code retrieval step.
        return csrf_for_otp, trans_id_for_otp

    def _get_authorization_code(self, csrf: str, trans_id: str) -> Optional[str]:
        """Fetch the final authorization code after successful login/MFA.
        Uses the /api/SelfAsserted/confirmed endpoint pattern observed in working TS code.
        """
        # URL based on TypeScript implementation:
        url = (
            "https://custlogin.gm.com/gmb2cprod.onmicrosoft.com/"
            "B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/api/SelfAsserted/confirmed"
            f"?csrf_token={csrf}&tx={trans_id}&p=B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn"
        )

        # Use the _get_request helper method.
        # It already handles debug logging for the GET, sets appropriate Accept headers,
        # and sets allow_redirects=False.
        # It also calls resp.raise_for_status(), which is fine as 302 is not an HTTP error status.
        resp = self._get_request(url)
        
        # ADD Debug: Check if session cookies were updated
        if self.debug:
            # ADD MORE DEBUG
            logger.debug(f"[GMAuth] Auth Code GET Response Status: {resp.status_code}")
            logger.debug(f"[GMAuth] Auth Code GET Response Headers: {resp.headers}")
            if resp.status_code != 302:
                 logger.debug(f"[GMAuth] Auth Code GET Response Body (first 500):\\n{resp.text[:500]}")

        if resp.status_code != 302:
            # Log the response content if we didn't get the expected redirect
            if self.debug:
                logger.debug(f"[GMAuth] Unexpected status {resp.status_code} fetching auth code.")
                logger.debug(f"[GMAuth] Response body:\\n{resp.text[:500]}...") # Log first 500 chars
            raise RuntimeError(f"Expected redirect when fetching auth code, got {resp.status_code}")
        location = resp.headers.get("Location") or resp.headers.get("location")
        if not location:
            raise RuntimeError("Auth code redirect Location header missing")

        code = self._regex_extract(location, r"code=(.*?)(&|$)")
        return code

    # ------------------------------------------------------------------
    # MS tokens
    # ------------------------------------------------------------------

    def _fetch_ms_token(self, code: str, code_verifier: str) -> TokenSet:
        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        }
        resp = self._post_oauth_token_request(self._token_endpoint, data)
        token_resp = resp.json()
        if "access_token" not in token_resp:
            raise RuntimeError("token_endpoint did not return access_token")

        token_set: TokenSet = {
            "access_token": token_resp["access_token"],
            "id_token": token_resp.get("id_token"),
            "refresh_token": token_resp.get("refresh_token"),
            "expires_in": token_resp.get("expires_in"),
        }
        if token_set.get("expires_in"):
            token_set["expires_at"] = int(time.time()) + int(token_set["expires_in"])
        return token_set

    def _refresh_ms_token(self, refresh_token: str) -> TokenSet:
        data = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": refresh_token,
        }
        resp = self._post_oauth_token_request(self._token_endpoint, data)
        token_resp = resp.json()
        if "access_token" not in token_resp:
            raise RuntimeError("Refresh failed – no access_token")
        token_set: TokenSet = {
            "access_token": token_resp["access_token"],
            "id_token": token_resp.get("id_token"),
            "refresh_token": token_resp.get("refresh_token", refresh_token),
            "expires_in": token_resp.get("expires_in"),
        }
        if token_set.get("expires_in"):
            token_set["expires_at"] = int(time.time()) + int(token_set["expires_in"])
        return token_set

    # ------------------------------------------------------------------
    # GM API token exchange
    # ------------------------------------------------------------------

    @staticmethod
    def _token_is_valid(token: GMAPITokenResponse) -> bool:
        return token.get("expires_at", 0) > int(time.time()) + 5 * 60

    def _get_gm_api_token(self, token_set: TokenSet) -> GMAPITokenResponse:
        # Cached & valid?
        if self._current_gm_token and self._token_is_valid(self._current_gm_token):
            if self.debug:
                logger.debug("[GMAuth] Using cached GM API token")
            return self._current_gm_token

        if self.debug:
            logger.debug("[GMAuth] Requesting GM API token via token exchange…")

        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": token_set["access_token"],
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "msso role_owner priv onstar gmoc user user_trailer",
            "device_id": self.config["device_id"],
        }
        resp = self._post_oauth_token_request(GM_TOKEN_ENDPOINT, data)
        gm_token: GMAPITokenResponse = resp.json()  # type: ignore[assignment]
        # Add expires_at for convenience
        gm_token["expires_at"] = int(time.time()) + int(gm_token["expires_in"])

        # Sanity check – ensure vehs are present
        decoded: DecodedPayload = jwt.decode(
            gm_token["access_token"],
            options={"verify_signature": False, "verify_aud": False},
        )  # type: ignore[arg-type]
        if not decoded.get("vehs"):
            # Wipe tokens for reauth
            if self.debug:
                logger.debug("[GMAuth] GM token missing vehicle info – forcing re-auth")
            if self._ms_token_path.exists():
                self._ms_token_path.rename(self._ms_token_path.with_suffix(".old"))
            if self._gm_token_path.exists():
                self._gm_token_path.rename(self._gm_token_path.with_suffix(".old"))
            self._current_gm_token = None
            return self.authenticate()  # recursive call

        self._current_gm_token = gm_token
        # Persist both sets
        self._save_tokens(token_set)
        return gm_token

    # ------------------------------------------------------------------
    # Token persistence helpers
    # ------------------------------------------------------------------

    def _save_tokens(self, token_set: TokenSet):
        # MS tokens
        with self._ms_token_path.open("w", encoding="utf-8") as fp:
            json.dump(token_set, fp)
        # GM tokens
        if self._current_gm_token:
            with self._gm_token_path.open("w", encoding="utf-8") as fp:
                json.dump(self._current_gm_token, fp)
        if self.debug:
            logger.debug(f"[GMAuth] Tokens persisted to → {self._ms_token_path.parent}")

    def _load_current_gm_api_token(self):
        if not self._gm_token_path.exists():
            return
        try:
            gm_token: GMAPITokenResponse = json.loads(self._gm_token_path.read_text())  # type: ignore[arg-type]
            decoded: DecodedPayload = jwt.decode(
                gm_token["access_token"], options={"verify_signature": False, "verify_aud": False}
            )  # type: ignore[arg-type]
            if decoded.get("uid", "").upper() != self.config["username"].upper():
                if self.debug:
                    logger.debug("[GMAuth] Stored GM token belongs to another user – ignoring")
                return
            if self._token_is_valid(gm_token):
                self._current_gm_token = gm_token
                if self.debug:
                    logger.debug("[GMAuth] Loaded valid GM token from disk")
        except Exception as exc:
            if self.debug:
                logger.debug(f"[GMAuth] Failed to load GM token – {exc}")

    def _load_ms_token(self) -> TokenSet | bool:
        if not self._ms_token_path.exists():
            return False
        try:
            stored: TokenSet = json.loads(self._ms_token_path.read_text())  # type: ignore[arg-type]
            # Validate expiry & ownership
            decoded = jwt.decode(
                stored["access_token"], options={"verify_signature": False, "verify_aud": False}
            )
            email_or_name = decoded.get("name", "").upper() or decoded.get("email", "").upper()
            if email_or_name != self.config["username"].upper():
                if self.debug:
                    logger.debug("[GMAuth] Cached MS token belongs to different user – ignoring")
                return False
            if stored.get("expires_at", 0) > int(time.time()) + 5 * 60:
                return stored
            # else attempt refresh
            if stored.get("refresh_token"):
                if self.debug:
                    logger.debug("[GMAuth] MS access_token expired → attempting refresh…")
                try:
                    refreshed = self._refresh_ms_token(stored["refresh_token"])
                    self._save_tokens(refreshed)
                    return refreshed
                except Exception as exc:
                    if self.debug:
                        logger.debug(f"[GMAuth] Failed to refresh MS token – {exc}")
        except Exception as exc:
            if self.debug:
                logger.debug(f"[GMAuth] Error loading MS token: {exc}")
        return False

    # ------------------------------------------------------------------
    # Misc helpers
    # ------------------------------------------------------------------

    def _regex_extract(self, text: str, pattern: str) -> Optional[str]:
        match = re.search(pattern, text)
        return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Convenience wrapper mirroring getGMAPIJWT() TS helper
# ---------------------------------------------------------------------------

def get_gm_api_jwt(config: GMAuthConfig, debug: bool = False):
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