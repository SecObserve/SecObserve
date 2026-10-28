from unittest.mock import MagicMock, patch

import requests
from jira.exceptions import JIRAError

from application.commons.services.connection_error import (
    get_connection_error_message,
    raise_for_status,
)
from unittests.base_test_case import BaseTestCase


class TestGetConnectionErrorMessage(BaseTestCase):
    @patch("application.commons.services.connection_error.logger.warning")
    def test_connection_error(self, mock_warning):
        exception = requests.exceptions.ConnectionError("[Errno 111] Connection refused")

        message = get_connection_error_message("Cannot access API", exception)

        self.assertEqual("Cannot access API, see backend log for details", message)
        self.assertIn("[Errno 111] Connection refused", mock_warning.call_args.args[0])

    @patch("application.commons.services.connection_error.logger.warning")
    def test_http_error(self, mock_warning):
        response = MagicMock()
        response.status_code = 503
        exception = requests.exceptions.HTTPError("503 Server Error", response=response)

        message = get_connection_error_message("Cannot access API", exception)

        self.assertEqual("Cannot access API: HTTP status 503", message)
        mock_warning.assert_called_once()

    @patch("application.commons.services.connection_error.logger.warning")
    def test_jira_error(self, mock_warning):
        exception = JIRAError(status_code=404, text="response text")

        message = get_connection_error_message("Cannot access API", exception)

        self.assertEqual("Cannot access API: HTTP status 404", message)
        mock_warning.assert_called_once()


class TestRaiseForStatus(BaseTestCase):
    def test_redirect(self):
        response = requests.Response()
        response.status_code = 302
        response.url = "https://example.com/api"

        with self.assertRaises(requests.exceptions.HTTPError) as e:
            raise_for_status(response)

        self.assertEqual("302 Redirect for url: https://example.com/api", str(e.exception))
        self.assertEqual(response, e.exception.response)

    def test_client_error(self):
        response = requests.Response()
        response.status_code = 404
        response.reason = "Not Found"
        response.url = "https://example.com/api"

        with self.assertRaises(requests.exceptions.HTTPError) as e:
            raise_for_status(response)

        self.assertEqual("404 Client Error: Not Found for url: https://example.com/api", str(e.exception))

    def test_success(self):
        response = requests.Response()
        response.status_code = 200

        raise_for_status(response)
