import os
from datetime import datetime, timezone
from typing import Optional

from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request

from application.access_control.models import User
from application.access_control.services.oidc_authentication import (
    OIDC_PREFIX,
    OIDCAuthentication,
)
from application.commons.models import Settings

OIDC_CODE_REAUTHENTICATION_REQUIRED = "oidc_reauthentication_required"
OIDC_CODE_AUTH_TIME_MISSING = "oidc_auth_time_missing"

AUTH_TIME_CLAIM = "auth_time"


class OIDCReauthenticationRequired(Exception):
    """The OIDC authentication of the user is not recent enough to create or revoke a user API token."""

    def __init__(self, code: str, message: str, username: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.username = username


def oidc_is_configured() -> bool:
    return bool(os.environ.get("OIDC_AUTHORITY"))


def has_oidc_bearer_header(request: Request) -> bool:
    auth = get_authorization_header(request).split()
    if len(auth) != 2:
        return False

    return auth[0].decode("UTF-8").lower() == OIDC_PREFIX.lower()


def get_freshly_authenticated_oidc_user(request: Request) -> tuple[User, dict]:
    """Authenticate the user with the OIDC token of the request and check that the
    authentication at the OIDC provider is recent enough to issue a user API token."""

    authentication = OIDCAuthentication().authenticate(request)
    if not authentication:
        # Cannot happen, the caller checks the Authorization header beforehand
        raise OIDCReauthenticationRequired(OIDC_CODE_REAUTHENTICATION_REQUIRED, "No OIDC token provided")

    user, payload = authentication

    try:
        _check_authentication_age(payload)
    except OIDCReauthenticationRequired as e:
        # The user has been authenticated successfully, only the authentication is too
        # old. Adding the username makes the refusal traceable in the log.
        e.username = user.username
        raise

    return user, payload


def _check_authentication_age(payload: dict) -> None:
    settings = Settings.load()

    max_authentication_age_minutes = settings.oidc_api_token_max_authentication_age
    if max_authentication_age_minutes == 0:
        # Checking the age of the authentication is disabled
        return

    auth_time = _get_auth_time(payload)
    if auth_time is None:
        raise OIDCReauthenticationRequired(
            OIDC_CODE_AUTH_TIME_MISSING,
            "The OIDC token has no auth_time claim, the age of the authentication cannot be checked",
        )

    # The clock skew is given in seconds, the maximum authentication age in minutes.
    max_authentication_age = max_authentication_age_minutes * 60

    # An auth_time slightly in the future must not be rejected if the clocks of OIDC
    # provider and backend differ, but only within the clock skew.
    age = int(datetime.now(timezone.utc).timestamp()) - auth_time
    if age > max_authentication_age + settings.oidc_clock_skew or age < -settings.oidc_clock_skew:
        raise OIDCReauthenticationRequired(
            OIDC_CODE_REAUTHENTICATION_REQUIRED,
            f"The authentication is older than {max_authentication_age_minutes} minutes, "
            "please authenticate again to manage API tokens",
        )


def _get_auth_time(payload: dict) -> Optional[int]:
    auth_time = payload.get(AUTH_TIME_CLAIM)

    if isinstance(auth_time, bool):
        return None

    if isinstance(auth_time, (int, float)):
        return int(auth_time)

    # Some OIDC providers send auth_time as a string
    if isinstance(auth_time, str) and auth_time.isdigit():
        return int(auth_time)

    return None
