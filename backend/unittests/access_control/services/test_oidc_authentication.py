from unittest.mock import patch

import jwt
from django.core.management import call_command
from django.http import HttpRequest
from rest_framework.exceptions import AuthenticationFailed

from application.access_control.models import User
from application.access_control.services.oidc_authentication import OIDCAuthentication
from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase


class TestOIDCAuthentication(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

    # --- authenticate ---

    def test_authenticate_no_header(self):
        request = HttpRequest()
        oidc_authentication = OIDCAuthentication()
        user = oidc_authentication.authenticate(request)

        self.assertIsNone(user)

    def test_authenticate_invalid_header_1(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header"
        with self.assertRaises(AuthenticationFailed) as e:
            oidc_authentication = OIDCAuthentication()
            oidc_authentication.authenticate(request)

        self.assertEqual("Invalid token header: No credentials provided.", str(e.exception))

    def test_authenticate_invalid_header_spaces(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header token_1 token_2"
        with self.assertRaises(AuthenticationFailed) as e:
            oidc_authentication = OIDCAuthentication()
            oidc_authentication.authenticate(request)

        self.assertEqual(
            "Invalid token header: Token string should not contain spaces.",
            str(e.exception),
        )

    def test_authenticate_wrong_header(self):
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"header token"
        oidc_authentication = OIDCAuthentication()
        user = oidc_authentication.authenticate(request)

        self.assertIsNone(user)

    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._validate_jwt")
    def test_authenticate_wrong_token(self, mock):
        mock.return_value = None

        with self.assertRaises(AuthenticationFailed) as e:
            request = HttpRequest()
            request.META["HTTP_AUTHORIZATION"] = b"Bearer token"
            oidc_authentication = OIDCAuthentication()
            oidc_authentication.authenticate(request)

        self.assertEqual("Invalid token.", str(e.exception))

    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._validate_jwt")
    def test_authenticate_user_deactivated(self, mock):
        mock.return_value = self.user_internal
        self.user_internal.is_active = False

        with self.assertRaises(AuthenticationFailed) as e:
            request = HttpRequest()
            request.META["HTTP_AUTHORIZATION"] = b"Bearer token"
            oidc_authentication = OIDCAuthentication()
            oidc_authentication.authenticate(request)

        self.assertEqual("User is deactivated.", str(e.exception))

        self.user_internal.is_active = True

    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._validate_jwt")
    def test_authenticate_successful(self, mock):
        mock.return_value = self.user_internal

        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = b"Bearer token"
        oidc_authentication = OIDCAuthentication()
        user, _ = oidc_authentication.authenticate(request)

        self.assertEqual(self.user_internal, user)

    # --- authenticate_header ---

    def test_authenticate_header(self):
        oidc_authentication = OIDCAuthentication()
        self.assertEqual("Bearer", oidc_authentication.authenticate_header(None))

    # --- _validate_jwt ---

    @patch("jwt.decode")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._get_jwks_uri")
    @patch("jwt.PyJWKClient.__init__")
    @patch("jwt.PyJWKClient.get_signing_key_from_jwt")
    def test_validate_jwt_message(self, get_signing_key_mock, pyjwkclient_mock, jwks_uri_mock, jwt_mock):
        jwks_uri_mock.return_value = "test_jwks_uri"
        pyjwkclient_mock.return_value = None
        mock_py_jwk = MockPyJWK("test_key")
        get_signing_key_mock.return_value = mock_py_jwk
        jwt_mock.side_effect = jwt.ExpiredSignatureError("Signature expired")

        settings = Settings.load()
        settings.oidc_clock_skew = 9

        with self.assertRaises(AuthenticationFailed) as e:
            oidc_authentication = OIDCAuthentication()
            oidc_authentication._validate_jwt("token")

        self.assertEqual("Signature expired", str(e.exception))
        jwks_uri_mock.assert_called_once()
        pyjwkclient_mock.assert_called_once_with("test_jwks_uri")
        get_signing_key_mock.assert_called_once_with("token")
        jwt_mock.assert_called_with(
            jwt="token",
            options={
                "verify_signature": True,
                "verify_aud": True,
                "strict_aud": True,
                "require": ["exp"],
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
            },
            key="test_key",
            algorithms=["RS256", "RS384", "RS512", "ES256 ", "ES384", "ES512", "EdDSA"],
            audience="client_id",
            leeway=9,
        )

    @patch("jwt.decode")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._get_jwks_uri")
    @patch("jwt.PyJWKClient.__init__")
    @patch("jwt.PyJWKClient.get_signing_key_from_jwt")
    @patch("application.access_control.services.oidc_authentication.get_user_by_username")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._create_user")
    def test_validate_jwt_user_not_found(
        self,
        create_user_mock,
        get_user_mock,
        get_signing_key_mock,
        pyjwkclient_mock,
        jwks_uri_mock,
        jwt_mock,
    ):
        jwks_uri_mock.return_value = "test_jwks_uri"
        pyjwkclient_mock.return_value = None
        mock_py_jwk = MockPyJWK("test_key")
        get_signing_key_mock.return_value = mock_py_jwk
        jwt_mock.return_value = {"preferred_username": "test_username"}
        get_user_mock.return_value = None
        expected_user = User(username="test_username")
        create_user_mock.return_value = expected_user

        settings = Settings.load()
        settings.oidc_clock_skew = 7

        oidc_authentication = OIDCAuthentication()
        user = oidc_authentication._validate_jwt("token")

        self.assertEqual(user, expected_user)
        get_user_mock.assert_called_with("test_username")
        jwks_uri_mock.assert_called_once()
        pyjwkclient_mock.assert_called_once_with("test_jwks_uri")
        get_signing_key_mock.assert_called_once_with("token")
        jwt_mock.assert_called_with(
            jwt="token",
            options={
                "verify_signature": True,
                "verify_aud": True,
                "strict_aud": True,
                "require": ["exp"],
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
            },
            key="test_key",
            algorithms=["RS256", "RS384", "RS512", "ES256 ", "ES384", "ES512", "EdDSA"],
            audience="client_id",
            leeway=7,
        )
        create_user_mock.assert_called_once_with("test_username", {"preferred_username": "test_username"})

    @patch("jwt.decode")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._get_jwks_uri")
    @patch("jwt.PyJWKClient.__init__")
    @patch("jwt.PyJWKClient.get_signing_key_from_jwt")
    @patch("application.access_control.services.oidc_authentication.get_user_by_username")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._check_user_change")
    def test_validate_jwt_user_found(
        self,
        check_user_change_mock,
        get_user_mock,
        get_signing_key_mock,
        pyjwkclient_mock,
        jwks_uri_mock,
        jwt_mock,
    ):
        jwks_uri_mock.return_value = "test_jwks_uri"
        pyjwkclient_mock.return_value = None
        mock_py_jwk = MockPyJWK("test_key")
        get_signing_key_mock.return_value = mock_py_jwk
        jwt_mock.return_value = {"preferred_username": self.user_internal.username}
        get_user_mock.return_value = self.user_internal
        check_user_change_mock.return_value = self.user_internal

        settings = Settings.load()
        settings.oidc_clock_skew = 5

        oidc_authentication = OIDCAuthentication()
        user = oidc_authentication._validate_jwt("token")

        self.assertEqual(self.user_internal, user)
        get_user_mock.assert_called_with(self.user_internal.username)
        jwks_uri_mock.assert_called_once()
        pyjwkclient_mock.assert_called_once_with("test_jwks_uri")
        get_signing_key_mock.assert_called_once_with("token")
        jwt_mock.assert_called_with(
            jwt="token",
            options={
                "verify_signature": True,
                "verify_aud": True,
                "strict_aud": True,
                "require": ["exp"],
                "verify_iat": True,
                "verify_exp": True,
                "verify_nbf": True,
            },
            key="test_key",
            algorithms=["RS256", "RS384", "RS512", "ES256 ", "ES384", "ES512", "EdDSA"],
            audience="client_id",
            leeway=5,
        )
        check_user_change_mock.assert_called_once_with(
            self.user_internal, {"preferred_username": self.user_internal.username}
        )

    @patch("requests.request")
    def test_get_jwks_uri(self, requests_mock):
        requests_mock.return_value = MockResponse()
        oidc_authentication = OIDCAuthentication()
        jwks_uri = oidc_authentication._get_jwks_uri()

        self.assertEqual("https://authority/.well-known/jwks.json", jwks_uri)
        requests_mock.assert_called_once_with(
            method="GET",
            url="https://authority/.well-known/openid-configuration",
            timeout=60,
        )

    @patch("application.access_control.services.oidc_authentication.User.save")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._synchronize_groups")
    def test_create_user(self, synchronize_groups_mock, user_save_mock):
        oidc_authentication = OIDCAuthentication()
        payload = {
            "preferred_username": "test_username",
            "given_name": "test_first_name",
            "family_name": "test_last_name",
            "name": "test_full_name",
            "email": "test_email",
            "groups": ["test_group_1", "test_group_2"],
        }

        user = oidc_authentication._create_user("test_username", payload)

        self.assertEqual("test_username", user.username)
        self.assertEqual("test_first_name", user.first_name)
        self.assertEqual("test_last_name", user.last_name)
        self.assertEqual("test_full_name", user.full_name)
        self.assertEqual("test_email", user.email)
        self.assertEqual(
            "27cbb2858ce86012e498c8102d24d066837d67beec8c180f5e85e652df700c9f",
            user.oidc_groups_hash,
        )
        self.assertFalse(user.is_external)

        user_save_mock.assert_called_once()
        synchronize_groups_mock.assert_called_with(user, payload)

    @patch("application.access_control.services.oidc_authentication.User.save")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._synchronize_groups")
    def test_create_user_internal(self, synchronize_groups_mock, user_save_mock):
        settings = Settings.load()
        settings.internal_users = ".*@example.com, .*@test.com"
        settings.save()

        oidc_authentication = OIDCAuthentication()
        payload = {
            "preferred_username": "test_username",
            "given_name": "test_first_name",
            "family_name": "test_last_name",
            "name": "test_full_name",
            "email": "test_email@test.com",
            "groups": ["test_group_1", "test_group_2"],
        }

        user = oidc_authentication._create_user("test_username", payload)

        self.assertEqual("test_username", user.username)
        self.assertEqual("test_first_name", user.first_name)
        self.assertEqual("test_last_name", user.last_name)
        self.assertEqual("test_full_name", user.full_name)
        self.assertEqual("test_email@test.com", user.email)
        self.assertEqual(
            "27cbb2858ce86012e498c8102d24d066837d67beec8c180f5e85e652df700c9f",
            user.oidc_groups_hash,
        )
        self.assertFalse(user.is_external)

        user_save_mock.assert_called_once()
        synchronize_groups_mock.assert_called_with(user, payload)

        settings.internal_users = ""
        settings.save()

    @patch("application.access_control.services.oidc_authentication.User.save")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._synchronize_groups")
    def test_create_user_external(self, synchronize_groups_mock, user_save_mock):
        settings = Settings.load()
        settings.internal_users = ".*@example.com, .*@test.com"
        settings.save()

        oidc_authentication = OIDCAuthentication()
        payload = {
            "preferred_username": "test_username",
            "given_name": "test_first_name",
            "family_name": "test_last_name",
            "name": "test_full_name",
            "email": "test_email@test.net",
            "groups": ["test_group_1", "test_group_2"],
        }

        user = oidc_authentication._create_user("test_username", payload)

        self.assertEqual("test_username", user.username)
        self.assertEqual("test_first_name", user.first_name)
        self.assertEqual("test_last_name", user.last_name)
        self.assertEqual("test_full_name", user.full_name)
        self.assertEqual("test_email@test.net", user.email)
        self.assertEqual(
            "27cbb2858ce86012e498c8102d24d066837d67beec8c180f5e85e652df700c9f",
            user.oidc_groups_hash,
        )
        self.assertTrue(user.is_external)

        user_save_mock.assert_called_once()
        synchronize_groups_mock.assert_called_with(user, payload)

        settings.internal_users = ""
        settings.save()

    @patch("application.access_control.services.oidc_authentication.User.save")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._synchronize_groups")
    def test_create_user_no_claim_mappings(self, synchronize_groups_mock, user_save_mock):
        oidc_authentication = OIDCAuthentication()
        payload = {
            "preferred_username": "test_username",
            "given_name": "test_first_name",
            "family_name": "test_last_name",
            "name": "test_full_name",
            "email": "test_email",
            "groups": ["test_group_1", "test_group_2"],
        }

        with patch.dict(
            "os.environ",
            {
                "OIDC_FIRST_NAME": "",
                "OIDC_LAST_NAME": "",
                "OIDC_FULL_NAME": "",
                "OIDC_EMAIL": "",
                "OIDC_GROUPS": "",
            },
        ):
            user = oidc_authentication._create_user("test_username", payload)

            self.assertEqual("test_username", user.username)
            self.assertEqual("", user.first_name)
            self.assertEqual("", user.last_name)
            self.assertEqual("", user.full_name)
            self.assertEqual("", user.email)
            self.assertEqual("", user.oidc_groups_hash)
            user_save_mock.assert_called_once()
            synchronize_groups_mock.assert_called_with(user, payload)

    @patch("application.access_control.services.oidc_authentication.User.save")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._synchronize_groups")
    def test_check_user_change_no_change(self, synchronize_groups_mock, user_save_mock):
        old_user = User(
            username="test_username",
            first_name="test_first_name",
            last_name="test_last_name",
            full_name="test_full_name",
            email="test_email",
            oidc_groups_hash="",
            is_oidc_user=True,
        )
        old_user.set_unusable_password()
        oidc_authentication = OIDCAuthentication()
        new_user = oidc_authentication._check_user_change(
            old_user,
            {
                "preferred_username": "test_username",
                "given_name": "test_first_name",
                "family_name": "test_last_name",
                "name": "test_full_name",
                "email": "test_email",
                "groups": [],
            },
        )

        self.assertEqual("test_username", new_user.username)
        self.assertEqual("test_first_name", new_user.first_name)
        self.assertEqual("test_last_name", new_user.last_name)
        self.assertEqual("test_full_name", new_user.full_name)
        self.assertEqual("test_email", new_user.email)
        user_save_mock.assert_not_called()
        synchronize_groups_mock.assert_not_called()

    @patch("application.access_control.services.oidc_authentication.User.save")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._synchronize_groups")
    def test_check_user_change_no_claim_mappings(self, synchronize_groups_mock, user_save_mock):
        old_user = User(
            username="test_username",
            first_name="test_first_name",
            last_name="test_last_name",
            full_name="test_full_name",
            email="test_email",
            oidc_groups_hash="",
            is_oidc_user=True,
        )
        old_user.set_unusable_password()
        oidc_authentication = OIDCAuthentication()

        with patch.dict(
            "os.environ",
            {
                "OIDC_FIRST_NAME": "",
                "OIDC_LAST_NAME": "",
                "OIDC_FULL_NAME": "",
                "OIDC_EMAIL": "",
                "OIDC_GROUPS": "",
            },
        ):
            new_user = oidc_authentication._check_user_change(
                old_user,
                {
                    "preferred_username": "username",
                    "given_name": "first_name",
                    "family_name": "last_name",
                    "name": "full_name",
                    "email": "email",
                    "groups": ["group_1", "group_2"],
                },
            )

            self.assertEqual("test_username", new_user.username)
            self.assertEqual("test_first_name", new_user.first_name)
            self.assertEqual("test_last_name", new_user.last_name)
            self.assertEqual("test_full_name", new_user.full_name)
            self.assertEqual("test_email", new_user.email)
            self.assertEqual("", new_user.oidc_groups_hash)
            user_save_mock.assert_not_called()
            synchronize_groups_mock.assert_not_called()

    @patch("application.access_control.services.oidc_authentication.User.save")
    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication._synchronize_groups")
    def test_check_user_change_with_changes(self, synchronize_groups_mock, user_save_mock):
        old_user = User(
            username="test_username",
            first_name="test_first_name",
            last_name="test_last_name",
            full_name="test_full_name",
            email="test_email",
            oidc_groups_hash="",
        )
        oidc_authentication = OIDCAuthentication()
        payload = {
            "preferred_username": "test_username",
            "given_name": "test_first_name_new",
            "family_name": "test_last_name_new",
            "name": "test_full_name_new",
            "email": "test_email_new",
            "groups": ["test_group_1", "test_group_2"],
        }
        new_user = oidc_authentication._check_user_change(old_user, payload)

        self.assertEqual("test_username", new_user.username)
        self.assertEqual("test_first_name_new", new_user.first_name)
        self.assertEqual("test_last_name_new", new_user.last_name)
        self.assertEqual("test_full_name_new", new_user.full_name)
        self.assertEqual("test_email_new", new_user.email)
        self.assertEqual(
            "27cbb2858ce86012e498c8102d24d066837d67beec8c180f5e85e652df700c9f",
            new_user.oidc_groups_hash,
        )
        self.assertFalse(new_user.has_usable_password())
        user_save_mock.assert_called_once()
        synchronize_groups_mock.assert_called_with(new_user, payload)

    def test_synchronize_groups(self):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        oidc_authentication = OIDCAuthentication()
        user = User.objects.get(username="db_internal_write")
        payload = {"groups": ["oidc_1"]}

        oidc_authentication._synchronize_groups(user, payload)

        groups = user.authorization_groups.all().order_by("name")
        self.assertEqual(2, len(groups))
        self.assertEqual("non_oidc_group", groups[0].name)
        self.assertEqual("oidc_group_1", groups[1].name)

        payload = {"groups": ["oidc_2"]}

        oidc_authentication._synchronize_groups(user, payload)

        groups = user.authorization_groups.all().order_by("name")
        self.assertEqual(2, len(groups))
        self.assertEqual("non_oidc_group", groups[0].name)
        self.assertEqual("oidc_group_2", groups[1].name)


class MockPyJWK:
    def __init__(self, key):
        self.key = key


class MockResponse:
    def __init__(self):
        self.raise_for_status_called = False

    def raise_for_status(self):
        self.raise_for_status_called = True

    def json(self):
        if not self.raise_for_status_called:
            raise Exception("raise_for_status not called")
        return {"jwks_uri": "https://authority/.well-known/jwks.json"}
