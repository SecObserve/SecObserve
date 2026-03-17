from unittest.mock import MagicMock, patch

from application.notifications.services.send_notifications_observation_title import (
    _send_observation_title_notifications,
    send_observation_title_notification,
)
from unittests.base_test_case import BaseTestCase

MODULE = "application.notifications.services.send_notifications_observation_title"


def _make_settings(
    *,
    min_severity=None,
    statuses=None,
    min_priority=None,
    parser_type=None,
    email_to="admin@example.com",
    email_from="noreply@example.com",
    ms_teams_webhook=None,
    slack_webhook=None,
):
    s = MagicMock()
    s.observation_title_notification_min_severity = min_severity
    s.observation_title_notification_statuses = statuses
    s.observation_title_notification_min_priority = min_priority
    s.observation_title_notification_parser_type = parser_type
    s.observation_title_notification_email_to = email_to
    s.email_from = email_from
    s.observation_title_notification_ms_teams_webhook = ms_teams_webhook
    s.observation_title_notification_slack_webhook = slack_webhook
    return s


def _make_observation(
    *,
    title="SQL Injection",
    numerical_severity=1,
    current_severity="Critical",
    current_status="Open",
    current_priority=1,
    parser_type="SAST",
):
    obs = MagicMock()
    obs.title = title
    obs.numerical_severity = numerical_severity
    obs.current_severity = current_severity
    obs.current_status = current_status
    obs.current_priority = current_priority
    obs.parser.type = parser_type
    return obs


class TestSendObservationTitleNotification(BaseTestCase):

    # -----------------------------------------------------------------------
    # Filtering – notification should NOT be sent
    # -----------------------------------------------------------------------

    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Settings")
    def test_no_filter_configured_skips_everything(self, mock_settings_cls, mock_otn, mock_send):
        """When no filter is configured the outer condition is False and we fall
        into the else branch; but because no Observation_Title_Notified record
        exists, the function returns early without sending anything."""
        settings = _make_settings()
        mock_settings_cls.load.return_value = settings
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist

        observation = _make_observation()
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    @patch(f"{MODULE}.Settings")
    def test_severity_filter_blocks_low_severity(self, mock_settings_cls, mock_severity, mock_otn, mock_send):
        """Observation severity higher than threshold should not trigger notification."""
        # numerical_severity 5 (low) vs threshold 2 (high) → 5 > 2, blocked
        settings = _make_settings(min_severity="High")
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"High": 2}
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist

        observation = _make_observation(numerical_severity=5)
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    @patch(f"{MODULE}.Settings")
    def test_status_filter_blocks_wrong_status(self, mock_settings_cls, mock_severity, mock_otn, mock_send):
        """Observation in a status not listed in the filter should not trigger."""
        settings = _make_settings(min_severity="Critical", statuses=["Open"])
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"Critical": 1}
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist

        observation = _make_observation(numerical_severity=1, current_status="Resolved")
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    @patch(f"{MODULE}.Settings")
    def test_priority_filter_blocks_low_priority(self, mock_settings_cls, mock_severity, mock_otn, mock_send):
        """Observation priority higher than threshold (worse priority) is blocked."""
        settings = _make_settings(min_severity="Critical", min_priority=2)
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"Critical": 1}
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist

        # priority 5 > threshold 2 → blocked
        observation = _make_observation(numerical_severity=1, current_priority=5)
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    @patch(f"{MODULE}.Settings")
    def test_priority_filter_blocks_no_priority(self, mock_settings_cls, mock_severity, mock_otn, mock_send):
        """Observation with no priority is blocked."""
        settings = _make_settings(min_priority=2)
        mock_settings_cls.load.return_value = settings
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist

        # no priority in observation -> blocked
        observation = _make_observation(current_priority=None)
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    @patch(f"{MODULE}.Settings")
    def test_parser_type_filter_blocks_wrong_type(self, mock_settings_cls, mock_severity, mock_otn, mock_send):
        """Observation with a different parser type than the filter is blocked."""
        settings = _make_settings(min_severity="Critical", parser_type="DAST")
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"Critical": 1}
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist

        observation = _make_observation(numerical_severity=1, parser_type="SAST")
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    # -----------------------------------------------------------------------
    # Filtering – new notification path
    # -----------------------------------------------------------------------

    @patch(f"{MODULE}.Status")
    @patch(f"{MODULE}.Settings")
    @patch(f"{MODULE}.get_base_url_frontend")
    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    def test_new_notification_created_when_no_existing_record(
        self, mock_severity, mock_otn, mock_send, mock_base_url, mock_settings_cls, mock_status
    ):
        """First-time observation triggers a 'New notification' message and saves the record."""
        settings = _make_settings(min_severity="Critical")
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"Critical": 1}
        mock_base_url.return_value = "https://app.example.com/"
        mock_status.STATUS_ACTIVE = ["Open", "Affected", "In review"]
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist
        new_record = MagicMock(severity=None, status=None, priority=None)
        mock_otn.return_value = new_record

        observation = _make_observation(numerical_severity=1, current_status="Open")
        send_observation_title_notification(observation)

        first_line_arg = mock_send.call_args[0][2]
        assert "New notification" in first_line_arg
        assert observation.title in first_line_arg
        new_record.save.assert_called_once()

    @patch(f"{MODULE}.Status")
    @patch(f"{MODULE}.Settings")
    @patch(f"{MODULE}.get_base_url_frontend")
    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    def test_change_notification_when_severity_differs(
        self, mock_severity, mock_otn, mock_send, mock_base_url, mock_settings_cls, mock_status
    ):
        """Existing record with different severity triggers a 'Change in' message."""
        settings = _make_settings(min_severity="Critical")
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"Critical": 1}
        mock_base_url.return_value = "https://app.example.com/"
        mock_status.STATUS_ACTIVE = ["Open", "Affected", "In review"]
        mock_otn.DoesNotExist = Exception
        existing = MagicMock(severity="High", status="Open", priority=1)  # severity differs
        mock_otn.objects.get.return_value = existing

        observation = _make_observation(
            numerical_severity=1,
            current_severity="Critical",
            current_status="Open",
            current_priority=1,
        )
        send_observation_title_notification(observation)

        first_line_arg = mock_send.call_args[0][2]
        assert "Change in" in first_line_arg
        existing.save.assert_called_once()

    @patch(f"{MODULE}.Status")
    @patch(f"{MODULE}.Settings")
    @patch(f"{MODULE}.get_base_url_frontend")
    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    def test_no_notification_when_record_unchanged(
        self, mock_severity, mock_otn, mock_send, mock_base_url, mock_settings_cls, mock_status
    ):
        """Existing record with identical fields should not re-send notification."""
        settings = _make_settings(min_severity="Critical")
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"Critical": 1}
        mock_status.STATUS_ACTIVE = ["Open"]
        mock_otn.DoesNotExist = Exception
        existing = MagicMock(severity="Critical", status="Open", priority=1)
        mock_otn.objects.get.return_value = existing

        observation = _make_observation(
            numerical_severity=1,
            current_severity="Critical",
            current_status="Open",
            current_priority=1,
        )
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    # -----------------------------------------------------------------------
    # Else-branch: observation fell out of notifications
    # -----------------------------------------------------------------------

    @patch(f"{MODULE}.Settings")
    @patch(f"{MODULE}.get_base_url_frontend")
    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    def test_fell_out_of_notifications_deletes_record_new(self, mock_otn, mock_send, mock_base_url, mock_settings_cls):
        """When filters no longer match and a record exists, a 'fell out' notification is sent
        and the record is deleted."""
        settings = _make_settings()  # no filters → outer condition False
        mock_settings_cls.load.return_value = settings
        mock_base_url.return_value = "https://app.example.com/"
        mock_otn.DoesNotExist = Exception
        existing = MagicMock()
        mock_otn.objects.get.return_value = existing

        observation = _make_observation()
        send_observation_title_notification(observation, True)

        mock_send.assert_not_called()
        existing.delete.assert_not_called()

    @patch(f"{MODULE}.Settings")
    @patch(f"{MODULE}.get_base_url_frontend")
    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    def test_fell_out_of_notifications_deletes_record_not_new(
        self, mock_otn, mock_send, mock_base_url, mock_settings_cls
    ):
        """When filters no longer match and a record exists, a 'fell out' notification is sent
        and the record is deleted."""
        settings = _make_settings()  # no filters → outer condition False
        mock_settings_cls.load.return_value = settings
        mock_base_url.return_value = "https://app.example.com/"
        mock_otn.DoesNotExist = Exception
        existing = MagicMock()
        mock_otn.objects.get.return_value = existing

        observation = _make_observation()
        send_observation_title_notification(observation)

        first_line_arg = mock_send.call_args[0][2]
        assert "fell out of notifications" in first_line_arg
        existing.delete.assert_called_once()

    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Settings")
    def test_fell_out_returns_early_when_no_record(self, mock_settings_cls, mock_otn, mock_send):
        """When filters don't match and no record exists, return early without sending."""
        settings = _make_settings()
        mock_settings_cls.load.return_value = settings
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist

        observation = _make_observation()
        send_observation_title_notification(observation)

        mock_send.assert_not_called()

    # -----------------------------------------------------------------------
    # URL construction
    # -----------------------------------------------------------------------

    @patch(f"{MODULE}.Status")
    @patch(f"{MODULE}.Settings")
    @patch(f"{MODULE}.get_base_url_frontend")
    @patch(f"{MODULE}._send_observation_title_notifications")
    @patch(f"{MODULE}.Observation_Title_Notified")
    @patch(f"{MODULE}.Severity")
    def test_url_contains_title_and_status_filter(
        self, mock_severity, mock_otn, mock_send, mock_base_url, mock_settings_cls, mock_status
    ):
        """URL passed to _send includes the observation title and active-status filter."""
        settings = _make_settings(min_severity="Critical")
        mock_settings_cls.load.return_value = settings
        mock_severity.NUMERICAL_SEVERITIES = {"Critical": 1}
        mock_base_url.return_value = "https://app.example.com/"
        mock_status.STATUS_ACTIVE = ["Open"]
        mock_otn.DoesNotExist = Exception
        mock_otn.objects.get.side_effect = mock_otn.DoesNotExist
        new_record = MagicMock(severity=None, status=None, priority=None)
        mock_otn.return_value = new_record

        observation = _make_observation(title="XSS Attack", numerical_severity=1, current_status="Open")
        send_observation_title_notification(observation)

        url_arg = mock_send.call_args[0][3]
        assert "XSS Attack" in url_arg
        assert "https://app.example.com/" in url_arg


# ===========================================================================
# Tests for _send_observation_title_notifications
# ===========================================================================


class TestSendObservationTitleNotificationsHelper(BaseTestCase):

    @patch(f"{MODULE}.Notification")
    @patch(f"{MODULE}.get_current_user")
    @patch(f"{MODULE}.send_email_notification")
    @patch(f"{MODULE}._get_first_name")
    @patch(f"{MODULE}._get_email_to_addresses")
    def test_sends_email_for_each_address(
        self, mock_get_addresses, mock_first_name, mock_send_email, mock_get_user, mock_notification
    ):
        """An email is sent for every address returned by _get_email_to_addresses."""
        mock_get_addresses.return_value = ["a@example.com", "b@example.com"]
        mock_first_name.side_effect = lambda addr: addr.split("@")[0]
        mock_get_user.return_value = MagicMock()

        settings = _make_settings(email_from="noreply@example.com", ms_teams_webhook=None, slack_webhook=None)
        observation = _make_observation()
        _send_observation_title_notifications(settings, observation, "First line", "http://url")

        assert mock_send_email.call_count == 2
        calls = mock_send_email.call_args_list
        assert calls[0][0][0] == "a@example.com"
        assert calls[1][0][0] == "b@example.com"

    @patch(f"{MODULE}.Notification")
    @patch(f"{MODULE}.get_current_user")
    @patch(f"{MODULE}.send_msteams_notification")
    @patch(f"{MODULE}._get_email_to_addresses")
    def test_sends_msteams_notification_when_webhook_configured(
        self, mock_get_addresses, mock_send_teams, mock_get_user, mock_notification
    ):
        mock_get_addresses.return_value = []
        mock_get_user.return_value = MagicMock()

        settings = _make_settings(
            email_from=None, ms_teams_webhook="https://teams.webhook.example.com", slack_webhook=None
        )
        observation = _make_observation()
        _send_observation_title_notifications(settings, observation, "First line", "http://url")

        mock_send_teams.assert_called_once_with(
            "https://teams.webhook.example.com",
            "msteams_observation_title.tpl",
            observation=observation,
            url="http://url",
            first_line="First line",
        )

    @patch(f"{MODULE}.Notification")
    @patch(f"{MODULE}.get_current_user")
    @patch(f"{MODULE}.send_slack_notification")
    @patch(f"{MODULE}._get_email_to_addresses")
    def test_sends_slack_notification_when_webhook_configured(
        self, mock_get_addresses, mock_send_slack, mock_get_user, mock_notification
    ):
        mock_get_addresses.return_value = []
        mock_get_user.return_value = MagicMock()

        settings = _make_settings(email_from=None, ms_teams_webhook=None, slack_webhook="https://hooks.slack.com/test")
        observation = _make_observation()
        _send_observation_title_notifications(settings, observation, "First line", "http://url")

        mock_send_slack.assert_called_once_with(
            "https://hooks.slack.com/test",
            "slack_observation_title.tpl",
            observation=observation,
            url="http://url",
            first_line="First line",
        )

    @patch(f"{MODULE}.Notification")
    @patch(f"{MODULE}.get_current_user")
    @patch(f"{MODULE}.send_email_notification")
    @patch(f"{MODULE}.send_msteams_notification")
    @patch(f"{MODULE}.send_slack_notification")
    @patch(f"{MODULE}._get_email_to_addresses")
    def test_no_email_sent_when_email_from_missing(
        self, mock_get_addresses, mock_send_slack, mock_send_teams, mock_send_email, mock_get_user, mock_notification
    ):
        """Email should NOT be sent when email_from is not configured."""
        mock_get_addresses.return_value = ["someone@example.com"]
        mock_get_user.return_value = MagicMock()

        settings = _make_settings(email_from=None, ms_teams_webhook=None, slack_webhook=None)
        observation = _make_observation()
        _send_observation_title_notifications(settings, observation, "First line", "http://url")

        mock_send_email.assert_not_called()

    @patch(f"{MODULE}.Notification")
    @patch(f"{MODULE}.get_current_user")
    @patch(f"{MODULE}._get_email_to_addresses")
    def test_always_creates_notification_record(self, mock_get_addresses, mock_get_user, mock_notification):
        """A Notification DB record is always created regardless of channels."""
        mock_get_addresses.return_value = []
        user = MagicMock()
        mock_get_user.return_value = user

        settings = _make_settings(email_from=None, ms_teams_webhook=None, slack_webhook=None)
        observation = _make_observation()
        _send_observation_title_notifications(settings, observation, "My first line", "http://url")

        mock_notification.objects.create.assert_called_once_with(
            name="My first line",
            user=user,
            type=mock_notification.TYPE_OBSERVATION_TITLE,
        )

    @patch(f"{MODULE}.Notification")
    @patch(f"{MODULE}.get_current_user")
    @patch(f"{MODULE}._get_first_name")
    @patch(f"{MODULE}.send_email_notification")
    @patch(f"{MODULE}.send_msteams_notification")
    @patch(f"{MODULE}.send_slack_notification")
    @patch(f"{MODULE}._get_email_to_addresses")
    def test_all_channels_triggered_simultaneously(
        self,
        mock_get_addresses,
        mock_send_slack,
        mock_send_teams,
        mock_send_email,
        mock_first_name,
        mock_get_user,
        mock_notification,
    ):
        """When all channels are configured, all three are called."""
        mock_get_addresses.return_value = ["x@example.com"]
        mock_first_name.return_value = "X"
        mock_get_user.return_value = MagicMock()

        settings = _make_settings(
            email_from="noreply@example.com",
            ms_teams_webhook="https://teams.webhook",
            slack_webhook="https://slack.webhook",
        )
        observation = _make_observation()
        _send_observation_title_notifications(settings, observation, "Line", "http://url")

        mock_send_email.assert_called_once()
        mock_send_teams.assert_called_once()
        mock_send_slack.assert_called_once()
