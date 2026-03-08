from datetime import datetime, timedelta
from unittest.mock import ANY, call, patch

from requests import Response

from application.commons.models import Settings
from application.commons.services.functions import get_classname
from application.notifications.models import Notification
from application.notifications.services.send_notifications_base import (
    _create_notification_message,
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
    def test_send_msteams_notification_success(
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
    def test_send_msteams_notification_empty_message(self, mock_request, mock_create_message):
        mock_create_message.return_value = None

        send_msteams_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_not_called()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_send_msteams_notification_exception(self, mock_format, mock_logger, mock_request, mock_create_message):
        mock_create_message.return_value = "test_message"
        mock_request.side_effect = Exception("test_exception")

        send_msteams_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(method="POST", url="test_webhook", data="test_message", timeout=60)
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_send_msteams_notification_not_ok(self, mock_format, mock_logger, mock_request, mock_create_message):
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 400
        mock_request.return_value = response

        send_msteams_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(method="POST", url="test_webhook", data="test_message", timeout=60)
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_send_msteams_notification_success(self, mock_format, mock_logger, mock_request, mock_create_message):
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        send_msteams_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(method="POST", url="test_webhook", data="test_message", timeout=60)
        mock_logger.assert_not_called()
        mock_format.assert_not_called()

    # --- send_slack_notification ---

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    def test_send_slack_notification_empty_message(self, mock_request, mock_create_message):
        mock_create_message.return_value = None

        send_slack_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_not_called()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_send_slack_notification_exception(self, mock_format, mock_logger, mock_request, mock_create_message):
        mock_create_message.return_value = "test_message"
        mock_request.side_effect = Exception("test_exception")

        send_slack_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(method="POST", url="test_webhook", data="test_message", timeout=60)
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_send_slack_notification_not_ok(self, mock_format, mock_logger, mock_request, mock_create_message):
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 400
        mock_request.return_value = response

        send_slack_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(method="POST", url="test_webhook", data="test_message", timeout=60)
        mock_logger.assert_called_once()
        mock_format.assert_called_once()

    @patch("application.notifications.services.send_notifications_base._create_notification_message")
    @patch("application.notifications.services.send_notifications_base.requests.request")
    @patch("application.notifications.services.send_notifications_base.logger.error")
    @patch("application.notifications.services.send_notifications_base.format_log_message")
    def test_send_slack_notification_success(self, mock_format, mock_logger, mock_request, mock_create_message):
        mock_create_message.return_value = "test_message"
        response = Response()
        response.status_code = 200
        mock_request.return_value = response

        send_slack_notification("test_webhook", "test_template")

        mock_create_message.assert_called_with("test_template")
        mock_request.assert_called_with(method="POST", url="test_webhook", data="test_message", timeout=60)
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
            "value": "2022-12-31 23:59:59.000000"
        }, {
            "name": "Trace:",
            "value": ""
        }],
        "markdown": true
    }],
}
"""
        self.assertEqual(expected_message, message)
