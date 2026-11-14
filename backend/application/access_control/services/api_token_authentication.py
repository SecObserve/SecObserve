from datetime import date
from typing import Optional

from argon2 import PasswordHasher
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from application.access_control.models import API_Token_Multiple, User

API_TOKEN_PREFIX = "APIToken"  # nosec B105


class APITokenAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> Optional[tuple[User, None]]:
        authentication_header = get_authorization_header(request).split()

        if not authentication_header:
            return None

        if len(authentication_header) == 1:
            raise AuthenticationFailed("Invalid token header: No credentials provided.")

        if len(authentication_header) > 2:
            raise AuthenticationFailed("Invalid token header: Token string should not contain spaces.")

        try:
            auth_prefix = authentication_header[0].decode("UTF-8")
            auth_token = authentication_header[1].decode("UTF-8")
        except UnicodeDecodeError as e:
            raise AuthenticationFailed(
                "Invalid token header: Token string should not contain invalid characters."
            ) from e

        if auth_prefix.lower() != API_TOKEN_PREFIX.lower():
            # Authorization header is possibly for another backend
            return None

        api_token = self._validate_api_token(auth_token)
        if not api_token:
            raise AuthenticationFailed("Invalid API token.")

        if not api_token.user.is_active:
            raise AuthenticationFailed("User is deactivated.")

        if api_token.expiration_date and api_token.expiration_date < date.today():
            raise AuthenticationFailed("API token has expired.")

        return (api_token.user, None)

    def authenticate_header(self, request: Request) -> str:
        return API_TOKEN_PREFIX

    def _validate_api_token(self, api_token: str) -> Optional[API_Token_Multiple]:
        ph = PasswordHasher()
        api_tokens = API_Token_Multiple.objects.all()
        for api_token_data in api_tokens:
            try:
                ph.verify(api_token_data.api_token_hash, api_token)
                return api_token_data
            except Exception:  # nosec B110
                # all token need to be checked if a valid one can be found
                pass
        return None
