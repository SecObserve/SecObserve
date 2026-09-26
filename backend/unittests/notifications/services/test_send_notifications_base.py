import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from requests import HTTPError, Response

import config.settings.base as settings_module
from application.access_control.models import User
from application.commons.models import Settings
from application.commons.services.functions import get_classname
from application.core.models import Observation, Observation_Log
from application.core.types import Severity, Status
from application.notifications.services.send_notifications_base import (
    _create_notification_message,
    _get_first_name,
    _get_notification_email_to,
    _get_notification_ms_teams_webhook,
    _get_notification_slack_webhook,
    _is_msteams_v2,
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
    send_user_notification,
)
from application.rules.models import Rule
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
            "msteams/product_security_gate.tpl",
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
            "msteams/exception.tpl",
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
    }]
}
"""
        self.assertEqual(expected_message, message)

    def test_create_notification_message_new_security_gate(self):
        message = _create_notification_message(
            "msteams_v2/product_security_gate.tpl",
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
            "msteams_v2/exception.tpl",
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

    def test_create_notification_message_observation_email_minimal(self):
        self.observation_1.current_severity = Severity.SEVERITY_HIGH
        self.observation_1.current_status = Status.STATUS_OPEN

        message = _create_notification_message(
            "email/observation.tpl",
            observation=self.observation_1,
            observation_url="observation_url",
            first_line="first_line",
            first_name=" Jane",
        )

        expected_message = """
Hello Jane,

first_line

Product:           product_1
Branch:            branch_1
Title:             observation_1
Severity:          High
Status:            Open
URL:               observation_url

Regards,

SecObserve

"""
        self.assertEqual(expected_message, message)

    def test_create_notification_message_observation_email_all_fields(self):
        self.observation_1.current_severity = Severity.SEVERITY_HIGH
        self.observation_1.current_status = Status.STATUS_OPEN
        self.observation_1.current_priority = 3
        self.observation_1.origin_service = self.service_1
        self.observation_1.vulnerability_id = "CVE-2024-12345"
        self.observation_1.origin_component_name_version = "component_1:1.0.0"
        self.observation_1.cvss3_score = Decimal("7.5")
        self.observation_1.cvss4_score = Decimal("8.7")
        self.observation_1.epss_score = Decimal("12.345")
        self.observation_1.scanner = "scanner_1 / 1.0.0"

        message = _create_notification_message(
            "email/observation.tpl",
            observation=self.observation_1,
            observation_url="observation_url",
            first_line="first_line",
            first_name=" Jane",
        )

        expected_message = """
Hello Jane,

first_line

Product:           product_1
Branch:            branch_1
Service:           service_1
Title:             observation_1
Vulnerability ID:  CVE-2024-12345
Component:         component_1:1.0.0
Severity:          High
CVSS 4 score:      8.7
CVSS 3 score:      7.5
EPSS score (%):    12.345
Status:            Open
Priority:          3
Scanner:           scanner_1 / 1.0.0
URL:               observation_url

Regards,

SecObserve

"""
        self.assertEqual(expected_message, message)

    def test_create_notification_message_backslash_breakout(self):
        # A backslash in an import-derived title must not break JSON string
        # parity in the hand-built Slack/Teams payloads (template-injection f013).
        self.observation_1.title = 'evil\\", "extra": "x'
        message = _create_notification_message(
            "msteams/observation.tpl",
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
            "msteams_v2/observation.tpl",
            observation=self.observation_1,
            observation_url="observation_url",
            first_line='New notification for observation "evil\\", "extra": "x"',
        )

        parsed = json.loads(message)
        card = parsed["attachments"][0]["content"]
        self.assertEqual(f"View observation {self.observation_1.title}", card["actions"][0]["title"])

    # --- is_msteams_v2 ---

    def testis_msteams_v2_office_com_is_v1(self):
        self.assertFalse(_is_msteams_v2("https://tenant.webhook.office.com/webhookb2/abc123"))

    def testis_msteams_v2_subdomain_office_com_is_v1(self):
        self.assertFalse(_is_msteams_v2("https://contoso.webhook.office.com/webhookb2/xyz"))

    def testis_msteams_v2_bare_webhook_office_com_is_v1(self):
        self.assertFalse(_is_msteams_v2("https://webhook.office.com/webhookb2/test"))

    def testis_msteams_v2_power_automate_is_v2(self):
        self.assertTrue(
            _is_msteams_v2("https://prod-42.westeurope.logic.azure.com/workflows/abc/triggers/manual/paths/invoke")
        )

    def testis_msteams_v2_generic_https_is_v2(self):
        self.assertTrue(_is_msteams_v2("https://hooks.example.org/webhook"))

    def testis_msteams_v2_empty_string_is_v2(self):
        self.assertTrue(_is_msteams_v2(""))

    def testis_msteams_v2_invalid_url_is_v2(self):
        self.assertTrue(_is_msteams_v2("not-a-url"))

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

    # --- templates of the user specific notifications ---

    def test_create_notification_message_assessment_approval_webhooks(self):
        """The rendered message is posted as the raw body of the request, so it has to be valid JSON."""
        self.observation_1.title = 'observation "1"'
        self.observation_log_1.comment = 'back\\slash and "quotes"'

        for template in (
            "msteams/assessment_approval.tpl",
            "msteams_v2/assessment_approval.tpl",
            "slack/assessment_approval.tpl",
        ):
            with self.subTest(template=template):
                message = _create_notification_message(
                    template,
                    observation=self.observation_1,
                    observation_log=self.observation_log_1,
                    observation_log_url="observation_log_url",
                    first_line="Assessment needs approval",
                )

                self.assertIsNotNone(message)
                json.loads(message)
                self.assertIn("Assessment needs approval", message)
                self.assertIn("observation_log_url", message)

    def test_create_notification_message_product_rule_webhooks(self):
        self.product_rule_1.new_severity = Severity.SEVERITY_HIGH
        self.product_rule_1.new_status = Status.STATUS_OPEN

        for template in (
            "msteams/product_rule.tpl",
            "msteams_v2/product_rule.tpl",
            "slack/product_rule.tpl",
        ):
            with self.subTest(template=template):
                message = _create_notification_message(
                    template,
                    rule=self.product_rule_1,
                    rule_url="rule_url",
                    first_line="Product rule needs approval",
                )

                self.assertIsNotNone(message)
                json.loads(message)
                self.assertIn("Product rule needs approval", message)
                self.assertIn("rule_url", message)
                self.assertIn("rule_1", message)

    # --- send_user_notification ---

    def _get_user(self, **kwargs) -> User:
        return User(id=10, username="jane@example.com", email="jane@example.com", full_name="Jane Doe", **kwargs)

    def _get_settings(self, email_from: str = "secobserve@example.com") -> Settings:
        settings = Settings()
        settings.email_from = email_from
        return settings

    @patch("application.notifications.services.send_notifications_base.send_slack_notification")
    @patch("application.notifications.services.send_notifications_base.send_msteams_notification")
    @patch("application.notifications.services.send_notifications_base.send_email_notification")
    def test_send_user_notification_email_only(self, mock_email, mock_msteams, mock_slack):
        send_user_notification(self._get_user(), self._get_settings(), "subject", "observation", key="value")

        mock_email.assert_called_once_with("jane@example.com", "subject", "email/observation.tpl", key="value")
        mock_msteams.assert_not_called()
        mock_slack.assert_not_called()

    @patch("application.notifications.services.send_notifications_base.send_email_notification")
    def test_send_user_notification_without_email_from(self, mock_email):
        send_user_notification(self._get_user(), self._get_settings(email_from=""), "subject", "observation")

        mock_email.assert_not_called()

    @patch("application.notifications.services.send_notifications_base.send_email_notification")
    def test_send_user_notification_email_already_notified(self, mock_email):
        send_user_notification(
            self._get_user(),
            self._get_settings(),
            "subject",
            "observation",
            notified_email_addresses={"jane@example.com"},
        )

        mock_email.assert_not_called()

    @patch("application.notifications.services.send_notifications_base.send_slack_notification")
    def test_send_user_notification_slack_already_notified(self, mock_slack):
        user = self._get_user(notification_slack_active=True, notification_slack_webhook="https://example.com/slack")

        send_user_notification(
            user,
            self._get_settings(email_from=""),
            "subject",
            "observation",
            notified_webhooks={"https://example.com/slack"},
        )

        mock_slack.assert_not_called()

    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.send_slack_notification")
    def test_send_user_notification_webhook_exception_is_logged(self, mock_slack, mock_logging):
        """One broken webhook must not stop the notifications of the other users."""
        mock_slack.side_effect = Exception("webhook is broken")
        user = self._get_user(notification_slack_active=True, notification_slack_webhook="https://example.com/slack")

        send_user_notification(user, self._get_settings(email_from=""), "subject", "observation")

        mock_slack.assert_called_once()
        mock_logging.assert_called_once()

    # --- every webhook template has to render as valid JSON ---

    def _get_template_contexts(self) -> dict:
        """A full and a sparse context per event. The sparse ones leave every optional field empty,
        which is what the conditional commas in the JSON templates have to survive."""
        self.observation_1.product = self.product_1
        self.observation_1.branch = self.branch_1
        self.observation_1.origin_service = self.service_1
        self.observation_1.vulnerability_id = "CVE-2024-1234"
        self.observation_1.origin_component_name_version = "django:5.1.8"
        self.observation_1.current_severity = Severity.SEVERITY_HIGH
        self.observation_1.current_status = Status.STATUS_OPEN
        self.observation_1.current_priority = 3
        self.observation_1.cvss4_score = Decimal("8.1")
        self.observation_1.cvss3_score = Decimal("7.5")
        self.observation_1.epss_score = Decimal("12.34")
        self.observation_1.scanner = "trivy"

        self.observation_log_1.priority_changed = True
        self.observation_log_1.vex_justification = "component_not_present"
        self.observation_log_1.comment = "looks fine"

        sparse_observation = Observation(
            title="observation_sparse",
            product=self.product_1,
            current_severity=Severity.SEVERITY_HIGH,
            current_status=Status.STATUS_OPEN,
        )
        sparse_log = Observation_Log(observation=sparse_observation)
        sparse_rule = Rule(name="rule_sparse", product=self.product_1)

        exception_context = {
            "exception_class": "builtins.Exception",
            "exception_message": "test_exception",
            "date_time": datetime(2022, 12, 31, 23, 59, 59),
            "exception_trace": "trace",
        }

        return {
            "observation": [
                {"observation": self.observation_1, "observation_url": "url", "first_line": "first line"},
                {"observation": sparse_observation, "observation_url": "url", "first_line": "first line"},
            ],
            "observation_title": [
                {"observation": self.observation_1, "url": "url", "first_line": "first line"},
                {"observation": sparse_observation, "url": "url", "first_line": "first line"},
            ],
            "assessment_approval": [
                {
                    "observation": self.observation_1,
                    "observation_log": self.observation_log_1,
                    "observation_log_url": "url",
                    "first_line": "first line",
                },
                {
                    "observation": sparse_observation,
                    "observation_log": sparse_log,
                    "observation_log_url": "url",
                    "first_line": "first line",
                },
            ],
            "product_rule": [
                {"rule": self.product_rule_1, "rule_url": "url", "first_line": "first line"},
                {"rule": sparse_rule, "rule_url": "url", "first_line": "first line"},
            ],
            "product_security_gate": [
                {"product": self.product_1, "security_gate_status": "Passed", "product_url": "url"},
            ],
            "exception": [exception_context],
            "task_exception": [
                {**exception_context, "function": "function", "arguments": "arguments", "user": self.user_internal},
            ],
            "test": [{}],
        }

    def test_all_webhook_templates_render_valid_json(self):
        templates = Path(settings_module.__file__).parent.parent.parent / "application/notifications/templates"
        contexts = self._get_template_contexts()
        checked = 0

        for channel in ("msteams", "msteams_v2", "slack"):
            for template in sorted((templates / channel).glob("*.tpl")):
                for context in contexts[template.stem]:
                    with self.subTest(template=f"{channel}/{template.stem}", context=context.get("observation")):
                        message = _create_notification_message(f"{channel}/{template.stem}.tpl", **context)
                        self.assertIsNotNone(message)
                        json.loads(message)
                        checked += 1

        # 3 channels * 8 templates, with a second context for the 4 templates that have optional fields
        self.assertEqual(36, checked)
