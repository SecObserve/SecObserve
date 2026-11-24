from rest_framework.test import APIClient

from application.access_control.models import User
from unittests.base_test_case import BaseTestCase

NOT_CHANGEABLE = "Cannot be changed after the user has been created"


class TestServiceAccount(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_user(username="admin_sa_test", password="x", is_superuser=True)
        self.client = APIClient()
        self.client.force_authenticate(user=self.superuser)

    def _create_service_account(self) -> User:
        response = self.client.post("/api/users/", {"username": "sa", "is_service_account": True}, "json")
        self.assertEqual(201, response.status_code)
        return User.objects.get(username="sa")

    def test_create_service_account_has_no_usable_password(self):
        user = self._create_service_account()

        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.is_service_account)

    def test_create_regular_user_unchanged(self):
        response = self.client.post("/api/users/", {"username": "regular"}, "json")

        self.assertEqual(201, response.status_code)
        self.assertFalse(User.objects.get(username="regular").is_service_account)

    def test_update_cannot_set_service_account(self):
        user = User.objects.create_user(username="regular", password="x")

        response = self.client.patch(f"/api/users/{user.pk}/", {"is_service_account": True}, "json")

        self.assertEqual(400, response.status_code)
        self.assertIn(NOT_CHANGEABLE, response.content.decode())

    def test_update_cannot_unset_service_account(self):
        user = self._create_service_account()

        response = self.client.patch(f"/api/users/{user.pk}/", {"is_service_account": False}, "json")

        self.assertEqual(400, response.status_code)
        self.assertIn(NOT_CHANGEABLE, response.content.decode())

    def test_update_same_value_allowed(self):
        user = self._create_service_account()

        response = self.client.patch(
            f"/api/users/{user.pk}/", {"is_service_account": True, "full_name": "x"}, "json"
        )

        self.assertEqual(200, response.status_code)

    def test_password_login_refused(self):
        self._create_service_account()

        response = APIClient().post(
            "/api/authentication/authenticate/", {"username": "sa", "password": "anything"}, "json"
        )

        self.assertEqual(403, response.status_code)

    def test_change_password_refused(self):
        user = self._create_service_account()

        response = self.client.patch(
            f"/api/users/{user.pk}/change_password/",
            {"new_password_1": "Abcdef-123456", "new_password_2": "Abcdef-123456"},
            "json",
        )

        self.assertEqual(400, response.status_code)
        self.assertIn("User's password cannot be changed", response.content.decode())
