from datetime import timedelta
from unittest.mock import ANY, call, patch

from django.db import OperationalError
from django.utils import timezone

from application.commons.models import Settings
from application.notifications.models import Notification
from application.notifications.services.send_notifications_exception import (
    LAST_EXCEPTIONS,
    _get_stack_trace,
    _ratelimit_exception,
    send_email_notification_background,
    send_exception_notification,
    send_msteams_notification_background,
    send_slack_notification_background,
    send_task_exception_notification,
)
from unittests.base_test_case import BaseTestCase


class TestPushNotifications(BaseTestCase):
    # --- send_exception_notification ---

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_exception._ratelimit_exception")
    @patch("application.notifications.services.send_notifications_exception.send_msteams_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_slack_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_email_notification_background")
    @patch("application.notifications.services.send_notifications_exception.get_current_user")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_exception_notification_no_webhook_no_email(
        self,
        mock_notification_create,
        mock_current_user,
        mock_send_email,
        mock_send_slack,
        mock_send_teams,
        mock_ratelimit,
        mock_settings_load,
    ):
        mock_settings_load.return_value = Settings()
        mock_ratelimit.return_value = True
        mock_current_user.return_value = self.user_internal

        send_exception_notification(Exception("test_exception"))

        mock_send_teams.assert_not_called()
        mock_send_slack.assert_not_called()
        mock_send_email.assert_not_called()
        mock_notification_create.assert_called_with(
            name='Exception "builtins.Exception" has occured',
            message="test_exception",
            user=self.user_internal,
            type=Notification.TYPE_EXCEPTION,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_exception._ratelimit_exception")
    @patch("application.notifications.services.send_notifications_exception.send_msteams_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_slack_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_email_notification_background")
    def test_send_exception_notification_no_ratelimit(
        self,
        mock_send_email,
        mock_send_slack,
        mock_send_teams,
        mock_ratelimit,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        settings.exception_email_to = "test1@example.com, test2@example.com"
        settings.exception_ms_teams_webhook = "https://msteams.microsoft.com"
        settings.exception_slack_webhook = "https://secobserve.slack.com"
        mock_settings_load.return_value = settings
        mock_ratelimit.return_value = False
        exception = Exception("test_exception")
        send_exception_notification(exception)
        mock_ratelimit.assert_called_with(exception)
        mock_send_teams.assert_not_called()
        mock_send_slack.assert_not_called()
        mock_send_email.assert_not_called()

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_exception._ratelimit_exception")
    @patch("application.notifications.services.send_notifications_exception.send_msteams_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_slack_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_email_notification_background")
    @patch("application.notifications.services.send_notifications_exception._get_first_name")
    @patch("application.notifications.services.send_notifications_exception.get_current_user")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_exception_notification_success(
        self,
        mock_notification_create,
        mock_current_user,
        mock_get_first_name,
        mock_send_email,
        mock_send_slack,
        mock_send_teams,
        mock_ratelimit,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        settings.exception_email_to = "test1@example.com, test2@example.com"
        settings.exception_ms_teams_webhook = "https://msteams.microsoft.com"
        settings.exception_slack_webhook = "https://secobserve.slack.com"
        mock_settings_load.return_value = settings
        mock_ratelimit.return_value = True
        mock_get_first_name.return_value = "first_name"
        mock_current_user.return_value = self.user_internal

        exception = Exception("test_exception")
        send_exception_notification(exception)

        mock_ratelimit.assert_called_with(exception)
        expected_calls_email = [
            call(
                "test1@example.com",
                'Exception "builtins.Exception" has occured',
                "email/exception.tpl",
                exception_class="builtins.Exception",
                exception_message="test_exception",
                exception_trace="",
                date_time=ANY,
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                'Exception "builtins.Exception" has occured',
                "email/exception.tpl",
                exception_class="builtins.Exception",
                exception_message="test_exception",
                exception_trace="",
                date_time=ANY,
                first_name="first_name",
            ),
        ]
        mock_send_email.assert_has_calls(expected_calls_email)
        mock_send_teams.assert_called_with(
            "https://msteams.microsoft.com",
            "msteams_v2/exception.tpl",
            exception_class="builtins.Exception",
            exception_message="test_exception",
            exception_trace="",
            date_time=ANY,
        )
        mock_send_slack.assert_called_with(
            "https://secobserve.slack.com",
            "slack/exception.tpl",
            exception_class="builtins.Exception",
            exception_message="test_exception",
            exception_trace="",
            date_time=ANY,
        )
        expected_calls_get_first_name = [
            call("test1@example.com"),
            call("test2@example.com"),
        ]
        mock_get_first_name.assert_has_calls(expected_calls_get_first_name)
        mock_notification_create.assert_called_with(
            name='Exception "builtins.Exception" has occured',
            message="test_exception",
            user=self.user_internal,
            type=Notification.TYPE_EXCEPTION,
        )

    # --- send_task_exception_notification ---

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_exception._ratelimit_exception")
    @patch("application.notifications.services.send_notifications_exception.send_msteams_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_slack_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_email_notification_background")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_task_exception_notification_no_webhook_no_email(
        self,
        mock_notification_create,
        mock_send_email,
        mock_send_slack,
        mock_send_teams,
        mock_ratelimit,
        mock_settings_load,
    ):
        mock_settings_load.return_value = Settings()
        arguments = {"argument": "test_argument"}
        mock_ratelimit.return_value = True
        send_task_exception_notification(
            function="test_function",
            arguments=arguments,
            user=self.user_internal,
            exception=Exception("test_exception"),
        )
        mock_send_teams.assert_not_called()
        mock_send_slack.assert_not_called()
        mock_send_email.assert_not_called()
        mock_notification_create.assert_called_with(
            name='Exception "builtins.Exception" has occured',
            message="test_exception",
            function="test_function",
            arguments="{'argument': 'test_argument'}",
            product=None,
            observation=None,
            user=self.user_internal,
            type=Notification.TYPE_TASK,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_exception._ratelimit_exception")
    @patch("application.notifications.services.send_notifications_exception.send_msteams_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_slack_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_email_notification_background")
    def test_send_task_exception_notification_no_ratelimit(
        self,
        mock_send_email,
        mock_send_slack,
        mock_send_teams,
        mock_ratelimit,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        settings.exception_email_to = "test1@example.com, test2@example.com"
        settings.exception_ms_teams_webhook = "https://msteams.microsoft.com"
        settings.exception_slack_webhook = "https://secobserve.slack.com"
        mock_settings_load.return_value = settings
        mock_ratelimit.return_value = False
        exception = Exception("test_exception")
        send_task_exception_notification(
            function="test_function",
            arguments="test_arguments",
            user=self.user_internal,
            exception=exception,
        )
        mock_ratelimit.assert_called_with(exception, "test_function", "test_arguments", is_task=True)
        mock_send_teams.assert_not_called()
        mock_send_slack.assert_not_called()
        mock_send_email.assert_not_called()

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_exception._ratelimit_exception")
    @patch("application.notifications.services.send_notifications_exception.send_msteams_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_slack_notification_background")
    @patch("application.notifications.services.send_notifications_exception.send_email_notification_background")
    @patch("application.notifications.services.send_notifications_exception._get_first_name")
    @patch("application.notifications.models.Notification.objects.create")
    def test_send_task_exception_notification_success(
        self,
        mock_notification_create,
        mock_get_first_name,
        mock_send_email,
        mock_send_slack,
        mock_send_teams,
        mock_ratelimit,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        settings.exception_email_to = "test1@example.com, test2@example.com"
        settings.exception_ms_teams_webhook = "https://msteams.microsoft.com"
        settings.exception_slack_webhook = "https://secobserve.slack.com"
        mock_settings_load.return_value = settings
        mock_ratelimit.return_value = True
        mock_get_first_name.return_value = "first_name"

        exception = Exception("test_exception")
        arguments = {"observation": self.observation_1}
        send_task_exception_notification(
            function="test_function",
            arguments=arguments,
            user=self.user_internal,
            exception=exception,
        )

        mock_ratelimit.assert_called_with(exception, "test_function", arguments, is_task=True)
        expected_calls_email = [
            call(
                "test1@example.com",
                'Exception "builtins.Exception" has occured in background task',
                "email/task_exception.tpl",
                function="test_function",
                arguments=str(arguments),
                user=self.user_internal,
                exception_class="builtins.Exception",
                exception_message="test_exception",
                exception_trace="",
                date_time=ANY,
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                'Exception "builtins.Exception" has occured in background task',
                "email/task_exception.tpl",
                function="test_function",
                arguments=str(arguments),
                user=self.user_internal,
                exception_class="builtins.Exception",
                exception_message="test_exception",
                exception_trace="",
                date_time=ANY,
                first_name="first_name",
            ),
        ]
        mock_send_email.assert_has_calls(expected_calls_email)
        mock_send_teams.assert_called_with(
            "https://msteams.microsoft.com",
            "msteams_v2/task_exception.tpl",
            function="test_function",
            arguments=str(arguments),
            user=self.user_internal,
            exception_class="builtins.Exception",
            exception_message="test_exception",
            exception_trace="",
            date_time=ANY,
        )
        mock_send_slack.assert_called_with(
            "https://secobserve.slack.com",
            "slack/task_exception.tpl",
            function="test_function",
            arguments=str(arguments),
            user=self.user_internal,
            exception_class="builtins.Exception",
            exception_message="test_exception",
            exception_trace="",
            date_time=ANY,
        )
        expected_calls_get_first_name = [
            call("test1@example.com"),
            call("test2@example.com"),
        ]
        mock_get_first_name.assert_has_calls(expected_calls_get_first_name)
        mock_notification_create.assert_called_with(
            name='Exception "builtins.Exception" has occured',
            message="test_exception",
            function="test_function",
            arguments=str(arguments),
            product=self.product_1,
            observation=self.observation_1,
            user=self.user_internal,
            type=Notification.TYPE_TASK,
        )

    # --- _ratelimit_exception ---

    def _create_notification(self, seconds_ago, type=Notification.TYPE_EXCEPTION, message="test_exception", **kwargs):
        notification = Notification.objects.create(
            name='Exception "builtins.Exception" has occured',
            message=message,
            type=type,
            **kwargs,
        )
        Notification.objects.filter(pk=notification.pk).update(created=timezone.now() - timedelta(seconds=seconds_ago))

    def _create_task_notification(self, **kwargs):
        self._create_notification(
            1, type=Notification.TYPE_TASK, function="test_function", arguments="{'a': 1}", **kwargs
        )

    def _set_rate_limit(self, seconds):
        settings = Settings.load()
        settings.exception_rate_limit = seconds
        settings.save()

    def test_ratelimit_exception_no_notification(self):
        self._set_rate_limit(10)

        self.assertTrue(_ratelimit_exception(Exception("test_exception")))

    def test_ratelimit_exception_inside_window(self):
        self._set_rate_limit(10)
        self._create_notification(9)

        self.assertFalse(_ratelimit_exception(Exception("test_exception")))

    def test_ratelimit_exception_outside_window(self):
        self._set_rate_limit(10)
        self._create_notification(11)

        self.assertTrue(_ratelimit_exception(Exception("test_exception")))

    def test_ratelimit_exception_zero_always_notifies(self):
        self._set_rate_limit(0)
        self._create_notification(0)

        self.assertTrue(_ratelimit_exception(Exception("test_exception")))

    def test_ratelimit_exception_different_message(self):
        self._set_rate_limit(10)
        self._create_notification(1, message="other_exception")

        self.assertTrue(_ratelimit_exception(Exception("test_exception")))

    def test_ratelimit_exception_task_inside_window(self):
        self._set_rate_limit(10)
        self._create_task_notification()

        self.assertFalse(_ratelimit_exception(Exception("test_exception"), "test_function", {"a": 1}, is_task=True))

    def test_ratelimit_exception_task_different_function(self):
        self._set_rate_limit(10)
        self._create_task_notification()

        self.assertTrue(_ratelimit_exception(Exception("test_exception"), "other_function", {"a": 1}, is_task=True))

    def test_ratelimit_exception_task_different_arguments(self):
        self._set_rate_limit(10)
        self._create_task_notification()

        self.assertTrue(_ratelimit_exception(Exception("test_exception"), "test_function", {"a": 2}, is_task=True))

    def test_ratelimit_exception_request_ignores_task_notification(self):
        self._set_rate_limit(10)
        self._create_task_notification()

        self.assertTrue(_ratelimit_exception(Exception("test_exception")))

    def test_ratelimit_exception_task_without_function_and_arguments(self):
        self._set_rate_limit(10)
        exception = Exception("no_function_exception")
        self.assertTrue(_ratelimit_exception(exception, None, None, is_task=True))

        send_task_exception_notification(None, None, None, exception)

        notification = Notification.objects.get(type=Notification.TYPE_TASK, message="no_function_exception")
        self.assertEqual("None", notification.function)
        self.assertFalse(_ratelimit_exception(exception, None, None, is_task=True))

    def test_ratelimit_exception_task_without_function_ignores_request_notification(self):
        self._set_rate_limit(10)
        self._create_notification(1)

        self.assertTrue(_ratelimit_exception(Exception("test_exception"), None, None, is_task=True))

    @patch.dict(LAST_EXCEPTIONS, clear=True)
    def test_ratelimit_exception_database_error_limits_per_process(self):
        self._set_rate_limit(10)

        with patch.object(Notification.objects, "filter", side_effect=OperationalError("connection lost")):
            self.assertTrue(_ratelimit_exception(Exception("test_exception")))
            self.assertFalse(_ratelimit_exception(Exception("test_exception")))
            self.assertTrue(_ratelimit_exception(Exception("other_exception")))
            self.assertTrue(_ratelimit_exception(Exception("test_exception"), "test_function", None, is_task=True))

    @patch.dict(LAST_EXCEPTIONS, clear=True)
    def test_ratelimit_exception_database_error_outside_window(self):
        self._set_rate_limit(10)

        with patch.object(Notification.objects, "filter", side_effect=OperationalError("connection lost")):
            self.assertTrue(_ratelimit_exception(Exception("test_exception")))
            with patch(
                "application.notifications.services.send_notifications_exception.timezone.now",
                return_value=timezone.now() + timedelta(seconds=11),
            ):
                self.assertTrue(_ratelimit_exception(Exception("test_exception")))

    # --- _get_stack_trace ---

    @patch("application.notifications.services.send_notifications_exception.traceback.format_tb")
    def test_get_stack_trace_format_as_code(self, mock_format):
        mock_format.return_value = ["line1", "line2"]
        exception = Exception("test_exception")
        self.assertEqual("```\nline1line2\n```", _get_stack_trace(exception, True))
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_exception.traceback.format_tb")
    def test_get_stack_trace_plain(self, mock_format):
        mock_format.return_value = ["line1", "line2"]
        exception = Exception("test_exception")
        self.assertEqual("line1line2", _get_stack_trace(exception, False))
        mock_format.assert_called_once()

    # --- send_email_notification_background ---

    @patch("application.notifications.services.send_notifications_exception.send_email_notification")
    @patch("application.notifications.services.send_notifications_exception.logger.error")
    @patch("application.notifications.services.send_notifications_exception.format_log_message")
    def test_send_email_notification_background_exception(self, mock_format, mock_logger, mock_send_email):
        mock_send_email.side_effect = Exception("test_exception")

        # Exceptions of notifications for exceptions have to be swallowed, otherwise the
        # failed background task would trigger the next exception notification
        with self.captureOnCommitCallbacks(execute=True):
            send_email_notification_background("test@example.com", "subject", "test_template")

        mock_send_email.assert_called_once_with("test@example.com", "subject", "test_template")
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    # --- send_msteams_notification_background ---

    @patch("application.notifications.services.send_notifications_exception.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_exception.logger.error")
    @patch("application.notifications.services.send_notifications_exception.format_log_message")
    def test_send_msteams_notification_background_exception(self, mock_format, mock_logger, mock_send_msteams):
        mock_send_msteams.side_effect = Exception("test_exception")

        with self.captureOnCommitCallbacks(execute=True):
            send_msteams_notification_background("https://hooks.example.org/webhook", "test_template")

        mock_send_msteams.assert_called_once_with("https://hooks.example.org/webhook", "test_template")
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    # --- send_slack_notification_background ---

    @patch("application.notifications.services.send_notifications_exception.send_slack_notification")
    @patch("application.notifications.services.send_notifications_exception.logger.error")
    @patch("application.notifications.services.send_notifications_exception.format_log_message")
    def test_send_slack_notification_background_exception(self, mock_format, mock_logger, mock_send_slack):
        mock_send_slack.side_effect = Exception("test_exception")

        with self.captureOnCommitCallbacks(execute=True):
            send_slack_notification_background("https://hooks.example.org/webhook", "test_template")

        mock_send_slack.assert_called_once_with("https://hooks.example.org/webhook", "test_template")
        mock_logger.assert_called_once()
        mock_format.assert_called_once()
