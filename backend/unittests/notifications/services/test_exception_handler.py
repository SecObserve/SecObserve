import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
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
from rest_framework.test import APIClient

from application.access_control.models import User
from application.notifications.api.exception_handler import custom_exception_handler
from application.vex.models import VEX_Document
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

    @patch("application.notifications.api.exception_handler.set_rollback")
    @patch("application.notifications.api.exception_handler.logger.error")
    @patch("application.notifications.api.exception_handler.format_log_message")
    @patch("application.notifications.api.exception_handler.send_exception_notification")
    @patch("application.notifications.api.exception_handler.get_current_username")
    def test_no_response(self, mock_username, mock_notify, mock_format, mock_logging, mock_rollback):
        mock_username.return_value = "user_internal@example.com"

        exception = Exception("Something unexpected has happened")
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        data = {"message": "Internal server error, check logs for details"}
        self.assertEqual(data, response.data)
        mock_notify.assert_called_with(exception)
        mock_format.assert_called_with(response=response, exception=exception, username="user_internal@example.com")
        self.assertEqual(mock_logging.call_count, 2)
        mock_rollback.assert_called_once()

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

    @patch("application.notifications.api.exception_handler.set_rollback")
    @patch("application.notifications.api.exception_handler.logger.error")
    @patch("application.notifications.api.exception_handler.format_log_message")
    @patch("application.notifications.api.exception_handler.send_exception_notification")
    @patch("application.notifications.api.exception_handler.get_current_username")
    def test_server_error(self, mock_username, mock_notification, mock_format, mock_logging, mock_rollback):
        mock_username.return_value = "user_internal@example.com"

        exception = APIException(Exception("Not authentication"))
        response = custom_exception_handler(exception, None)

        self.assertEqual(HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        data = {"message": "Internal server error, check logs for details"}
        self.assertEqual(data, response.data)
        mock_format.assert_called_with(response=response, exception=exception, username="user_internal@example.com")
        self.assertEqual(mock_logging.call_count, 2)
        mock_notification.assert_called_with(exception)
        mock_rollback.assert_called_once()


AUTHENTICATE = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
PROCESS_STATEMENTS = "application.vex.services.cyclonedx_parser._process_vex_statements"
NOTIFY = "application.notifications.api.exception_handler.send_exception_notification"


class TestExceptionHandlerTransaction(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="superuser@example.com", is_superuser=True)
        self.documents_when_notified = []

    def _import_vex(self):
        document = {
            "bomFormat": "CycloneDX",
            "serialNumber": "urn:uuid:6b0a3a4e-2f0d-4c47-9d3e-6c0f3c2b8a11",
            "version": 1,
            "metadata": {"authors": [{"name": "author"}]},
        }
        file = SimpleUploadedFile("vex.json", json.dumps(document).encode(), content_type="application/json")
        return APIClient(raise_request_exception=False).post("/api/vex/vex_import/", {"file": file}, format="multipart")

    def _count_documents(self, exception):
        self.documents_when_notified.append(VEX_Document.objects.count())

    @patch(NOTIFY)
    @patch(PROCESS_STATEMENTS)
    @patch(AUTHENTICATE)
    def test_unexpected_exception_rolls_back(self, mock_authenticate, mock_process, mock_notification):
        mock_authenticate.return_value = self.user, None
        mock_process.side_effect = RuntimeError("unexpected")
        mock_notification.side_effect = self._count_documents

        response = self._import_vex()

        self.assertEqual(HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual({"message": "Internal server error, check logs for details"}, response.data)
        self.assertEqual(0, VEX_Document.objects.count())
        self.assertEqual([0], self.documents_when_notified)

    @patch(NOTIFY)
    @patch(PROCESS_STATEMENTS)
    @patch(AUTHENTICATE)
    def test_database_error_is_notified_after_rollback(self, mock_authenticate, mock_process, mock_notification):
        def create_duplicate(data, document):
            VEX_Document.objects.create(
                type=document.type,
                document_id=document.document_id,
                version=document.version,
                current_release_date=document.current_release_date,
                initial_release_date=document.initial_release_date,
                author=document.author,
            )

        mock_authenticate.return_value = self.user, None
        mock_process.side_effect = create_duplicate
        mock_notification.side_effect = self._count_documents

        response = self._import_vex()

        self.assertEqual(HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual({"message": "Internal server error, check logs for details"}, response.data)
        self.assertEqual(0, VEX_Document.objects.count())
        self.assertEqual([0], self.documents_when_notified)
