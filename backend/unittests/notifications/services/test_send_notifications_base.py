import json
import os
from datetime import datetime
from unittest.mock import patch

from requests import HTTPError, Response

from application.commons.models import Settings
from application.commons.services.functions import get_classname
from application.notifications.services.send_notifications_base import (
    _create_notification_message,
    _get_first_name,
    _get_notification_email_to,
    _get_notification_ms_teams_webhook,
    _get_notification_slack_webhook,
    is_msteams_v2,
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
)
from unittests.base_test_case import BaseTestCase


class TestPushNotifications(BaseTestCase):
    # --- send_email_notification ---

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.send_mail")
    def test_send_email_notification_empty_message(self, mock_send_email, mock_create_message):
        mock_create_message.return_value = None

        send_email_notification("test@example.com", "subject", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_send_email.assert_not_called()

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.send_mail")
    def test_send_email_notification_exception(
        self,
        mock_send_email,
        mock_create_message,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        mock_settings_load.return_value = settings
        mock_create_message.return_value = "test_message"
        exception = Exception("test_exception")
        mock_send_email.side_effect = exception

        with patch.dict(
            "os.environ",
            {
                "EMAIL_HOST": "mail.example.com",
            },
        ):
            # The exception is not swallowed, so that the background task calling this
            # function is marked as failed
            with self.assertRaises(Exception) as context:
                send_email_notification("test@example.com", "subject", "test_template")
            self.assertEqual(exception, context.exception)

        mock_create_message.assert_called_with("test_template")
        mock_send_email.assert_called_with(
            subject="subject",
            message="test_message",
            from_email="secobserve@example.com",
            recipient_list=["test@example.com"],
            fail_silently=False,
        )

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.send_mail")
    @patch.dict(os.environ, {"EMAIL_HOST": "email.example.org"})
    def test_send_email_notification_success(
        self,
        mock_send_email,
        mock_create_message,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        mock_settings_load.return_value = settings
        mock_create_message.return_value = "test_message"

        send_email_notification("test@example.com", "subject", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_send_email.assert_called_with(
            subject="subject",
            message="test_message",
            from_email="secobserve@example.com",
            recipient_list=["test@example.com"],
            fail_silently=False,
        )

    # --- send_msteams_notification ---

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_internal_host_blocked(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("127.0.0.1", 443))]

        send_msteams_notification("https://localhost/webhook", "test_template")

        mock_create_message.assert_not_called()
        mock_request.assert_not_called()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_empty_message(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = None

        send_msteams_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_not_called()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_exception(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        exception = Exception("test_exception")
        mock_request.side_effect = exception

        # The exception is not swallowed, so that the background task calling this
        # function is marked as failed
        with self.assertRaises(Exception) as context:
            send_msteams_notification("https://tenant.webhook.office.com/webhookb2/test", "test_template")
        self.assertEqual(exception, context.exception)

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://tenant.webhook.office.com/webhookb2/test",
            data="test_message",
            allow_redirects=False,
            headers={},
            timeout=60,
        )

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_not_ok(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 400
        mock_request.return_value = response

        with self.assertRaises(HTTPError):
            send_msteams_notification("https://tenant.webhook.office.com/webhookb2/test", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://tenant.webhook.office.com/webhookb2/test",
            data="test_message",
            headers={},
            allow_redirects=False,
            timeout=60,
        )

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_success(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        send_msteams_notification("https://tenant.webhook.office.com/webhookb2/test", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://tenant.webhook.office.com/webhookb2/test",
            data="test_message",
            allow_redirects=False,
            headers={},
            timeout=60,
        )

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_v2_format_exception(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        exception = Exception("test_exception")
        mock_request.side_effect = exception

        with self.assertRaises(Exception) as context:
            send_msteams_notification("https://hooks.example.org/webhook", "test_template")
        self.assertEqual(exception, context.exception)

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            headers={"Content-Type": "application/json"},
            allow_redirects=False,
            timeout=60,
        )

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_v2_format_success(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        send_msteams_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            headers={"Content-Type": "application/json"},
            allow_redirects=False,
            timeout=60,
        )

    # --- send_slack_notification ---

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_slack_notification_empty_message(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = None

        send_slack_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_not_called()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_slack_notification_exception(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        exception = Exception("test_exception")
        mock_request.side_effect = exception

        # The exception is not swallowed, so that the background task calling this
        # function is marked as failed
        with self.assertRaises(Exception) as context:
            send_slack_notification("https://hooks.example.org/webhook", "test_template")
        self.assertEqual(exception, context.exception)

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            allow_redirects=False,
            timeout=60,
        )

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_slack_notification_not_ok(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 400
        mock_request.return_value = response

        with self.assertRaises(HTTPError):
            send_slack_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            allow_redirects=False,
            timeout=60,
        )

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_slack_notification_success(self, mock_getaddrinfo, mock_request, mock_create_message):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        send_slack_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            allow_redirects=False,
            timeout=60,
        )

    # --- _create_notification_message ---

    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_create_notification_message_not_found(self, mock_format, mock_logging):
        message = _create_notification_message("invalid_template_name.tpl")
        self.assertIsNone(message)
        mock_logging.assert_called_once()
        mock_format.assert_called_once()

    def test_create_notification_message_security_gate(self):
        message = _create_notification_message(
            "msteams_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="security_gate_passed",
            product_url="product_url",
        )

        expected_message = """{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "Security gate for product product_1 has changed to security_gate_passed",
    "summary": "Security gate for product product_1 has changed to security_gate_passed",
    "potentialAction": [
        {
            "@type": "OpenUri",
            "name": "View Product product_1",
            "targets": [
                {
                    "os": "default",
                    "uri": "product_url"
                }
            ]
        }
    ]
}
"""
        self.assertEqual(expected_message, message)

    def test_create_notification_message_exception(self):
        exception = Exception("test_exception")
        message = _create_notification_message(
            "msteams_exception.tpl",
            exception_class=get_classname(exception),
            exception_message=str(exception),
            date_time=datetime(2022, 12, 31, 23, 59, 59),
        )

        expected_message = """{
    "@type": "MessageCard",
    "@context": "https://schema.org/extensions",
    "title": "Exception builtins.Exception has occured",
    "summary": "Exception builtins.Exception has occured",
    "sections": [{
        "facts": [{
            "name": "Exception class:",
            "value": "builtins.Exception"
        }, {
            "name": "Exception message:",
            "value": "test_exception"
        }, {
            "name": "Timestamp:",
            "value": "2022\\u002D12\\u002D31 23:59:59.000000"
        }, {
            "name": "Trace:",
            "value": ""
        }],
        "markdown": true
    }],
}
"""
        self.assertEqual(expected_message, message)

    def test_create_notification_message_new_security_gate(self):
        message = _create_notification_message(
            "msteams_v2_product_security_gate.tpl",
            product=self.product_1,
            security_gate_status="security_gate_passed",
            product_url="product_url",
        )

        expected_message = """{
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": null,
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Security gate for product product_1 has changed to security_gate_passed",
                        "weight": "bolder",
                        "size": "medium",
                        "wrap": true
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View Product product_1",
                        "url": "product_url"
                    }
                ]
            }
        }
    ]
}
"""
        self.assertEqual(expected_message, message)

    def test_create_notification_message_new_exception(self):
        exception = Exception("test_exception")
        message = _create_notification_message(
            "msteams_v2_exception.tpl",
            exception_class=get_classname(exception),
            exception_message=str(exception),
            date_time=datetime(2022, 12, 31, 23, 59, 59),
        )

        expected_message = """{
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "contentUrl": null,
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Exception builtins.Exception has occured",
                        "weight": "bolder",
                        "size": "medium",
                        "wrap": true
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Exception class:",
                                "value": "builtins.Exception"
                            },
                            {
                                "title": "Exception message:",
                                "value": "test_exception"
                            },
                            {
                                "title": "Timestamp:",
                                "value": "2022\\u002D12\\u002D31 23:59:59.000000"
                            },
                            {
                                "title": "Trace:",
                                "value": ""
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
"""

        self.assertEqual(expected_message, message)

    def test_create_notification_message_backslash_breakout(self):
        # A backslash in an import-derived title must not break JSON string
        # parity in the hand-built Slack/Teams payloads (template-injection f013).
        self.observation_1.title = 'evil\\", "extra": "x'
        message = _create_notification_message(
            "msteams_observation.tpl",
            observation=self.observation_1,
            observation_url="observation_url",
            first_line='New notification for observation "evil\\", "extra": "x"',
        )
        # Before the fix the rendered payload is not valid JSON because the
        # trailing backslash escapes the closing quote; after the fix it parses.
        parsed = json.loads(message)
        self.assertNotIn(
            "extra",
            [action["name"] for action in parsed["potentialAction"]][0].split("View observation ")[-1][:4],
        )

    def test_create_notification_message_backslash_breakout_msteams_v2(self):
        # The adaptive cards for Power Automate are hand-built JSON as well, so they need
        # the same escaping as the MessageCard and Slack templates
        self.observation_1.title = 'evil\\", "extra": "x'
        message = _create_notification_message(
            "msteams_v2_observation.tpl",
            observation=self.observation_1,
            observation_url="observation_url",
            first_line='New notification for observation "evil\\", "extra": "x"',
        )

        parsed = json.loads(message)
        card = parsed["attachments"][0]["content"]
        self.assertEqual(f"View observation {self.observation_1.title}", card["actions"][0]["title"])

    # --- is_msteams_v2 ---

    def testis_msteams_v2_office_com_is_v1(self):
        self.assertFalse(is_msteams_v2("https://tenant.webhook.office.com/webhookb2/abc123"))

    def testis_msteams_v2_subdomain_office_com_is_v1(self):
        self.assertFalse(is_msteams_v2("https://contoso.webhook.office.com/webhookb2/xyz"))

    def testis_msteams_v2_bare_webhook_office_com_is_v1(self):
        self.assertFalse(is_msteams_v2("https://webhook.office.com/webhookb2/test"))

    def testis_msteams_v2_power_automate_is_v2(self):
        self.assertTrue(
            is_msteams_v2("https://prod-42.westeurope.logic.azure.com/workflows/abc/triggers/manual/paths/invoke")
        )

    def testis_msteams_v2_generic_https_is_v2(self):
        self.assertTrue(is_msteams_v2("https://hooks.example.org/webhook"))

    def testis_msteams_v2_empty_string_is_v2(self):
        self.assertTrue(is_msteams_v2(""))

    def testis_msteams_v2_invalid_url_is_v2(self):
        self.assertTrue(is_msteams_v2("not-a-url"))

    # --- _get_first_name ---

    @patch("application.notifications.services.send_notifications_base.get_user_by_email")
    def test_get_user_first_name_no_user(self, mock_get_user):
        mock_get_user.return_value = None
        self.assertEqual("", _get_first_name("test@example.com"))
        mock_get_user.assert_called_once_with("test@example.com")

    @patch("application.notifications.services.send_notifications_base.get_user_by_email")
    def test_get_user_first_name_no_first_name(self, mock_get_user):
        mock_get_user.return_value = self.user_internal
        self.assertEqual("", _get_first_name("test@example.com"))
        mock_get_user.assert_called_once_with("test@example.com")

    @patch("application.notifications.services.send_notifications_base.get_user_by_email")
    def test_get_user_first_name_success(self, mock_get_user):
        mock_get_user.return_value = self.user_internal
        self.user_internal.first_name = "first_name"
        self.assertEqual(" first_name", _get_first_name("test@example.com"))
        mock_get_user.assert_called_once_with("test@example.com")

    # --- _get_notification_email_to ---

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

    # --- _get_notification_ms_teams_webhook ---

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

    # --- _get_notification_slack_webhook ---

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
