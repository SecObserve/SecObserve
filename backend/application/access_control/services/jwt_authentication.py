from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from application.access_control.models import JWT_Secret, User
from application.access_control.queries.user import get_user_by_username
from application.commons.models import Settings

ALGORITHM = "HS256"
JWT_PREFIX = "JWT"


def create_jwt(user: User) -> str:
    settings = Settings.load()
    if user.is_superuser:
        jwt_validity_duration = settings.jwt_validity_duration_superuser
    else:
        jwt_validity_duration = settings.jwt_validity_duration_user

    payload = {
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=jwt_validity_duration),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
    }
    token = jwt.encode(payload, JWT_Secret.load().secret, algorithm=ALGORITHM)
    return token


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> Optional[tuple[User, None]]:
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if len(auth) == 1:
            raise AuthenticationFailed("Invalid token header: No credentials provided.")

        if len(auth) > 2:
            raise AuthenticationFailed("Invalid token header: Token string should not contain spaces.")

        try:
            auth_prefix = auth[0].decode("UTF-8")
            auth_token = auth[1].decode("UTF-8")
        except UnicodeDecodeError as e:
            raise AuthenticationFailed(
                "Invalid token header: Token string should not contain invalid characters."
            ) from e

        if auth_prefix.lower() != JWT_PREFIX.lower():
            # Authorization header is possibly for another backend
            return None

        user = self._validate_jwt(auth_token)
        if not user:
            raise AuthenticationFailed("Invalid token.")

        if not user.is_active:
            raise AuthenticationFailed("User is deactivated.")

        return (user, None)

    def authenticate_header(self, request: Request) -> str:
        return JWT_PREFIX

    def _validate_jwt(self, token: str) -> Optional[User]:
        try:
            payload = jwt.decode(token, JWT_Secret.load().secret, algorithms=[ALGORITHM])
            username = payload.get("username")
            if not username:
                raise AuthenticationFailed("No username in JWT")
            return get_user_by_username(username)
        except jwt.PyJWTError as e:
            raise AuthenticationFailed(str(e)) from e
