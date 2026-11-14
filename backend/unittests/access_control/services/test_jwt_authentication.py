from datetime import timedelta
from unittest.mock import patch

import jwt
from django.http import HttpRequest
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from application.access_control.models import JWT_Secret
from application.access_control.services.jwt_authentication import (
    JWTAuthentication,
    create_jwt,
)
from unittests.base_test_case import BaseTestCase


class TestFunctions(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.secret = "secret"

    @patch("application.access_control.models.JWT_Secret.load")
    def test_create_jwt_superuser(self, mock):
        jwt_secret = JWT_Secret(secret=self.secret)
        mock.return_value = jwt_secret

        token = create_jwt(self.user_admin)
        payload = jwt.decode(token, self.secret, algorithms="HS256")

        mock.assert_called()
        self.assertEqual(self.user_admin.username, payload["username"])
        self.assertEqual(self.user_admin.first_name, payload["first_name"])
        self.assertEqual(self.user_admin.last_name, payload["last_name"])
        self.assertEqual(self.user_admin.full_name, payload["full_name"])
        # Assert exp time is within 2 seconds of 1 day from now
        current_timestamp = (timezone.now() + timedelta(hours=24)).timestamp()
        exp_delta = current_timestamp - payload["exp"]
        self.assertTrue(0 <= exp_delta <= 2)

    @patch("application.access_control.models.JWT_Secret.load")
    def test_create_jwt_normal_user(self, mock):
        jwt_secret = JWT_Secret(secret=self.secret)
        mock.return_value = jwt_secret

        token = create_jwt(self.user_external)
        payload = jwt.decode(token, self.secret, algorithms="HS256")

        mock.assert_called()
        self.assertEqual(self.user_external.username, payload["username"])
        self.assertEqual(self.user_external.first_name, payload["first_name"])
        self.assertEqual(self.user_external.last_name, payload["last_name"])
        self.assertEqual(self.user_external.full_name, payload["full_name"])
        # Assert exp time is within 2 seconds of 7 days from now
        current_timestamp = (timezone.now() + timedelta(hours=168)).timestamp()
        exp_delta = current_timestamp - payload["exp"]
        self.assertTrue(0 <= exp_delta <= 2)


class TestJWTAuthentication(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

    # --- authenticate ---

    def test_authenticate_no_header(self):
        request = HttpRequest()
        jwt_authentication = JWTAuthentication()
        user = jwt_authentication.authenticate(request)

        self.assertIsNone(user)

    def test_authenticate_invalid_header_1(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header"
        with self.assertRaises(AuthenticationFailed) as e:
            jwt_authentication = JWTAuthentication()
            jwt_authentication.authenticate(request)

        self.assertEqual("Invalid token header: No credentials provided.", str(e.exception))

    def test_authenticate_invalid_header_spaces(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header token_1 token_2"
        with self.assertRaises(AuthenticationFailed) as e:
            jwt_authentication = JWTAuthentication()
            jwt_authentication.authenticate(request)

        self.assertEqual(
            "Invalid token header: Token string should not contain spaces.",
            str(e.exception),
        )

    def test_authenticate_invalid_header_not_utf8(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"JWT \xff"
        with self.assertRaises(AuthenticationFailed) as e:
            JWTAuthentication().authenticate(request)

        self.assertEqual(
            "Invalid token header: Token string should not contain invalid characters.",
            str(e.exception),
        )

    def test_authenticate_wrong_header(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header token"
        jwt_authentication = JWTAuthentication()
        user = jwt_authentication.authenticate(request)

        self.assertIsNone(user)

    @patch("application.access_control.services.jwt_authentication.JWTAuthentication._validate_jwt")
    def test_authenticate_wrong_token(self, mock):
        mock.return_value = None

        with self.assertRaises(AuthenticationFailed) as e:
            request = HttpRequest()
            request.META["HTTP_AUTHORIZATION"] = b"JWT token"
            jwt_authentication = JWTAuthentication()
            jwt_authentication.authenticate(request)

        self.assertEqual("Invalid token.", str(e.exception))

    @patch("application.access_control.services.jwt_authentication.JWTAuthentication._validate_jwt")
    def test_authenticate_user_deactivated(self, mock):
        mock.return_value = self.user_internal
        self.user_internal.is_active = False

        with self.assertRaises(AuthenticationFailed) as e:
            request = HttpRequest()
            request.META["HTTP_AUTHORIZATION"] = b"JWT token"
            jwt_authentication = JWTAuthentication()
            jwt_authentication.authenticate(request)

        self.assertEqual("User is deactivated.", str(e.exception))

        self.user_internal.is_active = True

    @patch("application.access_control.services.jwt_authentication.JWTAuthentication._validate_jwt")
    def test_authenticate_successful(self, mock):
        mock.return_value = self.user_internal

        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"JWT token"
        jwt_authentication = JWTAuthentication()
        user, _ = jwt_authentication.authenticate(request)

        self.assertEqual(self.user_internal, user)

    # --- authenticate_header ---

    def test_authenticate_header(self):
        jwt_authentication = JWTAuthentication()
        self.assertEqual("JWT", jwt_authentication.authenticate_header(None))

    # --- _validate_jwt ---

    @patch("jwt.decode")
    @patch("application.access_control.services.jwt_authentication.get_user_by_username")
    @patch("application.access_control.models.JWT_Secret.load")
    def test_validate_jwt_user(self, secret_mock, get_user_mock, jwt_mock):
        jwt_secret = JWT_Secret(secret="secret")
        secret_mock.return_value = jwt_secret
        get_user_mock.return_value = self.user_internal
        jwt_mock.return_value = {"username": self.user_internal.username}

        jwt_authentication = JWTAuthentication()
        user = jwt_authentication._validate_jwt("token")

        self.assertEqual(self.user_internal.username, user.username)
        secret_mock.assert_called()
        get_user_mock.assert_called_with(self.user_internal.username)
        jwt_mock.assert_called_with("token", "secret", algorithms=["HS256"])

    @patch("jwt.decode")
    @patch("application.access_control.models.JWT_Secret.load")
    def test_validate_jwt_message(self, secret_mock, jwt_mock):
        jwt_secret = JWT_Secret(secret="secret")
        secret_mock.return_value = jwt_secret
        jwt_mock.side_effect = jwt.ExpiredSignatureError("Signature expired")

        with self.assertRaises(AuthenticationFailed) as e:
            jwt_authentication = JWTAuthentication()
            jwt_authentication._validate_jwt("token")

        self.assertEqual("Signature expired", str(e.exception))
        secret_mock.assert_called()
        jwt_mock.assert_called_with("token", "secret", algorithms=["HS256"])
