"""Constants used in the OnStar authentication process."""

# Microsoft B2C OAuth constants
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

# OpenID endpoints
OIDC_ISSUER = (
    "https://custlogin.gm.com/"
    "gmb2cprod.onmicrosoft.com/"
    "b2c_1a_seamless_mobile_signuporsignin/v2.0/"
)

# Fallback endpoints if discovery fails
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

# Discovery URL for OpenID configuration
DISCOVERY_URL = (
    "https://custlogin.gm.com/"
    "gmb2cprod.onmicrosoft.com/"
    "B2C_1A_SEAMLESS_MOBILE_SignUpOrSignIn/v2.0/.well-known/openid-configuration"
)

# GM API endpoint for token exchange
GM_TOKEN_ENDPOINT = "https://na-mobile-api.gm.com/sec/authz/v3/oauth/token"

# User Agent (iPhone 15.x Safari)
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_8_3 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.6 "
    "Mobile/15E148 Safari/604.1"
)

# Common headers for all requests
COMMON_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": USER_AGENT,
} 