from datetime import date
from unittest.mock import patch

from argon2 import PasswordHasher
from argon2.profiles import RFC_9106_LOW_MEMORY
from django.http import HttpRequest
from rest_framework.exceptions import AuthenticationFailed

from application.access_control.models import API_Token_Multiple
from application.access_control.services.api_token_authentication import (
    APITokenAuthentication,
)
from application.access_control.services.user_api_token import (
    create_user_api_token,
    revoke_user_api_token,
)
from unittests.base_test_case import BaseTestCase


class TestAPITokenAuthentication(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.api_token = "api_token"
        ph = PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)
        api_token_hash = ph.hash(self.api_token)

        self.api_token_object = API_Token_Multiple(user=self.user_internal, api_token_hash=api_token_hash)
        self.api_tokens = [self.api_token_object]

    # --- authenticate_header ---

    def test_authenticate_header(self):
        api_token_authentication = APITokenAuthentication()
        self.assertEqual("APIToken", api_token_authentication.authenticate_header(None))

    # --- validate_api_token ---

    @patch("application.access_control.models.API_Token_Multiple.objects.all")
    def test_validate_api_token_none(self, mock):
        mock.return_value = self.api_tokens

        api_token_authentication = APITokenAuthentication()
        user = api_token_authentication._validate_api_token("sss")
        self.assertIsNone(user)

    @patch("application.access_control.models.API_Token_Multiple.objects.all")
    def test_validate_api_token_found(self, mock):
        mock.return_value = self.api_tokens

        api_token_authentication = APITokenAuthentication()
        api_token = api_token_authentication._validate_api_token(self.api_token)
        self.assertEqual(self.api_token_object, api_token)

    # --- authenticate ---

    def test_authenticate_no_header(self):
        request = HttpRequest()
        api_token_authentication = APITokenAuthentication()
        user = api_token_authentication.authenticate(request)

        self.assertIsNone(user)

    def test_authenticate_invalid_header_1(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header"
        with self.assertRaises(AuthenticationFailed) as e:
            api_token_authentication = APITokenAuthentication()
            api_token_authentication.authenticate(request)

        self.assertEqual("Invalid token header: No credentials provided.", str(e.exception))

    def test_authenticate_invalid_header_spaces(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header token_1 token_2"
        with self.assertRaises(AuthenticationFailed) as e:
            api_token_authentication = APITokenAuthentication()
            api_token_authentication.authenticate(request)

        self.assertEqual(
            "Invalid token header: Token string should not contain spaces.",
            str(e.exception),
        )

    def test_authenticate_invalid_header_not_utf8(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"APIToken \xff"
        with self.assertRaises(AuthenticationFailed) as e:
            APITokenAuthentication().authenticate(request)

        self.assertEqual(
            "Invalid token header: Token string should not contain invalid characters.",
            str(e.exception),
        )

    def test_authenticate_wrong_header(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header token"
        api_token_authentication = APITokenAuthentication()
        user = api_token_authentication.authenticate(request)

        self.assertIsNone(user)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication._validate_api_token")
    def test_authenticate_wrong_token(self, mock):
        mock.return_value = None

        with self.assertRaises(AuthenticationFailed) as e:
            request = HttpRequest()
            request.META["HTTP_AUTHORIZATION"] = b"APIToken token"
            api_token_authentication = APITokenAuthentication()
            api_token_authentication.authenticate(request)

        self.assertEqual("Invalid API token.", str(e.exception))

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication._validate_api_token")
    def test_authenticate_user_deactivated(self, mock):
        self.user_internal.is_active = False
        mock.return_value = API_Token_Multiple(user=self.user_internal)

        with self.assertRaises(AuthenticationFailed) as e:
            request = HttpRequest()
            request.META["HTTP_AUTHORIZATION"] = b"APIToken token"
            api_token_authentication = APITokenAuthentication()
            api_token_authentication.authenticate(request)

        self.assertEqual("User is deactivated.", str(e.exception))

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication._validate_api_token")
    def test_authenticate_expired_token(self, mock):
        mock.return_value = API_Token_Multiple(user=self.user_internal, expiration_date=date(2020, 1, 1))

        with self.assertRaises(AuthenticationFailed) as e:
            request = HttpRequest()
            request.META["HTTP_AUTHORIZATION"] = b"APIToken token"
            api_token_authentication = APITokenAuthentication()
            api_token_authentication.authenticate(request)

        self.assertEqual("API token has expired.", str(e.exception))

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication._validate_api_token")
    def test_authenticate_successful(self, mock):
        mock.return_value = self.api_token_object

        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"APIToken token"
        api_token_authentication = APITokenAuthentication()
        user, _ = api_token_authentication.authenticate(request)

        self.assertEqual(self.user_internal, user)
