from datetime import UTC, datetime
from unittest.mock import patch

from application.background_tasks.periodic_tasks.license_tasks import (
    task_spdx_license_import,
)
from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase

MODULE = "application.background_tasks.periodic_tasks.license_tasks"
SUNDAY = datetime(2026, 11, 22, 1, 30, tzinfo=UTC)
MONDAY = datetime(2026, 11, 23, 1, 30, tzinfo=UTC)


class TestLicenseTasks(BaseTestCase):
    # ---------------------------------------------------------------
    # task_spdx_license_import
    # ---------------------------------------------------------------

    @patch(f"{MODULE}.timezone.now", return_value=SUNDAY)
    @patch(f"{MODULE}.import_choosealicense", return_value="choosealicense.com imported")
    @patch(f"{MODULE}.import_scancode_licensedb", return_value="ScanCode imported")
    @patch(f"{MODULE}.import_licenses", return_value="Licenses imported")
    @patch(f"{MODULE}.Settings.load")
    def test_task_spdx_license_import_sunday(
        self, mock_settings_load, mock_import_licenses, mock_import_scancode, mock_import_choosealicense, mock_now
    ):
        mock_settings_load.return_value = Settings(feature_license_management=True)

        task_spdx_license_import()

        mock_import_licenses.assert_called_once_with()
        mock_import_scancode.assert_called_once_with(enrich_licenses=True)
        mock_import_choosealicense.assert_called_once_with()

    @patch(f"{MODULE}.timezone.now", return_value=MONDAY)
    @patch(f"{MODULE}.import_choosealicense", return_value="choosealicense.com imported")
    @patch(f"{MODULE}.import_scancode_licensedb", return_value="ScanCode imported")
    @patch(f"{MODULE}.import_licenses", return_value="Licenses imported")
    @patch(f"{MODULE}.Settings.load")
    def test_task_spdx_license_import_weekday(
        self, mock_settings_load, mock_import_licenses, mock_import_scancode, mock_import_choosealicense, mock_now
    ):
        mock_settings_load.return_value = Settings(feature_license_management=True)

        task_spdx_license_import()

        mock_import_licenses.assert_called_once_with()
        mock_import_scancode.assert_called_once_with(enrich_licenses=False)
        mock_import_choosealicense.assert_not_called()

    @patch(f"{MODULE}.import_choosealicense", return_value="choosealicense.com imported")
    @patch(f"{MODULE}.import_scancode_licensedb", return_value="ScanCode imported")
    @patch(f"{MODULE}.import_licenses", return_value="Licenses imported")
    @patch(f"{MODULE}.Settings.load")
    def test_task_spdx_license_import_disabled(
        self, mock_settings_load, mock_import_licenses, mock_import_scancode, mock_import_choosealicense
    ):
        mock_settings_load.return_value = Settings(feature_license_management=False)

        task_spdx_license_import()

        mock_import_licenses.assert_not_called()
        mock_import_scancode.assert_not_called()
        mock_import_choosealicense.assert_not_called()
