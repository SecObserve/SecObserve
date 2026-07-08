from unittest.mock import patch

from django.core.management import call_command
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from rest_framework.test import APIClient

from application.access_control.models import User
from application.access_control.queries.user import get_user_by_username
from application.authorization.services.roles_permissions import Roles
from application.commons.services import global_request
from application.core.models import Product, Product_Member
from application.notifications.models import Notification, Notification_Viewed
from unittests.base_test_case import BaseTestCase


class TestViews(BaseTestCase):
    def tearDown(self) -> None:
        global_request._requests.clear()  # pylint: disable=protected-access
        super().tearDown()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_bulk_mark_as_viewed_no_list(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/bulk_mark_as_viewed/")

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({"message": "Notifications: This field is required."}, response.data)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_bulk_mark_as_viewed_successful(self, mock_authentication):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        # mock_authentication.return_value = self.user_internal, None
        user = get_user_by_username("db_internal_write")
        mock_authentication.return_value = user, None

        data = {"notifications": [3, 5]}
        api_client = APIClient()
        response = api_client.post("/api/notifications/bulk_mark_as_viewed/", data=data, format="json")

        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)

        notification_viewed = Notification_Viewed.objects.get(notification_id=3, user=user)
        self.assertIsNotNone(notification_viewed)

        notification_viewed = Notification_Viewed.objects.get(notification_id=5, user=user)
        self.assertIsNotNone(notification_viewed)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_mark_as_viewed_not_found(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/99999/mark_as_viewed/")

        self.assertEqual(HTTP_404_NOT_FOUND, response.status_code)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_mark_as_viewed_not_found_for_user(self, mock_authentication):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        user = User.objects.get(username="db_internal_write")
        mock_authentication.return_value = user, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/2/mark_as_viewed/")

        self.assertEqual(HTTP_404_NOT_FOUND, response.status_code)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_mark_as_viewed_successful(self, mock_authentication):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        user = User.objects.get(username="db_internal_write")
        mock_authentication.return_value = user, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/3/mark_as_viewed/")

        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)

        notification_viewed = Notification_Viewed.objects.get(notification_id=3, user=user)
        self.assertIsNotNone(notification_viewed)

    def test_delete_request_notifications_are_visible_to_owner_only(self):
        owner = User.objects.create(username="notification_owner@example.com")
        maintainer = User.objects.create(username="notification_maintainer@example.com")
        product = Product.objects.create(name="delete_request_notification")
        Product_Member.objects.create(product=product, user=owner, role=Roles.Owner)
        Product_Member.objects.create(product=product, user=maintainer, role=Roles.Maintainer)
        notification = Notification.objects.create(
            name='Deletion requested for "delete_request_notification"',
            message="notification_maintainer@example.com requested deletion.",
            product=product,
            user=maintainer,
            type=Notification.TYPE_PRODUCT_DELETE_REQUEST,
        )

        api_client = APIClient()
        api_client.force_authenticate(user=owner)
        owner_response = api_client.get("/api/notifications/")
        self.assertEqual(HTTP_200_OK, owner_response.status_code, owner_response.data)
        self.assertIn(notification.pk, [item["id"] for item in owner_response.data["results"]])

        api_client.force_authenticate(user=maintainer)
        maintainer_response = api_client.get("/api/notifications/")
        self.assertEqual(HTTP_200_OK, maintainer_response.status_code, maintainer_response.data)
        self.assertNotIn(notification.pk, [item["id"] for item in maintainer_response.data["results"]])
