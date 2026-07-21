from unittest.mock import patch

from django.db.models.deletion import ProtectedError, RestrictedError
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied,
    ValidationError,
)
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from application.notifications.api.exception_handler import custom_exception_handler
from unittests.base_test_case import BaseTestCase


class TestExceptionHandler(BaseTestCase):
    def test_protected_error_formatted(self):
        exception = ProtectedError(
            "Cannot delete some instances of model 'Product' because they are referenced through protected foreign keys: 'Service.product_group', 'Observation.product'.",
            None,
        )
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_409_CONFLICT, response.status_code)
        data = {"message": "Cannot delete Product because it still has Services, Observations."}
        self.assertEqual(data, response.data)

    def test_protected_error_raw(self):
        exception = ProtectedError(
            "Cannot delete some instances of model Product because they are referenced through protected foreign keys: Service.product_group, 'Observation.product'.",
            None,
        )
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_409_CONFLICT, response.status_code)
        data = {
            "message": "Cannot delete some instances of model Product because they are referenced through protected foreign keys: Service.product_group, 'Observation.product'."
        }
        self.assertEqual(data, response.data)

    def test_restricted_error_formatted(self):
        exception = RestrictedError(
            "Cannot delete some instances of model 'Service' because they are referenced through restricted "
            "foreign keys: 'Observation.origin_service'.",
            None,
        )
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_409_CONFLICT, response.status_code)
        data = {"message": "Cannot delete Service because it still has Observations."}
        self.assertEqual(data, response.data)

    @patch("application.notifications.api.exception_handler.logger.error")
    @patch("application.notifications.api.exception_handler.format_log_message")
    @patch("application.notifications.api.exception_handler.send_exception_notification")
    @patch("application.notifications.api.exception_handler.get_current_username")
    def test_no_response(self, mock_username, mock_notify, mock_format, mock_logging):
        mock_username.return_value = "user_internal@example.com"

        exception = Exception("Something unexpected has happened")
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        data = {"message": "Internal server error, check logs for details"}
        self.assertEqual(data, response.data)
        mock_notify.assert_called_with(exception)
        mock_format.assert_called_with(response=response, exception=exception, username="user_internal@example.com")
        self.assertEqual(mock_logging.call_count, 2)

    @patch("application.notifications.api.exception_handler.logger.warning")
    @patch("application.notifications.api.exception_handler.format_log_message")
    @patch("application.notifications.api.exception_handler.get_current_username")
    def test_authentication_failed(self, mock_username, mock_format, mock_logging):
        mock_username.return_value = "user_internal@example.com"

        exception = AuthenticationFailed("Authentication has failed")
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_401_UNAUTHORIZED, response.status_code)
        data = {"message": "Authentication has failed"}
        self.assertEqual(data, response.data)
        mock_format.assert_called_with(response=response, exception=exception, username="user_internal@example.com")
        mock_logging.assert_called_once()

    @patch("application.notifications.api.exception_handler.logger.warning")
    @patch("application.notifications.api.exception_handler.format_log_message")
    @patch("application.notifications.api.exception_handler.get_current_username")
    def test_permission_denied(self, mock_username, mock_format, mock_logging):
        mock_username.return_value = "user_internal@example.com"

        exception = PermissionDenied("Not authentication")
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        data = {"message": "Not authentication"}
        self.assertEqual(data, response.data)
        mock_format.assert_called_with(response=response, exception=exception, username="user_internal@example.com")
        mock_logging.assert_called_once()

    @patch("application.notifications.api.exception_handler.logger.warning")
    @patch("application.notifications.api.exception_handler.format_log_message")
    def test_other_user_error(self, mock_format, mock_logging):
        exception = ValidationError("Not validated")
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)
        data = {"message": "Not validated"}
        self.assertEqual(data, response.data)
        mock_format.assert_not_called()
        mock_logging.assert_not_called()

    @patch("application.notifications.api.exception_handler.logger.error")
    @patch("application.notifications.api.exception_handler.format_log_message")
    @patch("application.notifications.api.exception_handler.send_exception_notification")
    @patch("application.notifications.api.exception_handler.get_current_username")
    def test_server_error(self, mock_username, mock_notification, mock_format, mock_logging):
        mock_username.return_value = "user_internal@example.com"

        exception = APIException(Exception("Not authentication"))
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        data = {"message": "Internal server error, check logs for details"}
        self.assertEqual(data, response.data)
        mock_format.assert_called_with(response=response, exception=exception, username="user_internal@example.com")
        self.assertEqual(mock_logging.call_count, 2)
        mock_notification.assert_called_with(exception)
