from unittest.mock import MagicMock, call, patch

from application.access_control.models import User
from application.commons.models import Settings
from application.notifications.models import Notification
from application.notifications.services.send_notifications_security_gate import (
    send_product_security_gate_notification,
)
from application.notifications.types import Product_Notification_Type
from unittests.base_test_case import BaseTestCase


class TestPushNotificationsSecurityGate(BaseTestCase):
    # --- send_product_security_gate_notification ---

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_security_gate.get_users_for_product_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_slack_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_email_notification")
    @patch("application.notifications.services.send_notifications_security_gate.get_current_user")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_email_to")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_ms_teams_webhook")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_product_security_gate_notification_no_webhook_no_email(
        self,
        mock_notification_create,
        mock_get_notification_ms_teams_webhook,
        mock_get_notification_slack_webhook,
        mock_get_notification_email_to,
        mock_current_user,
        mock_send_email,
        mock_send_teams,
        mock_send_slack,
        mock_get_users,
        mock_settings_load,
    ):
        mock_settings_load.return_value = Settings()
        mock_current_user.return_value = self.user_internal
        mock_get_notification_email_to.return_value = ""
        mock_get_notification_ms_teams_webhook.return_value = ""
        mock_get_notification_slack_webhook.return_value = ""
        mock_get_users.return_value = set()

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mock_get_notification_email_to.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        mock_get_notification_slack_webhook.assert_called_with(self.product_1)
        mock_send_teams.assert_not_called()
        mock_send_slack.assert_not_called()
        mock_send_email.assert_not_called()
        mock_notification_create.assert_called_with(
            name="Security gate has changed to None",
            product=self.product_1,
            user=self.user_internal,
            type=Notification.TYPE_SECURITY_GATE,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_security_gate.get_users_for_product_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_slack_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_email_notification")
    @patch("application.notifications.services.send_notifications_security_gate.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications_security_gate._get_first_name")
    @patch("application.notifications.services.send_notifications_security_gate.get_current_user")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_email_to")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_ms_teams_webhook")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_product_security_gate_notification_security_gate_none(
        self,
        mock_notification_create,
        mock_get_notification_ms_teams_webhook,
        mock_get_notification_slack_webhook,
        mock_get_notification_email_to,
        mock_current_user,
        mock_get_first_name,
        mock_base_url,
        mock_send_email,
        mock_send_teams,
        mock_send_slack,
        mock_get_users,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        mock_settings_load.return_value = settings
        mock_base_url.return_value = "https://secobserve.com/"
        mock_get_first_name.return_value = "first_name"
        mock_current_user.return_value = self.user_internal
        mock_get_notification_email_to.return_value = "test1@example.com, test2@example.com"
        mock_get_notification_ms_teams_webhook.return_value = "https://msteams.microsoft.com"
        mock_get_notification_slack_webhook.return_value = "https://secobserve.slack.com"
        mock_get_users.return_value = set()
        self.product_1.security_gate_passed = None
        self.product_1.pk = 1

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mock_get_notification_email_to.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        mock_get_notification_slack_webhook.assert_called_with(self.product_1)
        expected_calls_email = [
            call(
                "test1@example.com",
                "Security gate for product product_1 has changed to None",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="None",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                "Security gate for product product_1 has changed to None",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="None",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
        ]
        mock_send_email.assert_has_calls(expected_calls_email)
        mock_send_teams.assert_called_with(
            "https://msteams.microsoft.com",
            "msteams_v2_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="None",
            product_url="https://secobserve.com/#/products/1/show",
        )
        mock_send_slack.assert_called_with(
            "https://secobserve.slack.com",
            "slack_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="None",
            product_url="https://secobserve.com/#/products/1/show",
        )
        expected_calls_get_first_name = [
            call("test1@example.com"),
            call("test2@example.com"),
        ]
        mock_get_first_name.assert_has_calls(expected_calls_get_first_name)
        mock_notification_create.assert_called_with(
            name="Security gate has changed to None",
            product=self.product_1,
            user=self.user_internal,
            type=Notification.TYPE_SECURITY_GATE,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_security_gate.get_users_for_product_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_slack_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_email_notification")
    @patch("application.notifications.services.send_notifications_security_gate.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications_security_gate._get_first_name")
    @patch("application.notifications.services.send_notifications_security_gate.get_current_user")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_email_to")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_ms_teams_webhook")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_product_security_gate_notification_security_gate_passed(
        self,
        mock_notification_create,
        mock_get_notification_ms_teams_webhook,
        mock_get_notification_slack_webhook,
        mock_get_notification_email_to,
        mock_current_user,
        mock_get_first_name,
        mock_base_url,
        mock_send_email,
        mock_send_teams,
        mock_send_slack,
        mock_get_users,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        mock_settings_load.return_value = settings
        mock_base_url.return_value = "https://secobserve.com/"
        mock_get_first_name.return_value = "first_name"
        mock_current_user.return_value = self.user_internal
        mock_get_notification_email_to.return_value = "test1@example.com, test2@example.com"
        mock_get_notification_ms_teams_webhook.return_value = "https://msteams.microsoft.com"
        mock_get_notification_slack_webhook.return_value = "https://secobserve.slack.com"
        mock_get_users.return_value = set()
        self.product_1.security_gate_passed = True
        self.product_1.pk = 1

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mock_get_notification_email_to.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        mock_get_notification_slack_webhook.assert_called_with(self.product_1)
        expected_calls_email = [
            call(
                "test1@example.com",
                "Security gate for product product_1 has changed to Passed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Passed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                "Security gate for product product_1 has changed to Passed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Passed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
        ]
        mock_send_email.assert_has_calls(expected_calls_email)
        mock_send_teams.assert_called_with(
            "https://msteams.microsoft.com",
            "msteams_v2_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="Passed",
            product_url="https://secobserve.com/#/products/1/show",
        )
        mock_send_slack.assert_called_with(
            "https://secobserve.slack.com",
            "slack_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="Passed",
            product_url="https://secobserve.com/#/products/1/show",
        )
        expected_calls_get_first_name = [
            call("test1@example.com"),
            call("test2@example.com"),
        ]
        mock_get_first_name.assert_has_calls(expected_calls_get_first_name)
        mock_notification_create.assert_called_with(
            name="Security gate has changed to Passed",
            product=self.product_1,
            user=self.user_internal,
            type=Notification.TYPE_SECURITY_GATE,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_security_gate.get_users_for_product_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_slack_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_security_gate.send_email_notification")
    @patch("application.notifications.services.send_notifications_security_gate.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications_security_gate._get_first_name")
    @patch("application.notifications.services.send_notifications_security_gate.get_current_user")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_email_to")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_ms_teams_webhook")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_product_security_gate_notification_security_gate_failed(
        self,
        mock_notification_create,
        mock_get_notification_ms_teams_webhook,
        mock_get_notification_slack_webhook,
        mock_get_notification_email_to,
        mock_current_user,
        mock_get_first_name,
        mock_base_url,
        mock_send_email,
        mock_send_teams,
        mock_send_slack,
        mock_get_users,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        mock_settings_load.return_value = settings
        mock_base_url.return_value = "https://secobserve.com/"
        mock_get_first_name.return_value = "first_name"
        mock_current_user.return_value = self.user_internal
        mock_get_notification_email_to.return_value = "test1@example.com, test2@example.com"
        mock_get_notification_ms_teams_webhook.return_value = "https://msteams.microsoft.com"
        mock_get_notification_slack_webhook.return_value = "https://secobserve.slack.com"
        mock_get_users.return_value = set()
        self.product_1.security_gate_passed = False
        self.product_1.pk = 1

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mock_get_notification_email_to.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        mock_get_notification_slack_webhook.assert_called_with(self.product_1)
        expected_calls_email = [
            call(
                "test1@example.com",
                "Security gate for product product_1 has changed to Failed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Failed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                "Security gate for product product_1 has changed to Failed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Failed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
        ]
        mock_send_email.assert_has_calls(expected_calls_email)
        mock_send_teams.assert_called_with(
            "https://msteams.microsoft.com",
            "msteams_v2_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="Failed",
            product_url="https://secobserve.com/#/products/1/show",
        )
        mock_send_slack.assert_called_with(
            "https://secobserve.slack.com",
            "slack_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="Failed",
            product_url="https://secobserve.com/#/products/1/show",
        )
        expected_calls_get_first_name = [
            call("test1@example.com"),
            call("test2@example.com"),
        ]
        mock_get_first_name.assert_has_calls(expected_calls_get_first_name)
        mock_notification_create.assert_called_with(
            name="Security gate has changed to Failed",
            product=self.product_1,
            user=self.user_internal,
            type=Notification.TYPE_SECURITY_GATE,
        )

    # --- send_product_security_gate_notification, the task itself ---

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_security_gate.get_users_for_product_notification")
    @patch("application.notifications.services.send_notifications_security_gate.get_current_user")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_email_to")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications_security_gate._get_notification_ms_teams_webhook")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_product_security_gate_notification_is_deferred_until_commit(
        self,
        mock_notification_create,
        mock_get_notification_ms_teams_webhook,
        mock_get_notification_slack_webhook,
        mock_get_notification_email_to,
        mock_current_user,
        mock_get_users,
        mock_settings_load,
    ):
        mock_settings_load.return_value = Settings()
        mock_current_user.return_value = self.user_internal
        mock_get_notification_email_to.return_value = ""
        mock_get_notification_ms_teams_webhook.return_value = ""
        mock_get_notification_slack_webhook.return_value = ""
        mock_get_users.return_value = set()

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

            # the task runs after the commit, not while the transaction is still open
            mock_notification_create.assert_not_called()

        mock_notification_create.assert_called_once_with(
            name="Security gate has changed to None",
            product=self.product_1,
            user=self.user_internal,
            type=Notification.TYPE_SECURITY_GATE,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_security_gate.handle_task_exception")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_product_security_gate_notification_exception(
        self,
        mock_notification_create,
        mock_handle_task_exception,
        mock_settings_load,
    ):
        exception = Exception("test_exception")
        mock_settings_load.side_effect = exception

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mock_handle_task_exception.assert_called_once_with(exception)
        mock_notification_create.assert_not_called()

    # --- send_product_security_gate_notification, notifications for the users of the product ---

    def _patch_for_users(self, email_from: str = "secobserve@example.com") -> dict[str, MagicMock]:
        """The mocks all tests for the user specific notifications need, the webhooks and the
        notification email addresses of the product are switched off."""
        patchers = {
            "get_users": patch(
                "application.notifications.services.send_notifications_security_gate."
                "get_users_for_product_notification"
            ),
            "send_email": patch(
                "application.notifications.services.send_notifications_security_gate.send_email_notification"
            ),
            "base_url": patch(
                "application.notifications.services.send_notifications_security_gate.get_base_url_frontend"
            ),
            "current_user": patch(
                "application.notifications.services.send_notifications_security_gate.get_current_user"
            ),
            "email_to": patch(
                "application.notifications.services.send_notifications_security_gate._get_notification_email_to"
            ),
            "slack": patch(
                "application.notifications.services.send_notifications_security_gate._get_notification_slack_webhook"
            ),
            "ms_teams": patch(
                "application.notifications.services.send_notifications_security_gate._get_notification_ms_teams_webhook"
            ),
            "notification_create": patch("application.notifications.models.Notification.objects.create"),
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
        mocks["current_user"].return_value = self.user_internal
        mocks["email_to"].return_value = ""
        mocks["slack"].return_value = ""
        mocks["ms_teams"].return_value = ""

        self.product_1.security_gate_passed = True
        self.product_1.pk = 1

        return mocks

    def test_send_product_security_gate_notification_user_with_first_name(self):
        mocks = self._patch_for_users()
        user = User(
            id=10, username="jane@example.com", email="jane@example.com", first_name="Jane", full_name="Jane Doe"
        )
        mocks["get_users"].return_value = {user}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mocks["get_users"].assert_called_once_with(self.product_1, Product_Notification_Type.SECURITY_GATE_CHANGED)
        mocks["send_email"].assert_called_once_with(
            "jane@example.com",
            "Security gate for product product_1 has changed to Passed",
            "email_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="Passed",
            product_url="https://secobserve.com/#/products/1/show",
            first_name=" Jane",
        )

    def test_send_product_security_gate_notification_user_without_first_name(self):
        mocks = self._patch_for_users()
        user = User(id=10, username="jane@example.com", email="jane@example.com", first_name="", full_name="Jane Doe")
        mocks["get_users"].return_value = {user}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mocks["send_email"].assert_called_once_with(
            "jane@example.com",
            "Security gate for product product_1 has changed to Passed",
            "email_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="Passed",
            product_url="https://secobserve.com/#/products/1/show",
            first_name=" Jane Doe",
        )

    def test_send_product_security_gate_notification_several_users(self):
        mocks = self._patch_for_users()
        user_1 = User(
            id=10, username="jane@example.com", email="jane@example.com", first_name="Jane", full_name="Jane Doe"
        )
        user_2 = User(
            id=11, username="john@example.com", email="john@example.com", first_name="John", full_name="John Doe"
        )
        mocks["get_users"].return_value = {user_1, user_2}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        expected_calls = [
            call(
                "jane@example.com",
                "Security gate for product product_1 has changed to Passed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Passed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name=" Jane",
            ),
            call(
                "john@example.com",
                "Security gate for product product_1 has changed to Passed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Passed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name=" John",
            ),
        ]
        # get_users_for_product_notification() returns a set, the order is not defined
        mocks["send_email"].assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(2, mocks["send_email"].call_count)

    def test_send_product_security_gate_notification_no_users(self):
        mocks = self._patch_for_users()
        mocks["get_users"].return_value = set()

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mocks["send_email"].assert_not_called()
        mocks["notification_create"].assert_called_with(
            name="Security gate has changed to Passed",
            product=self.product_1,
            user=self.user_internal,
            type=Notification.TYPE_SECURITY_GATE,
        )

    def test_send_product_security_gate_notification_users_without_email_from(self):
        mocks = self._patch_for_users(email_from="")
        user = User(
            id=10, username="jane@example.com", email="jane@example.com", first_name="Jane", full_name="Jane Doe"
        )
        mocks["get_users"].return_value = {user}

        with self.captureOnCommitCallbacks(execute=True):
            send_product_security_gate_notification(self.product_1)

        mocks["get_users"].assert_not_called()
        mocks["send_email"].assert_not_called()
