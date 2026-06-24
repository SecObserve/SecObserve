import json
import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import requests
from requests import Response

from application.commons.models import Settings
from application.commons.services.functions import get_classname
from application.notifications.services.send_notifications_base import (
    _create_notification_message,
    _get_msteams_workflow_template,
    _is_msteams_workflow_webhook,
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
)
from unittests.base_test_case import BaseTestCase

# Fictional Power Automate "Workflows" webhook URL (host suffix + /workflows/
# path + explicit :443 port) used only to exercise the detection logic.
WORKFLOW_WEBHOOK = (
    "https://example.environment.api.powerplatform.com:443"
    "/powerautomate/automations/direct/workflows/00000000000000000000000000000000"
    "/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=test-signature"
)


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
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_send_email_notification_exception(
        self,
        mock_format,
        mock_logger,
        mock_send_email,
        mock_create_message,
        mock_settings_load,
    ):
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        mock_settings_load.return_value = settings
        mock_create_message.return_value = "test_message"
        mock_send_email.side_effect = Exception("test_exception")

        with patch.dict(
            "os.environ",
            {
                "EMAIL_HOST": "mail.example.com",
            },
        ):
            send_email_notification("test@example.com", "subject", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_send_email.assert_called_with(
            subject="subject",
            message="test_message",
            from_email="secobserve@example.com",
            recipient_list=["test@example.com"],
            fail_silently=False,
        )
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.commons.models.Settings.load")
    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.send_mail")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch.dict(os.environ, {"EMAIL_HOST": "email.example.org"})
    def test_send_email_notification_success(
        self,
        mock_format,
        mock_logger,
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
        mock_logger.assert_not_called()
        mock_format.assert_not_called()

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
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_exception(
        self, mock_getaddrinfo, mock_format, mock_logger, mock_request, mock_create_message
    ):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        mock_request.side_effect = Exception("test_exception")

        send_msteams_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            allow_redirects=False,
            timeout=60,
        )
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_not_ok(
        self, mock_getaddrinfo, mock_format, mock_logger, mock_request, mock_create_message
    ):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 400
        mock_request.return_value = response

        send_msteams_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            allow_redirects=False,
            timeout=60,
        )
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_success(
        self, mock_getaddrinfo, mock_format, mock_logger, mock_request, mock_create_message
    ):
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
            allow_redirects=False,
            timeout=60,
        )
        mock_logger.assert_not_called()
        mock_format.assert_not_called()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_workflow_webhook(
        self, mock_getaddrinfo, mock_format, mock_logger, mock_request, mock_create_message
    ):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        send_msteams_notification(WORKFLOW_WEBHOOK, "msteams_observation.tpl")

        # The Adaptive Card variant is rendered instead of the MessageCard one ...
        mock_create_message.assert_called_with("msteams_observation_workflow.tpl")
        # ... and the request carries the JSON content type Power Automate needs.
        mock_request.assert_called_with(
            method="POST",
            url=WORKFLOW_WEBHOOK,
            data="test_message",
            allow_redirects=False,
            timeout=60,
            headers={"Content-Type": "application/json"},
        )
        mock_logger.assert_not_called()
        mock_format.assert_not_called()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_msteams_notification_connector_webhook_unchanged(
        self, mock_getaddrinfo, mock_request, mock_create_message
    ):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        send_msteams_notification("https://example.webhook.office.com/webhookb2/abc", "msteams_observation.tpl")

        # Legacy connector keeps the MessageCard template and sends no extra header.
        mock_create_message.assert_called_with("msteams_observation.tpl")
        mock_request.assert_called_with(
            method="POST",
            url="https://example.webhook.office.com/webhookb2/abc",
            data="test_message",
            allow_redirects=False,
            timeout=60,
        )

    # --- _is_msteams_workflow_webhook / _get_msteams_workflow_template ---

    def test_is_msteams_workflow_webhook_true_by_path(self):
        # The "/workflows/" path is present in both the current and legacy URL forms.
        self.assertTrue(_is_msteams_workflow_webhook(WORKFLOW_WEBHOOK))
        self.assertTrue(
            _is_msteams_workflow_webhook(
                "https://prod-12.westeurope.logic.azure.com:443/workflows/abc/triggers/manual/paths/invoke"
            )
        )
        self.assertTrue(_is_msteams_workflow_webhook("https://example.org/foo/workflows/bar"))

    def test_is_msteams_workflow_webhook_true_by_host(self):
        # Host-suffix fallback (documented trigger hosts) even without the workflow path.
        self.assertTrue(_is_msteams_workflow_webhook("https://env.environment.api.powerplatform.com/anything"))
        self.assertTrue(_is_msteams_workflow_webhook("https://prod-00.eastus.logic.azure.com/health"))

    def test_is_msteams_workflow_webhook_false(self):
        self.assertFalse(_is_msteams_workflow_webhook("https://contoso.webhook.office.com/webhookb2/abc"))
        self.assertFalse(_is_msteams_workflow_webhook("https://hooks.example.org/webhook"))
        # azure-apim.net is the APIM OAuth-consent domain, not a webhook trigger host.
        self.assertFalse(_is_msteams_workflow_webhook("https://global.consent.azure-apim.net/redirect/apim/x"))
        self.assertFalse(_is_msteams_workflow_webhook(""))

    def test_get_msteams_workflow_template(self):
        self.assertEqual("msteams_observation_workflow.tpl", _get_msteams_workflow_template("msteams_observation.tpl"))
        self.assertEqual("test_template_workflow", _get_msteams_workflow_template("test_template"))

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
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_slack_notification_exception(
        self, mock_getaddrinfo, mock_format, mock_logger, mock_request, mock_create_message
    ):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        mock_request.side_effect = Exception("test_exception")

        send_slack_notification("https://hooks.example.org/webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(
            method="POST",
            url="https://hooks.example.org/webhook",
            data="test_message",
            allow_redirects=False,
            timeout=60,
        )
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_slack_notification_not_ok(
        self, mock_getaddrinfo, mock_format, mock_logger, mock_request, mock_create_message
    ):
        mock_getaddrinfo.return_value = [(2, 1, 6, "", ("1.2.3.4", 443))]
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 400
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
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    @patch("application.notifications.services.send_notifications_base.socket.getaddrinfo")
    def test_send_slack_notification_success(
        self, mock_getaddrinfo, mock_format, mock_logger, mock_request, mock_create_message
    ):
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
        mock_logger.assert_not_called()
        mock_format.assert_not_called()

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

    # --- Adaptive Card (Workflows) templates ---

    def _assert_adaptive_card_envelope(self, message):
        parsed = json.loads(message)
        self.assertEqual("message", parsed["type"])
        attachment = parsed["attachments"][0]
        self.assertEqual("application/vnd.microsoft.card.adaptive", attachment["contentType"])
        self.assertEqual("AdaptiveCard", attachment["content"]["type"])
        return parsed

    def test_create_notification_message_security_gate_workflow(self):
        message = _create_notification_message(
            "msteams_product_security_gate_workflow.tpl",
            product=self.product_1,
            security_gate_status="Failed",
            product_url="product_url",
            severity_stats=[
                {"label": "Critical", "count": 3, "threshold": 0},
                {"label": "High", "count": 1, "threshold": 2},
                {"label": "Medium", "count": 5, "threshold": 10},
                {"label": "Low", "count": 0, "threshold": 0},
                {"label": "Unknown", "count": 0, "threshold": 0},
            ],
        )

        content = self._assert_adaptive_card_envelope(message)["attachments"][0]["content"]
        header = content["body"][0]
        self.assertEqual("attention", header["style"])
        self.assertIn("failed", header["items"][0]["text"].lower())
        facts = {fact["title"]: fact["value"] for fact in content["body"][1]["facts"]}
        self.assertEqual(["Critical", "High", "Medium", "Low", "Unknown"], list(facts.keys()))
        self.assertEqual("3 / allowed 0", facts["Critical"])
        self.assertEqual("1 / allowed 2", facts["High"])
        self.assertEqual("5 / allowed 10", facts["Medium"])
        self.assertEqual("0 / allowed 0", facts["Unknown"])
        self.assertEqual("product_url", content["actions"][0]["url"])

    def test_create_notification_message_security_gate_workflow_disabled(self):
        # No counts/thresholds (gate disabled) -> "n/a" and no "allowed" suffix.
        message = _create_notification_message(
            "msteams_product_security_gate_workflow.tpl",
            product=self.product_1,
            security_gate_status="None",
            product_url="product_url",
            severity_stats=[
                {"label": "Critical", "count": None, "threshold": None},
                {"label": "High", "count": None, "threshold": None},
                {"label": "Medium", "count": None, "threshold": None},
                {"label": "Low", "count": None, "threshold": None},
                {"label": "Unknown", "count": None, "threshold": None},
            ],
        )

        content = self._assert_adaptive_card_envelope(message)["attachments"][0]["content"]
        self.assertEqual("default", content["body"][0]["style"])
        facts = {fact["title"]: fact["value"] for fact in content["body"][1]["facts"]}
        self.assertEqual("n/a", facts["Critical"])
        self.assertEqual("n/a", facts["Unknown"])

    def test_create_notification_message_observation_workflow(self):
        message = _create_notification_message(
            "msteams_observation_workflow.tpl",
            observation=self.observation_1,
            observation_url="observation_url",
            first_line="New observation",
        )

        parsed = self._assert_adaptive_card_envelope(message)
        content = parsed["attachments"][0]["content"]
        fact_titles = [fact["title"] for fact in content["body"][1]["facts"]]
        self.assertEqual(["Product:", "Severity:", "Status:", "Priority:"], fact_titles)
        self.assertEqual("observation_url", content["actions"][0]["url"])

    def test_create_notification_message_exception_workflow(self):
        exception = Exception("test_exception")
        message = _create_notification_message(
            "msteams_exception_workflow.tpl",
            exception_class=get_classname(exception),
            exception_message=str(exception),
            date_time=datetime(2022, 12, 31, 23, 59, 59),
            exception_trace="",
        )

        # Renders to valid JSON even with the date filter inside a string value.
        self._assert_adaptive_card_envelope(message)

    def test_create_notification_message_observation_workflow_backslash_breakout(self):
        # The escapejs hardening must hold for the Adaptive Card variant too.
        self.observation_1.title = 'evil\\", "extra": "x'
        message = _create_notification_message(
            "msteams_observation_workflow.tpl",
            observation=self.observation_1,
            observation_url="observation_url",
            first_line='New notification for observation "evil\\", "extra": "x"',
        )
        # Parsing must not surface an injected "extra" key in the envelope.
        parsed = json.loads(message)
        self.assertEqual({"type", "attachments"}, set(parsed.keys()))

    # --- manual live test ---

    # Skipped in CI: it makes a real HTTP request and posts a card to a channel.
    # To run it, paste a real Microsoft Teams "Workflows" (Power Automate) webhook
    # URL into ``live_webhook`` below and remove the @skip decorator. It exercises
    # detection -> Adaptive Card render -> POST and asserts Power Automate accepts
    # the request (HTTP 2xx). A 400 "InvalidRequestContent" instead means the body
    # was not sent as JSON (the bug this change fixes).
    @unittest.skip("manual live test — set a real Workflows webhook URL and remove this skip to run")
    def test_live_workflow_webhook_accepts_adaptive_card(self):
        live_webhook = (
            "https://<env>.environment.api.powerplatform.com"
            "/powerautomate/automations/direct/workflows/<workflow-id>"
            "/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=<signature>"
        )
        self.assertTrue(_is_msteams_workflow_webhook(live_webhook))
        template = _get_msteams_workflow_template("msteams_product_security_gate.tpl")
        message = _create_notification_message(
            template,
            product=SimpleNamespace(name="SecObserve live test"),
            security_gate_status="Passed",
            product_url="https://github.com/SecObserve/SecObserve",
        )
        response = requests.request(
            method="POST",
            url=live_webhook,
            data=message,
            allow_redirects=False,
            timeout=60,
            headers={"Content-Type": "application/json"},
        )
        self.assertIn(response.status_code, (200, 202))
