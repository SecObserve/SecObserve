from threading import current_thread
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.test import APIClient

from application.access_control.models import User
from application.access_control.queries.user import get_user_by_username
from application.authorization.services.roles_permissions import Roles
from application.commons.services import global_request
from application.core.models import (
    Observation,
    Observation_Log,
    Product,
    Product_Member,
)
from application.core.types import Assessment_Status, Severity, Status
from application.import_observations.models import Parser
from application.notifications.models import (
    Notification,
    Notification_Recipient,
    Notification_Viewed,
)
from unittests.base_test_case import BaseTestCase


class TestViews(BaseTestCase):
    def tearDown(self) -> None:
        global_request._requests.pop(current_thread().name, None)  # pylint: disable=protected-access
        super().tearDown()

    def _create_targeted_notification(self) -> tuple[Notification, User, User]:
        with patch("application.core.signals.get_current_user", return_value=None):
            product = Product.objects.create(name="targeted-notification-product")
        recipient = User.objects.create(username="notification-recipient@example.com")
        unrelated_member = User.objects.create(username="unrelated-member@example.com")
        Product_Member.objects.create(product=product, user=recipient, role=Roles.Writer)
        Product_Member.objects.create(product=product, user=unrelated_member, role=Roles.Writer)
        parser = Parser.objects.create(name="targeted-notification-parser")
        observation = Observation.objects.create(
            product=product,
            parser=parser,
            title="Targeted observation",
            current_severity=Severity.SEVERITY_HIGH,
            current_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )
        observation_log = Observation_Log.objects.create(
            observation=observation,
            user=unrelated_member,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL,
        )
        notification = Notification.objects.create(
            name="Assessment needs approval",
            message="Targeted approval message",
            product=product,
            observation=observation,
            observation_log=observation_log,
            user=unrelated_member,
            type=Notification.TYPE_ASSESSMENT_REQUEST,
        )
        Notification_Recipient.objects.create(notification=notification, user=recipient)
        return notification, recipient, unrelated_member

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_targeted_notification_recipient_can_list_retrieve_and_view_message(self, mock_authentication):
        notification, recipient, _unrelated_member = self._create_targeted_notification()
        mock_authentication.return_value = recipient, None
        api_client = APIClient()

        list_response = api_client.get("/api/notifications/")
        detail_response = api_client.get(f"/api/notifications/{notification.pk}/")

        self.assertEqual(HTTP_200_OK, list_response.status_code)
        self.assertEqual([notification.pk], [item["id"] for item in list_response.data["results"]])
        self.assertEqual(HTTP_200_OK, detail_response.status_code)
        self.assertEqual("Targeted approval message", detail_response.data["message"])
        self.assertEqual(notification.observation_log_id, detail_response.data["observation_log"])

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_targeted_notification_unrelated_member_is_denied(self, mock_authentication):
        notification, _recipient, unrelated_member = self._create_targeted_notification()
        mock_authentication.return_value = unrelated_member, None
        api_client = APIClient()

        list_response = api_client.get("/api/notifications/")
        detail_response = api_client.get(f"/api/notifications/{notification.pk}/")
        viewed_response = api_client.post(f"/api/notifications/{notification.pk}/mark_as_viewed/")

        self.assertEqual(HTTP_200_OK, list_response.status_code)
        self.assertEqual([], list_response.data["results"])
        self.assertEqual(HTTP_404_NOT_FOUND, detail_response.status_code)
        self.assertEqual(HTTP_404_NOT_FOUND, viewed_response.status_code)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_targeted_notification_superuser_can_retrieve(self, mock_authentication):
        notification, _recipient, _unrelated_member = self._create_targeted_notification()
        superuser = User.objects.create(username="notification-admin@example.com", is_superuser=True)
        mock_authentication.return_value = superuser, None

        response = APIClient().get(f"/api/notifications/{notification.pk}/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual("Targeted approval message", response.data["message"])

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_targeted_notification_writer_cannot_delete_shared_event(self, mock_authentication):
        notification, recipient, _unrelated_member = self._create_targeted_notification()
        mock_authentication.return_value = recipient, None

        response = APIClient().delete(f"/api/notifications/{notification.pk}/")

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        self.assertTrue(Notification.objects.filter(pk=notification.pk).exists())

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
