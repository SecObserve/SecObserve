import os
from datetime import datetime, timezone
from unittest.mock import patch

from django.http import HttpRequest

from application.access_control.services.oidc_reauthentication import (
    OIDC_CODE_AUTH_TIME_MISSING,
    OIDC_CODE_REAUTHENTICATION_REQUIRED,
    OIDCReauthenticationRequired,
    get_freshly_authenticated_oidc_user,
    has_oidc_bearer_header,
    oidc_is_configured,
)
from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase


def _now() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _request() -> HttpRequest:
    request = HttpRequest()
    request.META["HTTP_AUTHORIZATION"] = b"Bearer token"
    return request


class TestOIDCIsConfigured(BaseTestCase):
    def test_oidc_is_configured(self):
        self.assertTrue(oidc_is_configured())

    @patch.dict(os.environ, {"OIDC_AUTHORITY": ""})
    def test_oidc_is_not_configured(self):
        self.assertFalse(oidc_is_configured())


class TestHasOIDCBearerHeader(BaseTestCase):
    def test_no_header(self):
        self.assertFalse(has_oidc_bearer_header(HttpRequest()))

    def test_bearer_header(self):
        self.assertTrue(has_oidc_bearer_header(_request()))

    def test_bearer_header_lowercase(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"bearer token"
        self.assertTrue(has_oidc_bearer_header(request))

    def test_api_token_header(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"APIToken token"
        self.assertFalse(has_oidc_bearer_header(request))

    def test_jwt_header(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"JWT token"
        self.assertFalse(has_oidc_bearer_header(request))

    def test_incomplete_header(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"Bearer"
        self.assertFalse(has_oidc_bearer_header(request))


class TestGetFreshlyAuthenticatedOIDCUser(BaseTestCase):
    def _set_max_authentication_age(self, max_authentication_age_minutes: int, clock_skew: int = 0) -> None:
        settings = Settings.load()
        settings.oidc_api_token_max_authentication_age = max_authentication_age_minutes
        settings.oidc_clock_skew = clock_skew
        settings.save()

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_authentication_fresh(self, authenticate_mock):
        payload = {"auth_time": _now() - 10}
        authenticate_mock.return_value = (self.user_internal, payload)
        self._set_max_authentication_age(5)

        user, returned_payload = get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(self.user_internal, user)
        self.assertEqual(payload, returned_payload)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_authentication_within_max_authentication_age(self, authenticate_mock):
        # 5 minutes are 300 seconds, so an authentication 299 seconds ago is still fresh
        authenticate_mock.return_value = (self.user_internal, {"auth_time": _now() - 299})
        self._set_max_authentication_age(5)

        user, _ = get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(self.user_internal, user)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_authentication_too_old(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"auth_time": _now() - 301})
        self._set_max_authentication_age(5)

        with self.assertRaises(OIDCReauthenticationRequired) as e:
            get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(OIDC_CODE_REAUTHENTICATION_REQUIRED, e.exception.code)
        self.assertEqual(
            "The authentication is older than 5 minutes, please authenticate again to manage API tokens",
            e.exception.message,
        )

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_authentication_too_old_but_within_clock_skew(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"auth_time": _now() - 310})
        self._set_max_authentication_age(5, clock_skew=30)

        user, _ = get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(self.user_internal, user)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_authentication_in_the_future_within_clock_skew(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"auth_time": _now() + 20})
        self._set_max_authentication_age(5, clock_skew=30)

        user, _ = get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(self.user_internal, user)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_authentication_in_the_future_beyond_clock_skew(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"auth_time": _now() + 60})
        self._set_max_authentication_age(5, clock_skew=30)

        with self.assertRaises(OIDCReauthenticationRequired) as e:
            get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(OIDC_CODE_REAUTHENTICATION_REQUIRED, e.exception.code)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_auth_time_as_string(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"auth_time": str(_now() - 10)})
        self._set_max_authentication_age(5)

        user, _ = get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(self.user_internal, user)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_auth_time_missing(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"preferred_username": "user"})
        self._set_max_authentication_age(5)

        with self.assertRaises(OIDCReauthenticationRequired) as e:
            get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(OIDC_CODE_AUTH_TIME_MISSING, e.exception.code)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_auth_time_invalid(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"auth_time": "not_a_number"})
        self._set_max_authentication_age(5)

        with self.assertRaises(OIDCReauthenticationRequired) as e:
            get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(OIDC_CODE_AUTH_TIME_MISSING, e.exception.code)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_check_disabled_with_old_authentication(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"auth_time": _now() - 99999})
        self._set_max_authentication_age(0)

        user, _ = get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(self.user_internal, user)

    @patch("application.access_control.services.oidc_reauthentication.OIDCAuthentication.authenticate")
    def test_check_disabled_without_auth_time(self, authenticate_mock):
        authenticate_mock.return_value = (self.user_internal, {"preferred_username": "user"})
        self._set_max_authentication_age(0)

        user, _ = get_freshly_authenticated_oidc_user(_request())

        self.assertEqual(self.user_internal, user)
