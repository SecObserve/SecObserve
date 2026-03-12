from unittest.mock import MagicMock, call, patch

from application.commons.models import Settings
from application.notifications.models import Notification, Observation_Notified
from application.notifications.services.send_notifications_observation import (
    _send_observation_notifications,
    send_observation_notification,
)
from unittests.base_test_case import BaseTestCase


class TestPushNotificationsObservation(BaseTestCase):
    # --- send_observation_notification ---

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_no_filters_no_existing_notified(
        self,
        mock_observation_notified_get,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = None
        mock_get_statuses.return_value = None
        mock_get_min_priority.return_value = None
        mock_observation_notified_get.side_effect = Observation_Notified.DoesNotExist

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_not_called()
        mock_observation_notified_get.assert_called_once_with(observation=self.observation_1)

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_no_filters_existing_notified(
        self,
        mock_observation_notified_get,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = None
        mock_get_statuses.return_value = None
        mock_get_min_priority.return_value = None
        mock_notified = MagicMock()
        mock_observation_notified_get.return_value = mock_notified

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_called_once_with(
            self.observation_1,
            f'Observation "{self.observation_1.title}" fell out of notifications',
        )
        mock_notified.delete.assert_called_once()

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.models.Observation_Notified.save")
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_new_notification(
        self,
        mock_observation_notified_get,
        mock_observation_notified_save,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = None
        mock_get_statuses.return_value = "Open"
        mock_get_min_priority.return_value = None
        mock_observation_notified_get.side_effect = Observation_Notified.DoesNotExist
        self.observation_1.current_status = "Open"
        self.observation_1.current_severity = "Critical"
        self.observation_1.current_priority = None

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_called_once_with(
            self.observation_1,
            f'New notification for observation "{self.observation_1.title}"',
        )
        mock_observation_notified_save.assert_called_once()

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_existing_no_change(
        self,
        mock_observation_notified_get,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = None
        mock_get_statuses.return_value = "Open"
        mock_get_min_priority.return_value = None
        self.observation_1.current_status = "Open"
        self.observation_1.current_severity = "Critical"
        self.observation_1.current_priority = None
        mock_notified = MagicMock()
        mock_notified.severity = self.observation_1.current_severity
        mock_notified.status = self.observation_1.current_status
        mock_notified.priority = self.observation_1.current_priority
        mock_observation_notified_get.return_value = mock_notified

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_not_called()

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_existing_changed(
        self,
        mock_observation_notified_get,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = None
        mock_get_statuses.return_value = "Open"
        mock_get_min_priority.return_value = None
        self.observation_1.current_status = "Open"
        self.observation_1.current_severity = "Critical"
        self.observation_1.current_priority = None
        mock_notified = MagicMock()
        mock_notified.severity = "High"  # different from current_severity
        mock_notified.status = "Open"
        mock_notified.priority = None
        mock_observation_notified_get.return_value = mock_notified

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_called_once_with(
            self.observation_1,
            f'Change in observation "{self.observation_1.title}"',
        )
        mock_notified.save.assert_called_once()

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.services.send_notifications_observation.Severity")
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_severity_not_met_no_existing_notified(
        self,
        mock_observation_notified_get,
        mock_severity,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = "Medium"
        mock_severity.NUMERICAL_SEVERITIES.get.return_value = 3
        mock_get_statuses.return_value = None
        mock_get_min_priority.return_value = None
        self.observation_1.numerical_severity = 4  # worse than "Medium" (3), does not meet threshold
        mock_observation_notified_get.side_effect = Observation_Notified.DoesNotExist

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_not_called()
        mock_severity.NUMERICAL_SEVERITIES.get.assert_called_once_with("Medium")

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_status_not_met_existing_notified(
        self,
        mock_observation_notified_get,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = None
        mock_get_statuses.return_value = "Open"
        mock_get_min_priority.return_value = None
        self.observation_1.current_status = "Resolved"  # does not match "Open"
        mock_notified = MagicMock()
        mock_observation_notified_get.return_value = mock_notified

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_called_once_with(
            self.observation_1,
            f'Observation "{self.observation_1.title}" fell out of notifications',
        )
        mock_notified.delete.assert_called_once()

    @patch("application.notifications.services.send_notifications_observation._send_observation_notifications")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_priority"
    )
    @patch("application.notifications.services.send_notifications_observation._get_observation_notification_statuses")
    @patch(
        "application.notifications.services.send_notifications_observation._get_observation_notification_min_severity"
    )
    @patch("application.notifications.services.send_notifications_observation.Severity")
    @patch("application.notifications.models.Observation_Notified.save")
    @patch("application.notifications.models.Observation_Notified.objects.get")
    def test_send_observation_notification_severity_met_new_notification(
        self,
        mock_observation_notified_get,
        mock_observation_notified_save,
        mock_severity,
        mock_get_min_severity,
        mock_get_statuses,
        mock_get_min_priority,
        mock_send_notifications,
    ):
        mock_get_min_severity.return_value = "Medium"
        mock_severity.NUMERICAL_SEVERITIES.get.return_value = 3
        mock_get_statuses.return_value = None
        mock_get_min_priority.return_value = None
        self.observation_1.numerical_severity = 1  # Critical, better than "Medium" (3), meets threshold
        self.observation_1.current_severity = "Critical"
        self.observation_1.current_status = "Open"
        self.observation_1.current_priority = None
        mock_observation_notified_get.side_effect = Observation_Notified.DoesNotExist

        send_observation_notification(self.observation_1)

        mock_send_notifications.assert_called_once_with(
            self.observation_1,
            f'New notification for observation "{self.observation_1.title}"',
        )
        mock_observation_notified_save.assert_called_once()

    # --- _send_observation_notifications ---

    @patch("application.notifications.services.send_notifications_observation.send_slack_notification")
    @patch("application.notifications.services.send_notifications_observation.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_observation.send_email_notification")
    @patch("application.notifications.services.send_notifications_observation.get_current_user")
    @patch("application.notifications.services.send_notifications_observation._get_notification_email_to")
    @patch("application.notifications.services.send_notifications_observation._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications_observation._get_notification_ms_teams_webhook")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_observation_notifications_no_webhook_no_email(
        self,
        mock_notification_create,
        mock_get_notification_ms_teams_webhook,
        mock_get_notification_slack_webhook,
        mock_get_notification_email_to,
        mock_current_user,
        mock_send_email,
        mock_send_teams,
        mock_send_slack,
    ):
        mock_current_user.return_value = self.user_internal
        mock_get_notification_email_to.return_value = ""
        mock_get_notification_ms_teams_webhook.return_value = ""
        mock_get_notification_slack_webhook.return_value = ""
        first_line = f'New notification for observation "{self.observation_1.title}"'

        _send_observation_notifications(self.observation_1, first_line)

        mock_get_notification_email_to.assert_called_with(self.observation_1.product)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.observation_1.product)
        mock_get_notification_slack_webhook.assert_called_with(self.observation_1.product)
        mock_send_email.assert_not_called()
        mock_send_teams.assert_not_called()
        mock_send_slack.assert_not_called()
        mock_notification_create.assert_called_with(
            name="New notification for observation",
            product=self.observation_1.product,
            observation=self.observation_1,
            user=self.user_internal,
            type=Notification.TYPE_OBSERVATION,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_observation.send_slack_notification")
    @patch("application.notifications.services.send_notifications_observation.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_observation.send_email_notification")
    @patch("application.notifications.services.send_notifications_observation.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications_observation._get_first_name")
    @patch("application.notifications.services.send_notifications_observation.get_current_user")
    @patch("application.notifications.services.send_notifications_observation._get_notification_email_to")
    @patch("application.notifications.services.send_notifications_observation._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications_observation._get_notification_ms_teams_webhook")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_observation_notifications_success(
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
        self.observation_1.pk = 1
        first_line = f'New notification for observation "{self.observation_1.title}"'

        _send_observation_notifications(self.observation_1, first_line)

        mock_get_notification_email_to.assert_called_with(self.observation_1.product)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.observation_1.product)
        mock_get_notification_slack_webhook.assert_called_with(self.observation_1.product)
        expected_calls_email = [
            call(
                "test1@example.com",
                first_line,
                "email_observation.tpl",
                observation=self.observation_1,
                observation_url="https://secobserve.com/#/observations/1/show",
                first_line=first_line,
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                first_line,
                "email_observation.tpl",
                observation=self.observation_1,
                observation_url="https://secobserve.com/#/observations/1/show",
                first_line=first_line,
                first_name="first_name",
            ),
        ]
        mock_send_email.assert_has_calls(expected_calls_email)
        mock_send_teams.assert_called_with(
            "https://msteams.microsoft.com",
            "msteams_observation.tpl",
            observation=self.observation_1,
            observation_url="https://secobserve.com/#/observations/1/show",
            first_line=first_line,
        )
        mock_send_slack.assert_called_with(
            "https://secobserve.slack.com",
            "slack_observation.tpl",
            observation=self.observation_1,
            observation_url="https://secobserve.com/#/observations/1/show",
            first_line=first_line,
        )
        expected_calls_get_first_name = [
            call("test1@example.com"),
            call("test2@example.com"),
        ]
        mock_get_first_name.assert_has_calls(expected_calls_get_first_name)
        mock_notification_create.assert_called_with(
            name="New notification for observation",
            product=self.observation_1.product,
            observation=self.observation_1,
            user=self.user_internal,
            type=Notification.TYPE_OBSERVATION,
        )
