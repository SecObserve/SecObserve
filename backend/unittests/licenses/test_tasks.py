from unittest.mock import patch

from application.licenses.tasks import task_import_license_details
from unittests.base_test_case import BaseTestCase


class TestTasks(BaseTestCase):
    @patch("application.licenses.tasks.handle_task_exception")
    @patch("application.licenses.tasks.import_choosealicense")
    @patch("application.licenses.tasks.import_scancode_licensedb")
    def test_task_import_license_details(self, mock_import_scancode, mock_import_choosealicense, mock_handle_exception):
        task_import_license_details.call_local()

        mock_import_scancode.assert_called_once_with()
        mock_import_choosealicense.assert_called_once_with()
        mock_handle_exception.assert_not_called()

    @patch("application.licenses.tasks.handle_task_exception")
    @patch("application.licenses.tasks.import_choosealicense")
    @patch("application.licenses.tasks.import_scancode_licensedb")
    def test_task_import_license_details_exception(
        self, mock_import_scancode, mock_import_choosealicense, mock_handle_exception
    ):
        exception = RuntimeError("Download failed")
        mock_import_scancode.side_effect = exception

        with self.assertRaises(RuntimeError):
            task_import_license_details.call_local()

        mock_import_choosealicense.assert_not_called()
        mock_handle_exception.assert_called_once_with(exception)
