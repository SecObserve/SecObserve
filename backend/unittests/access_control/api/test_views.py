import os
from datetime import date
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from rest_framework.exceptions import (
    AuthenticationFailed,
    PermissionDenied,
    ValidationError,
)
from rest_framework.test import APIClient

from application.access_control.api.views import _get_authenticated_user
from application.access_control.models import User
from application.access_control.services.oidc_reauthentication import (
    OIDC_CODE_AUTH_TIME_MISSING,
    OIDC_CODE_REAUTHENTICATION_REQUIRED,
    OIDCReauthenticationRequired,
)
from unittests.base_test_case import BaseTestCase


class TestAPIToken(BaseTestCase):
    # --- create_user_api_token ---

    @patch("application.access_control.api.views._get_authenticated_user")
    def test_create_api_token_view_not_authenticated(self, mock):
        mock.side_effect = PermissionDenied("Invalid credentials")

        api_client = APIClient()
        request_data = {"username": "user@example.com", "password": "not-so-secret", "name": "api_token_name"}
        response = api_client.post(reverse("create_user_api_token"), request_data, "json")

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        mock.assert_called_with(request_data)

    @patch("application.access_control.api.views._get_authenticated_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_validation_error(self, api_mock, user_mock):
        api_mock.side_effect = ValidationError("Only one API token per user is allowed.")
        user_mock.return_value = self.user_internal

        api_client = APIClient()
        request_data = {
            "username": "user@example.com",
            "password": "not-so-secret",
            "name": "api_token_name",
            "expiration_date": date.today(),
        }
        response = api_client.post(reverse("create_user_api_token"), request_data, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("Only one API token per user is allowed.", response.data["message"])
        user_mock.assert_called_with(request_data)
        api_mock.assert_called_with(self.user_internal, "api_token_name", date.today())

    @patch("application.access_control.api.views._get_authenticated_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_expiration_date_past(self, api_mock, user_mock):
        api_mock.side_effect = ValidationError("Only one API token per user is allowed.")
        user_mock.return_value = self.user_internal

        api_client = APIClient()
        request_data = {
            "username": "user@example.com",
            "password": "not-so-secret",
            "name": "api_token_name",
            "expiration_date": date(2022, 2, 2),
        }
        response = api_client.post(reverse("create_user_api_token"), request_data, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("Expiration date: Expiration date cannot be in the past", response.data["message"])

    @patch("application.access_control.api.views._get_authenticated_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_successful(self, api_mock, user_mock):
        api_mock.return_value = "api_token"
        user_mock.return_value = self.user_internal

        api_client = APIClient()
        request_data = {"username": "user@example.com", "password": "not-so-secret", "name": "api_token_name"}
        response = api_client.post(reverse("create_user_api_token"), request_data, "json")
        self.assertEqual(201, response.status_code)
        self.assertEqual("api_token", response.data["token"])
        user_mock.assert_called_with(request_data)
        api_mock.assert_called_with(self.user_internal, "api_token_name", None)

    # --- create_user_api_token with OIDC ---

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_oidc_successful(self, api_mock, oidc_mock):
        api_mock.return_value = "api_token"
        oidc_mock.return_value = (self.user_internal, {"auth_time": 1234567890})

        api_client = APIClient()
        request_data = {"name": "api_token_name"}
        response = api_client.post(
            reverse("create_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(201, response.status_code)
        self.assertEqual("api_token", response.data["token"])
        api_mock.assert_called_with(self.user_internal, "api_token_name", None)

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_oidc_reauthentication_required(self, api_mock, oidc_mock):
        oidc_mock.side_effect = OIDCReauthenticationRequired(
            OIDC_CODE_REAUTHENTICATION_REQUIRED, "The authentication is too old"
        )

        api_client = APIClient()
        request_data = {"name": "api_token_name"}
        response = api_client.post(
            reverse("create_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(OIDC_CODE_REAUTHENTICATION_REQUIRED, response.data["code"])
        self.assertEqual("The authentication is too old", response.data["message"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_oidc_auth_time_missing(self, api_mock, oidc_mock):
        oidc_mock.side_effect = OIDCReauthenticationRequired(OIDC_CODE_AUTH_TIME_MISSING, "No auth_time claim")

        api_client = APIClient()
        request_data = {"name": "api_token_name"}
        response = api_client.post(
            reverse("create_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(OIDC_CODE_AUTH_TIME_MISSING, response.data["code"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_oidc_username_mismatch(self, api_mock, oidc_mock):
        oidc_mock.return_value = (self.user_internal, {"auth_time": 1234567890})

        api_client = APIClient()
        request_data = {"username": "another_user@example.com", "name": "api_token_name"}
        response = api_client.post(
            reverse("create_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(400, response.status_code)
        self.assertEqual("Username does not match the authenticated user", response.data["message"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views._get_authenticated_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_api_token_header_uses_password(self, api_mock, user_mock):
        # A leaked API token must not be able to create new API tokens,
        # only the Authorization header with an OIDC token is accepted.
        api_mock.return_value = "api_token"
        user_mock.return_value = self.user_internal

        api_client = APIClient()
        request_data = {"username": "user@example.com", "password": "not-so-secret", "name": "api_token_name"}
        response = api_client.post(
            reverse("create_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="APIToken api_token_secret"
        )

        self.assertEqual(201, response.status_code)
        user_mock.assert_called_with(request_data)

    @patch.dict(os.environ, {"OIDC_AUTHORITY": ""})
    def test_create_api_token_view_bearer_header_without_oidc(self):
        # Without OIDC configured, a Bearer header must not lead to an internal server error
        api_client = APIClient()
        request_data = {"name": "api_token_name"}
        response = api_client.post(
            reverse("create_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])

    # --- revoke_user_api_token ---

    @patch("application.access_control.api.views._get_authenticated_user")
    def test_revoke_api_token_view_not_authenticated(self, mock):
        mock.side_effect = PermissionDenied("Invalid credentials")

        api_client = APIClient()
        request_data = {"username": "user@example.com", "password": "not-so-secret", "name": "api_token_name"}
        response = api_client.post(reverse("revoke_user_api_token"), request_data, "json")

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        mock.assert_called_with(request_data)

    @patch("application.access_control.api.views._get_authenticated_user")
    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_successful(self, revoke_mock, user_mock):
        user_mock.return_value = self.user_internal

        api_client = APIClient()
        request_data = {"username": "user@example.com", "password": "not-so-secret", "name": "api_token_name"}
        response = api_client.post(reverse("revoke_user_api_token"), request_data, "json")

        self.assertEqual(204, response.status_code)
        user_mock.assert_called_with(request_data)
        revoke_mock.assert_called_with(self.user_internal, "api_token_name")

    # --- revoke_user_api_token with OIDC ---

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_oidc_successful(self, revoke_mock, oidc_mock):
        oidc_mock.return_value = (self.user_internal, {"auth_time": 1234567890})

        api_client = APIClient()
        request_data = {"name": "api_token_name"}
        response = api_client.post(
            reverse("revoke_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(204, response.status_code)
        revoke_mock.assert_called_with(self.user_internal, "api_token_name")

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_oidc_reauthentication_required(self, revoke_mock, oidc_mock):
        oidc_mock.side_effect = OIDCReauthenticationRequired(
            OIDC_CODE_REAUTHENTICATION_REQUIRED, "The authentication is too old"
        )

        api_client = APIClient()
        request_data = {"name": "api_token_name"}
        response = api_client.post(
            reverse("revoke_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(OIDC_CODE_REAUTHENTICATION_REQUIRED, response.data["code"])
        revoke_mock.assert_not_called()

    @patch.dict(os.environ, {"OIDC_AUTHORITY": ""})
    def test_revoke_api_token_view_bearer_header_without_oidc(self):
        # Without OIDC configured, a Bearer header must not lead to an internal server error
        api_client = APIClient()
        request_data = {"name": "api_token_name"}
        response = api_client.post(
            reverse("revoke_user_api_token"), request_data, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])


class TestAPITokenAuthenticationRequired(BaseTestCase):
    """Creating and revoking a user API token needs either username and password or an
    OIDC token, everything else has to be refused.

    These tests deliberately do not mock `_get_authenticated_user` or `django_authenticate`,
    so that the credentials are really checked and not only the handling of a refusal.
    """

    PASSWORD = "not-so-secret-password"  # nosec B105
    # eliminate false positive, the password is only used for a user in the test database

    def setUp(self) -> None:
        super().setUp()
        self.user_with_password = User.objects.create_user(
            username="user_with_password@example.com", password=self.PASSWORD
        )

    # --- no credentials at all ---

    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_without_credentials(self, api_mock):
        api_client = APIClient()
        response = api_client.post(reverse("create_user_api_token"), {"name": "api_token_name"}, "json")

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_without_credentials(self, revoke_mock):
        api_client = APIClient()
        response = api_client.post(reverse("revoke_user_api_token"), {"name": "api_token_name"}, "json")

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        revoke_mock.assert_not_called()

    # --- wrong password ---

    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_wrong_password(self, api_mock):
        api_client = APIClient()
        request_data = {
            "username": self.user_with_password.username,
            "password": "wrong-password",
            "name": "api_token_name",
        }
        response = api_client.post(reverse("create_user_api_token"), request_data, "json")

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_wrong_password(self, revoke_mock):
        api_client = APIClient()
        request_data = {
            "username": self.user_with_password.username,
            "password": "wrong-password",
            "name": "api_token_name",
        }
        response = api_client.post(reverse("revoke_user_api_token"), request_data, "json")

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        revoke_mock.assert_not_called()

    # --- correct password, to show that the tests above do not refuse everything ---

    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_correct_password(self, api_mock):
        api_mock.return_value = "api_token"

        api_client = APIClient()
        request_data = {
            "username": self.user_with_password.username,
            "password": self.PASSWORD,
            "name": "api_token_name",
        }
        response = api_client.post(reverse("create_user_api_token"), request_data, "json")

        self.assertEqual(201, response.status_code)
        api_mock.assert_called_with(self.user_with_password, "api_token_name", None)

    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_correct_password(self, revoke_mock):
        api_client = APIClient()
        request_data = {
            "username": self.user_with_password.username,
            "password": self.PASSWORD,
            "name": "api_token_name",
        }
        response = api_client.post(reverse("revoke_user_api_token"), request_data, "json")

        self.assertEqual(204, response.status_code)
        revoke_mock.assert_called_with(self.user_with_password, "api_token_name")

    # --- other Authorization headers must not replace the password ---

    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_jwt_header_without_password(self, api_mock):
        # A JWT of a signed in user must not be able to create an API token without a password
        api_client = APIClient()
        response = api_client.post(
            reverse("create_user_api_token"),
            {"name": "api_token_name"},
            "json",
            HTTP_AUTHORIZATION="JWT jwt_of_the_user",
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_api_token_header_without_password(self, api_mock):
        # A leaked API token must not be able to create further API tokens
        api_client = APIClient()
        response = api_client.post(
            reverse("create_user_api_token"),
            {"name": "api_token_name"},
            "json",
            HTTP_AUTHORIZATION="APIToken api_token_secret",
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_jwt_header_without_password(self, revoke_mock):
        api_client = APIClient()
        response = api_client.post(
            reverse("revoke_user_api_token"),
            {"name": "api_token_name"},
            "json",
            HTTP_AUTHORIZATION="JWT jwt_of_the_user",
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        revoke_mock.assert_not_called()

    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_api_token_header_without_password(self, revoke_mock):
        api_client = APIClient()
        response = api_client.post(
            reverse("revoke_user_api_token"),
            {"name": "api_token_name"},
            "json",
            HTTP_AUTHORIZATION="APIToken api_token_secret",
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        revoke_mock.assert_not_called()

    # --- invalid OIDC token ---

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.create_user_api_token")
    def test_create_api_token_view_invalid_oidc_token(self, api_mock, oidc_mock):
        oidc_mock.side_effect = AuthenticationFailed("Invalid token.")

        api_client = APIClient()
        response = api_client.post(
            reverse("create_user_api_token"), {"name": "api_token_name"}, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid token.", response.data["message"])
        api_mock.assert_not_called()

    @patch("application.access_control.api.views.get_freshly_authenticated_oidc_user")
    @patch("application.access_control.api.views.revoke_user_api_token")
    def test_revoke_api_token_view_invalid_oidc_token(self, revoke_mock, oidc_mock):
        oidc_mock.side_effect = AuthenticationFailed("Invalid token.")

        api_client = APIClient()
        response = api_client.post(
            reverse("revoke_user_api_token"), {"name": "api_token_name"}, "json", HTTP_AUTHORIZATION="Bearer token"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid token.", response.data["message"])
        revoke_mock.assert_not_called()


class TestAuthenticate(BaseTestCase):
    @patch("application.access_control.api.views._get_authenticated_user")
    def test_authenticate_view_not_authenticated(self, mock):
        mock.side_effect = PermissionDenied("Invalid credentials")

        api_client = APIClient()
        request_data = {"username": "user@example.com", "password": "not-so-secret"}
        response = api_client.post(reverse("authenticate"), request_data, "json")

        self.assertEqual(403, response.status_code)
        self.assertEqual("Invalid credentials", response.data["message"])
        mock.assert_called_with(request_data)

    @patch("application.access_control.api.views._get_authenticated_user")
    @patch("application.access_control.api.views.create_jwt")
    def test_authenticate_view_successful(self, jwt_mock, user_mock):
        jwt_mock.return_value = "token"
        user_mock.return_value = self.user_internal

        api_client = APIClient()
        request_data = {"username": "user@example.com", "password": "not-so-secret"}
        response = api_client.post(reverse("authenticate"), request_data, "json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("token", response.data["jwt"])
        self.assertEqual(self.user_internal.username, response.data["user"]["username"])
        user_mock.assert_called_with(request_data)
        jwt_mock.assert_called_with(self.user_internal)


class TestGetAuthenticatedUser(BaseTestCase):
    @patch("application.access_control.api.views.django_authenticate")
    def test_get_authenticated_user_not_authenticated(self, mock):
        mock.return_value = None

        data = {"username": "user@example.com", "password": "not_so_secret"}
        with self.assertRaises(PermissionDenied) as e:
            _get_authenticated_user(data)

        self.assertEqual("Invalid credentials", str(e.exception))
        mock.assert_called_with(username="user@example.com", password="not_so_secret")

    @patch("application.access_control.api.views.django_authenticate")
    def test_get_authenticated_user_successful(self, mock):
        mock.return_value = self.user_internal

        data = {"username": "user@example.com", "password": "not_so_secret"}
        self.assertEqual(self.user_internal, _get_authenticated_user(data))
        mock.assert_called_with(username="user@example.com", password="not_so_secret")


class TestChangePassword(BaseTestCase):
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.api.views.UserViewSet.get_object")
    @patch("application.access_control.models.User.set_password")
    @patch("application.access_control.models.User.save")
    def test_change_password_unusable_password(
        self, save_mock, set_password_mock, get_object_mock, authentication_mock
    ):
        self.user_internal.set_unusable_password()
        get_object_mock.return_value = self.user_internal
        authentication_mock.return_value = self.user_admin, None

        api_client = APIClient()
        request_data = {
            "current_password": "current",
            "new_password_1": "new",
            "new_password_2": "new",
        }
        response = api_client.patch("/api/users/123/change_password/", request_data, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("User's password cannot be changed", response.data["message"])
        save_mock.assert_not_called()
        set_password_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.api.views.UserViewSet.get_object")
    @patch("application.access_control.models.User.set_password")
    @patch("application.access_control.models.User.save")
    def test_change_password_oidc_user(self, save_mock, set_password_mock, get_object_mock, authentication_mock):
        self.user_internal.is_oidc_user = True
        get_object_mock.return_value = self.user_internal
        authentication_mock.return_value = self.user_admin, None

        api_client = APIClient()
        request_data = {
            "current_password": "current",
            "new_password_1": "new",
            "new_password_2": "new",
        }
        response = api_client.patch("/api/users/123/change_password/", request_data, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("User's password cannot be changed", response.data["message"])
        save_mock.assert_not_called()
        set_password_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.api.views.UserViewSet.get_object")
    @patch("application.access_control.models.User.set_password")
    @patch("application.access_control.models.User.save")
    def test_change_password_do_not_match(self, save_mock, set_password_mock, get_object_mock, authentication_mock):
        get_object_mock.return_value = self.user_internal
        authentication_mock.return_value = self.user_admin, None

        api_client = APIClient()
        request_data = {
            "current_password": "current",
            "new_password_1": "new_1",
            "new_password_2": "new_2",
        }
        response = api_client.patch("/api/users/123/change_password/", request_data, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("The new passwords do not match", response.data["message"])
        save_mock.assert_not_called()
        set_password_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.api.views.UserViewSet.get_object")
    @patch("application.access_control.models.User.set_password")
    @patch("application.access_control.models.User.save")
    @patch("application.access_control.api.views.django_authenticate")
    def test_change_password_current_password_incorrect(
        self,
        django_authenticate_mock,
        save_mock,
        set_password_mock,
        get_object_mock,
        authentication_mock,
    ):
        get_object_mock.return_value = self.user_internal
        authentication_mock.return_value = self.user_admin, None
        django_authenticate_mock.return_value = None

        api_client = APIClient()
        request_data = {
            "current_password": "current",
            "new_password_1": "new",
            "new_password_2": "new",
        }
        response = api_client.patch("/api/users/123/change_password/", request_data, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("Current password is incorrect", response.data["message"])
        django_authenticate_mock.assert_called_with(username="user_admin@example.com", password="current")
        save_mock.assert_not_called()
        set_password_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.api.views.UserViewSet.get_object")
    @patch("application.access_control.models.User.set_password")
    @patch("application.access_control.models.User.save")
    @patch("application.access_control.api.views.django_authenticate")
    @patch("application.access_control.api.views.validate_password")
    def test_change_password_not_valid(
        self,
        validate_password_mock,
        django_authenticate_mock,
        save_mock,
        set_password_mock,
        get_object_mock,
        authentication_mock,
    ):
        get_object_mock.return_value = self.user_internal
        authentication_mock.return_value = self.user_admin, None
        django_authenticate_mock.return_value = self.user_admin
        validate_password_mock.side_effect = DjangoValidationError(["too_short", "too_common"])

        api_client = APIClient()
        request_data = {
            "current_password": "current",
            "new_password_1": "new",
            "new_password_2": "new",
        }
        response = api_client.patch("/api/users/123/change_password/", request_data, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("too_short / too_common", response.data["message"])
        django_authenticate_mock.assert_called_with(username="user_admin@example.com", password="current")
        save_mock.assert_not_called()
        set_password_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.api.views.UserViewSet.get_object")
    @patch("application.access_control.models.User.set_password")
    @patch("application.access_control.models.User.save")
    @patch("application.access_control.api.views.django_authenticate")
    @patch("application.access_control.api.views.validate_password")
    def test_change_password_successful(
        self,
        validate_password_mock,
        django_authenticate_mock,
        save_mock,
        set_password_mock,
        get_object_mock,
        authentication_mock,
    ):
        get_object_mock.return_value = self.user_internal
        authentication_mock.return_value = self.user_admin, None
        django_authenticate_mock.return_value = self.user_admin
        validate_password_mock.return_value = None

        api_client = APIClient()
        request_data = {
            "current_password": "current",
            "new_password_1": "new",
            "new_password_2": "new",
        }
        response = api_client.patch("/api/users/123/change_password/", request_data, "json")

        self.assertEqual(204, response.status_code)
        self.assertEqual(None, response.data)
        django_authenticate_mock.assert_called_with(username="user_admin@example.com", password="current")
        save_mock.assert_called()
        set_password_mock.assert_called_with("new")


class TestMySettings(BaseTestCase):
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_email_active_without_email(self, save_mock, authentication_mock):
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.patch("/api/users/my_settings/", {"notification_email_active": True}, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            "Notification email active: Cannot be activated without an email address", response.data["message"]
        )
        save_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_ms_teams_active_without_webhook(self, save_mock, authentication_mock):
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.patch("/api/users/my_settings/", {"notification_ms_teams_active": True}, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            "Notification ms teams active: Cannot be activated without a webhook", response.data["message"]
        )
        save_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_slack_active_without_webhook(self, save_mock, authentication_mock):
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.patch("/api/users/my_settings/", {"notification_slack_active": True}, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("Notification slack active: Cannot be activated without a webhook", response.data["message"])
        save_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_channel_activated_with_webhook(self, save_mock, authentication_mock):
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        request_data = {
            "notification_slack_webhook": "https://example.com/slack",
            "notification_slack_active": True,
        }
        response = api_client.patch("/api/users/my_settings/", request_data, "json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("https://example.com/slack", self.user_internal.notification_slack_webhook)
        self.assertTrue(self.user_internal.notification_slack_active)
        save_mock.assert_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_channel_activated_with_stored_webhook(self, save_mock, authentication_mock):
        """The webhook does not have to be part of the request, it can have been stored before."""
        self.user_internal.notification_slack_webhook = "https://example.com/slack"
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.patch("/api/users/my_settings/", {"notification_slack_active": True}, "json")

        self.assertEqual(200, response.status_code)
        self.assertTrue(self.user_internal.notification_slack_active)
        save_mock.assert_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_email_of_oidc_user(self, save_mock, authentication_mock):
        self.user_internal.is_oidc_user = True
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.patch("/api/users/my_settings/", {"email": "changed@example.com"}, "json")

        self.assertEqual(400, response.status_code)
        self.assertEqual("Email: Cannot be changed for an OIDC user", response.data["message"])
        save_mock.assert_not_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_unchanged_email_of_oidc_user(self, save_mock, authentication_mock):
        self.user_internal.is_oidc_user = True
        self.user_internal.email = "oidc@example.com"
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.patch("/api/users/my_settings/", {"email": "oidc@example.com"}, "json")

        self.assertEqual(200, response.status_code)
        save_mock.assert_called()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.access_control.models.User.save")
    def test_my_settings_email_successful(self, save_mock, authentication_mock):
        authentication_mock.return_value = self.user_internal, None

        api_client = APIClient()
        request_data = {
            "email": "internal@example.com",
            "notification_email_active": True,
        }
        response = api_client.patch("/api/users/my_settings/", request_data, "json")

        self.assertEqual(200, response.status_code)
        self.assertEqual("internal@example.com", self.user_internal.email)
        self.assertTrue(self.user_internal.notification_email_active)
        save_mock.assert_called()
