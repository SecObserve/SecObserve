import hashlib
import os
import re
from typing import Optional

import jwt
import requests
from django.core.cache import cache
from django.db import IntegrityError, transaction
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from application.access_control.models import Authorization_Group, User
from application.access_control.queries.user import get_user_by_username
from application.commons.models import Settings

OIDC_PREFIX = "Bearer"
ALGORITHMS = ["RS256", "RS384", "RS512", "ES256 ", "ES384", "ES512", "EdDSA"]


class OIDCAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> Optional[tuple[User, None]]:
        auth = get_authorization_header(request).split()
        if not auth:
            return None

        if len(auth) == 1:
            raise AuthenticationFailed("Invalid token header: No credentials provided.")

        if len(auth) > 2:
            raise AuthenticationFailed("Invalid token header: Token string should not contain spaces.")

        auth_prefix = auth[0].decode("UTF-8")
        auth_token = auth[1].decode("UTF-8")

        if auth_prefix.lower() != OIDC_PREFIX.lower():
            # Authorization header is possibly for another backend
            return None

        user = self._validate_jwt(auth_token)
        if not user:
            raise AuthenticationFailed("Invalid token.")

        if not user.is_active:
            raise AuthenticationFailed("User is deactivated.")

        return (user, None)

    def authenticate_header(self, request: Request) -> str:
        return OIDC_PREFIX

    def _validate_jwt(self, token: str) -> Optional[User]:
        settings = Settings.load()
        try:
            jwks_uri = self._get_jwks_uri()
            jwks_client = jwt.PyJWKClient(jwks_uri)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            options = {
                "verify_signature": True,
                "verify_aud": True,
                "strict_aud": True,
                "require": ["exp"],
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
            }
            payload = jwt.decode(
                jwt=token,
                options=options,
                key=signing_key.key,
                algorithms=ALGORITHMS,
                audience=os.environ["OIDC_CLIENT_ID"],
                leeway=settings.oidc_clock_skew,
            )
            username = payload.get(os.environ["OIDC_USERNAME"])
            user = get_user_by_username(username)
            if user:
                user = self._check_user_change(user, payload)
                return user
            return self._create_user(username, payload)
        except jwt.PyJWTError as e:
            raise AuthenticationFailed(str(e)) from e

    def _get_jwks_uri(self) -> str:
        jwks_uri = cache.get("jwks_uri")
        if not jwks_uri:
            response = requests.request(
                method="GET",
                url=f"{os.environ['OIDC_AUTHORITY']}/.well-known/openid-configuration",
                timeout=60,
            )
            response.raise_for_status()
            jwks_uri = response.json()["jwks_uri"]
            cache.set("jwks_uri", jwks_uri, timeout=5 * 60)

        return jwks_uri

    def _create_user(self, username: str, payload: dict) -> User:
        user = User(username=username, first_name="", last_name="", email="")
        if os.environ.get("OIDC_EMAIL"):
            user.email = payload[os.environ["OIDC_EMAIL"]]
        if os.environ.get("OIDC_FULL_NAME"):
            user.full_name = payload[os.environ["OIDC_FULL_NAME"]]
        if os.environ.get("OIDC_FIRST_NAME"):
            user.first_name = payload[os.environ["OIDC_FIRST_NAME"]]
        if os.environ.get("OIDC_LAST_NAME"):
            user.last_name = payload[os.environ["OIDC_LAST_NAME"]]
        user.oidc_groups_hash = self._get_groups_hash(payload)
        user.is_oidc_user = True
        user.is_active = True

        settings = Settings.load()
        if settings.internal_users and user.email:
            user.is_external = True
            for internal_user in settings.internal_users.split(","):
                internal_user = internal_user.strip()
                if re.match(internal_user, user.email):
                    user.is_external = False
                    break
        else:
            user.is_external = False

        try:
            with transaction.atomic():
                user.save()
                self._synchronize_groups(user, payload)
            return user
        except IntegrityError as e:
            # User was most likely created by another request
            existing_user = get_user_by_username(username)
            if not existing_user:
                raise e
            return existing_user

    def _check_user_change(self, user: User, payload: dict) -> User:
        user_changed = False
        if os.environ.get("OIDC_EMAIL") and user.email != payload[os.environ["OIDC_EMAIL"]]:
            user.email = payload[os.environ["OIDC_EMAIL"]]
            user_changed = True
        if os.environ.get("OIDC_FULL_NAME") and user.full_name != payload[os.environ["OIDC_FULL_NAME"]]:
            user.full_name = payload[os.environ["OIDC_FULL_NAME"]]
            user_changed = True
        if os.environ.get("OIDC_FIRST_NAME") and user.first_name != payload[os.environ["OIDC_FIRST_NAME"]]:
            user.first_name = payload[os.environ["OIDC_FIRST_NAME"]]
            user_changed = True
        if os.environ.get("OIDC_LAST_NAME") and user.last_name != payload[os.environ["OIDC_LAST_NAME"]]:
            user.last_name = payload[os.environ["OIDC_LAST_NAME"]]
            user_changed = True
        groups_hash = self._get_groups_hash(payload)
        if user.oidc_groups_hash != groups_hash:
            user.oidc_groups_hash = groups_hash
            self._synchronize_groups(user, payload)
            user_changed = True
        if not user.is_oidc_user:
            user.is_oidc_user = True
            user_changed = True
        if user.has_usable_password():
            user.set_unusable_password()
            user_changed = True

        if user_changed:
            user.save()
        return user

    def _get_groups_from_token(self, payload: dict) -> list:
        if not os.environ.get("OIDC_GROUPS"):
            return []

        groups = payload.get(os.environ["OIDC_GROUPS"])

        if not groups:
            return []

        if isinstance(groups, str):
            groups = [groups]

        if not isinstance(groups, list):
            return []

        return sorted(groups)

    def _get_groups_hash(self, payload: dict) -> str:
        groups = self._get_groups_from_token(payload)
        if groups:
            return hashlib.sha256("".join(groups).encode("UTF-8")).hexdigest()
        return ""

    def _synchronize_groups(self, user: User, payload: dict) -> None:
        groups = Authorization_Group.objects.exclude(oidc_group="")
        for group in groups:
            group.users.remove(user)

        oidc_groups = self._get_groups_from_token(payload)
        authorization_groups = Authorization_Group.objects.filter(oidc_group__in=oidc_groups)
        for authorization_group in authorization_groups:
            user.authorization_groups.add(authorization_group)
