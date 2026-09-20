from unittest.mock import patch

from application.access_control.signals import (
    signal_user_logged_in,
    signal_user_logged_out,
    signal_user_login_failed,
)
from unittests.base_test_case import BaseTestCase


class TestSignals(BaseTestCase):
    @patch("application.access_control.signals.logger.info")
    @patch("application.access_control.signals.format_log_message")
    def test_signal_user_logged_in(self, mock_format, mock_logging):
        signal_user_logged_in(None, user=self.user_internal)

        mock_format.assert_called_with(message="User logged in", username="user_internal@example.com")
        mock_logging.assert_called_once()

    @patch("application.access_control.signals.logger.info")
    @patch("application.access_control.signals.format_log_message")
    def test_signal_user_logged_out(self, mock_format, mock_logging):
        signal_user_logged_out(None, user=self.user_internal)

        mock_format.assert_called_with(message="User logged out", username="user_internal@example.com")
        mock_logging.assert_called_once()

    @patch("application.access_control.signals.logger.info")
    @patch("application.access_control.signals.format_log_message")
    @patch("application.access_control.signals.get_current_username")
    def test_signal_user_login_failed(self, mock_username, mock_format, mock_logging):
        mock_username.return_value = "user_admin@example.com"
        credentials = {"user": "test_user", "password": "*****"}
        signal_user_login_failed(None, credentials=credentials)

        mock_format.assert_called_with(
            message="User login failed: ", data=credentials, username="user_admin@example.com"
        )
        mock_logging.assert_called_once()
