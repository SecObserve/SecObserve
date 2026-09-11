from unittest.mock import MagicMock, patch

from application.access_control.models import User
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.notifications.services.send_notifications_observation_review import (
    send_observation_review_notification,
)
from application.notifications.types import Product_Notification_Type
from unittests.base_test_case import BaseTestCase


class TestSendNotificationsObservationReview(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.product_1.pk = 1
        self.observation_1.pk = 2
        self.user_jane = User(
            id=10, username="jane@example.com", email="jane@example.com", first_name="Jane", full_name="Jane Doe"
        )
        self.user_john = User(id=11, username="john@example.com", email="john@example.com", full_name="John Doe")

    def _patch(self, email_from: str = "secobserve@example.com") -> dict[str, MagicMock]:
        """The mocks all tests need: the users who want the notification and their permission to
        assess observations are mocked, so that no database is needed."""
        patchers = {
            "get_users": patch(
                "application.notifications.services.send_notifications_observation_review."
                "get_users_for_product_notification"
            ),
            "send_email": patch(
                "application.notifications.services.send_notifications_observation_review.send_email_notification"
            ),
            "base_url": patch(
                "application.notifications.services.send_notifications_observation_review.get_base_url_frontend"
            ),
            "has_permission": patch(
                "application.notifications.services.send_notifications_observation_review.user_has_permission"
            ),
            "settings_load": patch("application.commons.models.Settings.load"),
        }

        mocks = {}
        for name, patcher in patchers.items():
            mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)

        settings = Settings()
        settings.email_from = email_from
        mocks["settings_load"].return_value = settings
        mocks["base_url"].return_value = "https://secobserve.com/"
        mocks["get_users"].return_value = set()
        mocks["has_permission"].return_value = True

        return mocks

    def test_send_observation_review_notification_without_email_from(self):
        mocks = self._patch(email_from="")
        mocks["get_users"].return_value = {self.user_jane}

        with self.captureOnCommitCallbacks(execute=True):
            send_observation_review_notification(self.observation_1)

        mocks["get_users"].assert_not_called()
        mocks["send_email"].assert_not_called()

    def test_send_observation_review_notification_without_users(self):
        mocks = self._patch()

        with self.captureOnCommitCallbacks(execute=True):
            send_observation_review_notification(self.observation_1)

        mocks["get_users"].assert_called_once_with(self.product_1, Product_Notification_Type.OBSERVATION_TO_BE_REVIEWED)
        mocks["send_email"].assert_not_called()

    def test_send_observation_review_notification_user_with_first_name(self):
        mocks = self._patch()
        mocks["get_users"].return_value = {self.user_jane}

        with self.captureOnCommitCallbacks(execute=True):
            send_observation_review_notification(self.observation_1)

        mocks["has_permission"].assert_called_once_with(
            self.product_1, Permissions.Observation_Assessment, self.user_jane
        )
        mocks["send_email"].assert_called_once_with(
            "jane@example.com",
            'Observation "observation_1" has been set to "In review"',
            "email_observation.tpl",
            observation=self.observation_1,
            observation_url="https://secobserve.com/#/observations/2/show",
            first_line='Observation "observation_1" has been set to "In review"',
            first_name=" Jane",
        )

    def test_send_observation_review_notification_user_without_first_name(self):
        mocks = self._patch()
        mocks["get_users"].return_value = {self.user_john}

        with self.captureOnCommitCallbacks(execute=True):
            send_observation_review_notification(self.observation_1)

        self.assertEqual(" John Doe", mocks["send_email"].call_args.kwargs["first_name"])

    def test_send_observation_review_notification_without_assessment_permission(self):
        mocks = self._patch()
        mocks["get_users"].return_value = {self.user_jane}
        mocks["has_permission"].return_value = False

        with self.captureOnCommitCallbacks(execute=True):
            send_observation_review_notification(self.observation_1)

        mocks["send_email"].assert_not_called()

    def test_send_observation_review_notification_several_users(self):
        mocks = self._patch()
        mocks["get_users"].return_value = {self.user_jane, self.user_john}

        with self.captureOnCommitCallbacks(execute=True):
            send_observation_review_notification(self.observation_1)

        # get_users_for_product_notification() returns a set, the order is not defined
        self.assertEqual(2, mocks["send_email"].call_count)
        self.assertEqual(
            {"jane@example.com", "john@example.com"},
            {call.args[0] for call in mocks["send_email"].call_args_list},
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_observation_review.handle_task_exception")
    def test_send_observation_review_notification_exception(self, mock_handle_task_exception, mock_settings_load):
        exception = Exception("test_exception")
        mock_settings_load.side_effect = exception

        # call_local calls the undecorated function, so that the exception is not swallowed
        # by Huey. It has to be re-raised, so that Huey marks the task as failed.
        with self.assertRaises(Exception) as context:
            send_observation_review_notification.call_local(self.observation_1)
        self.assertEqual(exception, context.exception)

        mock_handle_task_exception.assert_called_once_with(exception)
