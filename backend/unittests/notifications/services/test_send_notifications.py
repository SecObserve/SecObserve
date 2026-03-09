import unittest
from datetime import datetime, timedelta
from unittest.mock import ANY, MagicMock, call, patch

from django.test import TestCase
from requests import Response

from application.access_control.models import User
from application.commons.models import Settings
from application.commons.services.functions import get_classname
from application.core.models import Observation, Product
from application.notifications.models import Notification, Observation_Notified
from application.notifications.services.send_notifications import (
    LAST_EXCEPTIONS,
    _get_first_name,
    _get_notification_email_to,
    _get_notification_ms_teams_webhook,
    _get_notification_slack_webhook,
    _get_stack_trace,
    _ratelimit_exception,
    _send_observation_notifications,
    get_base_url_frontend,
    send_exception_notification,
    send_observation_notification,
    send_product_security_gate_notification,
    send_task_exception_notification,
)
from unittests.base_test_case import BaseTestCase


class TestPushNotifications(BaseTestCase):
    # --- send_product_security_gate_notification ---

    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications.get_current_user")
    @patch("application.notifications.services.send_notifications._get_notification_email_to")
    @patch("application.notifications.services.send_notifications._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications._get_notification_ms_teams_webhook")
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
    ):
        mock_current_user.return_value = self.user_internal
        mock_get_notification_email_to.return_value = ""
        mock_get_notification_ms_teams_webhook.return_value = ""
        mock_get_notification_slack_webhook.return_value = ""

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
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications._get_first_name")
    @patch("application.notifications.services.send_notifications.get_current_user")
    @patch("application.notifications.services.send_notifications._get_notification_email_to")
    @patch("application.notifications.services.send_notifications._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications._get_notification_ms_teams_webhook")
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
        self.product_1.security_gate_passed = None
        self.product_1.pk = 1

        send_product_security_gate_notification(self.product_1)

        mock_get_notification_email_to.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        expected_calls_email = [
            call(
                "test1@example.com",
                "Security gate for product_1 has changed to None",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="None",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                "Security gate for product_1 has changed to None",
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
            "msteams_product_security_gate.tpl",
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
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications._get_first_name")
    @patch("application.notifications.services.send_notifications.get_current_user")
    @patch("application.notifications.services.send_notifications._get_notification_email_to")
    @patch("application.notifications.services.send_notifications._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications._get_notification_ms_teams_webhook")
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
        self.product_1.security_gate_passed = True
        self.product_1.pk = 1

        send_product_security_gate_notification(self.product_1)

        mock_get_notification_email_to.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        mock_get_notification_slack_webhook.assert_called_with(self.product_1)
        expected_calls_email = [
            call(
                "test1@example.com",
                "Security gate for product_1 has changed to Passed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Passed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                "Security gate for product_1 has changed to Passed",
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
            "msteams_product_security_gate.tpl",
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
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications._get_first_name")
    @patch("application.notifications.services.send_notifications.get_current_user")
    @patch("application.notifications.services.send_notifications._get_notification_email_to")
    @patch("application.notifications.services.send_notifications._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications._get_notification_ms_teams_webhook")
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
        self.product_1.security_gate_passed = False
        self.product_1.pk = 1

        send_product_security_gate_notification(self.product_1)

        mock_get_notification_email_to.assert_called_with(self.product_1)
        mock_get_notification_ms_teams_webhook.assert_called_with(self.product_1)
        mock_get_notification_slack_webhook.assert_called_with(self.product_1)
        expected_calls_email = [
            call(
                "test1@example.com",
                "Security gate for product_1 has changed to Failed",
                "email_product_security_gate.tpl",
                product=self.product_1,
                security_gate_status="Failed",
                product_url="https://secobserve.com/#/products/1/show",
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                "Security gate for product_1 has changed to Failed",
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
            "msteams_product_security_gate.tpl",
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

    # --- send_exception_notification ---

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications._ratelimit_exception")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications.get_current_user")
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
    @patch("application.notifications.services.send_notifications._ratelimit_exception")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
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
    @patch("application.notifications.services.send_notifications._ratelimit_exception")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications._get_first_name")
    @patch("application.notifications.services.send_notifications.get_current_user")
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
                "email_exception.tpl",
                exception_class="builtins.Exception",
                exception_message="test_exception",
                exception_trace="",
                date_time=ANY,
                first_name="first_name",
            ),
            call(
                "test2@example.com",
                'Exception "builtins.Exception" has occured',
                "email_exception.tpl",
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
            "msteams_exception.tpl",
            exception_class="builtins.Exception",
            exception_message="test_exception",
            exception_trace="",
            date_time=ANY,
        )
        mock_send_slack.assert_called_with(
            "https://secobserve.slack.com",
            "slack_exception.tpl",
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
    @patch("application.notifications.services.send_notifications._ratelimit_exception")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
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
    @patch("application.notifications.services.send_notifications._ratelimit_exception")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
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
        mock_ratelimit.assert_called_with(exception, "test_function", "test_arguments")
        mock_send_teams.assert_not_called()
        mock_send_slack.assert_not_called()
        mock_send_email.assert_not_called()

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications._ratelimit_exception")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications._get_first_name")
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

        mock_ratelimit.assert_called_with(exception, "test_function", arguments)
        expected_calls_email = [
            call(
                "test1@example.com",
                'Exception "builtins.Exception" has occured in background task',
                "email_task_exception.tpl",
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
                "email_task_exception.tpl",
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
            "msteams_task_exception.tpl",
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
            "slack_task_exception.tpl",
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

    # --- get_base_url_frontend ---

    @patch("application.commons.models.Settings.load")
    def testget_base_url_frontend_without_slash(self, mock_settings_load):
        settings = Settings()
        settings.base_url_frontend = "https://www.example.com"
        mock_settings_load.return_value = settings

        self.assertEqual("https://www.example.com/", get_base_url_frontend())

    @patch("application.commons.models.Settings.load")
    def testget_base_url_frontend_with_slash(self, mock_settings_load):
        settings = Settings()
        settings.base_url_frontend = "https://www.example.com"
        mock_settings_load.return_value = settings

        self.assertEqual("https://www.example.com/", get_base_url_frontend())

    # --- _ratelimit_exception ---

    def test_ratelimit_exception_new_key(self):
        LAST_EXCEPTIONS.clear()
        exception = Exception("test_exception")

        self.assertTrue(_ratelimit_exception(exception))
        self.assertEqual(1, len(LAST_EXCEPTIONS.keys()))

        difference: timedelta = datetime.now() - LAST_EXCEPTIONS["builtins.Exception/test_exception/None/"]
        self.assertGreater(difference.microseconds, 0)
        self.assertLess(difference.microseconds, 999)

    @patch("application.commons.models.Settings.load")
    def test_ratelimit_exception_true(self, mock_settings_load):
        settings = Settings()
        settings.exception_rate_limit = 10
        mock_settings_load.return_value = settings

        LAST_EXCEPTIONS.clear()
        LAST_EXCEPTIONS["builtins.Exception/test_exception/test_function/test_arguments"] = datetime.now() - timedelta(
            seconds=11
        )
        exception = Exception("test_exception")

        self.assertTrue(_ratelimit_exception(exception, "test_function", "test_arguments"))
        self.assertEqual(1, len(LAST_EXCEPTIONS.keys()))

    @patch("application.commons.models.Settings.load")
    def test_ratelimit_exception_false(self, mock_settings_load):
        settings = Settings()
        settings.exception_rate_limit = 10
        mock_settings_load.return_value = settings

        LAST_EXCEPTIONS.clear()
        LAST_EXCEPTIONS["builtins.Exception/test_exception/test_function/test_arguments"] = datetime.now() - timedelta(
            seconds=9
        )
        exception = Exception("test_exception")

        self.assertFalse(_ratelimit_exception(exception, "test_function", "test_arguments"))
        self.assertEqual(1, len(LAST_EXCEPTIONS.keys()))

    ## --- _get_user_first_name ---

    @patch("application.notifications.services.send_notifications.get_user_by_email")
    def test_get_user_first_name_no_user(self, mock_get_user):
        mock_get_user.return_value = None
        self.assertEqual("", _get_first_name("test@example.com"))
        mock_get_user.assert_called_once_with("test@example.com")

    @patch("application.notifications.services.send_notifications.get_user_by_email")
    def test_get_user_first_name_no_first_name(self, mock_get_user):
        mock_get_user.return_value = self.user_internal
        self.assertEqual("", _get_first_name("test@example.com"))
        mock_get_user.assert_called_once_with("test@example.com")

    @patch("application.notifications.services.send_notifications.get_user_by_email")
    def test_get_user_first_name_success(self, mock_get_user):
        mock_get_user.return_value = self.user_internal
        self.user_internal.first_name = "first_name"
        self.assertEqual(" first_name", _get_first_name("test@example.com"))
        mock_get_user.assert_called_once_with("test@example.com")

    ## --- _get_stack_trace ---

    @patch("application.notifications.services.send_notifications.traceback.format_tb")
    def test_get_stack_trace_format_as_code(self, mock_format):
        mock_format.return_value = ["line1", "line2"]
        exception = Exception("test_exception")
        self.assertEqual("```\nline1line2\n```", _get_stack_trace(exception, True))
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications.traceback.format_tb")
    def test_get_stack_trace_plain(self, mock_format):
        mock_format.return_value = ["line1", "line2"]
        exception = Exception("test_exception")
        self.assertEqual("line1line2", _get_stack_trace(exception, False))
        mock_format.assert_called_once()

    ## --- _get_notification_email_to ---

    def test_notification_email_to_product_email_to(self):
        self.product_1.notification_email_to = "test@example.com"
        self.assertEqual("test@example.com", _get_notification_email_to(self.product_1))

    def test_notification_email_to_product_group_email_to(self):
        self.product_group_1.notification_email_to = "test@example.com"
        self.product_1.product_group = self.product_group_1
        self.assertEqual("test@example.com", _get_notification_email_to(self.product_1))

    def test_notification_email_to_product_group_email_to_empty(self):
        self.product_1.product_group = self.product_group_1
        self.assertEqual(None, _get_notification_email_to(self.product_1))

    def test_notification_email_to_product_email_to_empty(self):
        self.assertEqual(None, _get_notification_email_to(self.product_1))

    ## --- _get_notification_ms_teams_webhook ---

    def test_get_notification_ms_teams_webhook_product_webhook(self):
        self.product_1.notification_ms_teams_webhook = "test@example.com"
        self.assertEqual("test@example.com", _get_notification_ms_teams_webhook(self.product_1))

    def test_get_notification_ms_teams_webhook_product_group_webhook(self):
        self.product_group_1.notification_ms_teams_webhook = "test@example.com"
        self.product_1.product_group = self.product_group_1
        self.assertEqual("test@example.com", _get_notification_ms_teams_webhook(self.product_1))

    def test_get_notification_ms_teams_webhook_product_group_webhook_empty(self):
        self.product_1.product_group = self.product_group_1
        self.assertEqual(None, _get_notification_ms_teams_webhook(self.product_1))

    def test_get_notification_ms_teams_webhook_product_webhook_empty(self):
        self.assertEqual(None, _get_notification_ms_teams_webhook(self.product_1))

    ## --- _get_notification_slack_webhook ---

    def test_get_notification_slack_webhook_product_webhook(self):
        self.product_1.notification_slack_webhook = "test@example.com"
        self.assertEqual("test@example.com", _get_notification_slack_webhook(self.product_1))

    def test_get_notification_slack_webhook_product_group_webhook(self):
        self.product_group_1.notification_slack_webhook = "test@example.com"
        self.product_1.product_group = self.product_group_1
        self.assertEqual("test@example.com", _get_notification_slack_webhook(self.product_1))

    def test_get_notification_slack_webhook_product_group_webhook_empty(self):
        self.product_1.product_group = self.product_group_1
        self.assertEqual(None, _get_notification_slack_webhook(self.product_1))

    def test_get_notification_slack_webhook_product_webhook_empty(self):
        self.assertEqual(None, _get_notification_slack_webhook(self.product_1))

    # --- send_observation_notification ---

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
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

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
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

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
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

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
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

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
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

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
    @patch("application.notifications.services.send_notifications.Severity")
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

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
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

    @patch("application.notifications.services.send_notifications._send_observation_notifications")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_priority")
    @patch("application.notifications.services.send_notifications._get_observation_notification_statuses")
    @patch("application.notifications.services.send_notifications._get_observation_notification_min_severity")
    @patch("application.notifications.services.send_notifications.Severity")
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

    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications.get_current_user")
    @patch("application.notifications.services.send_notifications._get_notification_email_to")
    @patch("application.notifications.services.send_notifications._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications._get_notification_ms_teams_webhook")
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
            name=f"New notification for observation",
            product=self.observation_1.product,
            observation=self.observation_1,
            user=self.user_internal,
            type=Notification.TYPE_OBSERVATION,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications.send_slack_notification")
    @patch("application.notifications.services.send_notifications.send_msteams_notification")
    @patch("application.notifications.services.send_notifications.send_email_notification")
    @patch("application.notifications.services.send_notifications.get_base_url_frontend")
    @patch("application.notifications.services.send_notifications._get_first_name")
    @patch("application.notifications.services.send_notifications.get_current_user")
    @patch("application.notifications.services.send_notifications._get_notification_email_to")
    @patch("application.notifications.services.send_notifications._get_notification_slack_webhook")
    @patch("application.notifications.services.send_notifications._get_notification_ms_teams_webhook")
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
