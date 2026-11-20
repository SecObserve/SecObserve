from unittest.mock import patch

from application.background_tasks.periodic_tasks.license_tasks import (
    task_spdx_license_import,
)
from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase


class TestLicenseTasks(BaseTestCase):
    # ---------------------------------------------------------------
    # task_spdx_license_import
    # ---------------------------------------------------------------

    @patch("application.background_tasks.periodic_tasks.license_tasks.import_choosealicense")
    @patch("application.background_tasks.periodic_tasks.license_tasks.import_scancode_licensedb")
    @patch("application.background_tasks.periodic_tasks.license_tasks.import_licenses")
    @patch("application.background_tasks.periodic_tasks.license_tasks.Settings.load")
    def test_task_spdx_license_import_enabled(
        self,
        mock_settings_load,
        mock_import_licenses,
        mock_import_scancode_licensedb,
        mock_import_choosealicense,
    ):
        # Setup
        mock_import_licenses.return_value = "Licenses imported"
        mock_import_scancode_licensedb.return_value = "ScanCode imported"
        mock_import_choosealicense.return_value = "choosealicense.com imported"
        settings = Settings()
        settings.feature_license_management = True
        mock_settings_load.return_value = settings

        # Execute
        task_spdx_license_import()

        # Assert
        self.assertEqual(mock_settings_load.call_count, 2)
        mock_import_licenses.assert_called_once()
        mock_import_scancode_licensedb.assert_called_once()
        mock_import_choosealicense.assert_called_once()

    @patch("application.background_tasks.periodic_tasks.license_tasks.import_choosealicense")
    @patch("application.background_tasks.periodic_tasks.license_tasks.import_scancode_licensedb")
    @patch("application.background_tasks.periodic_tasks.license_tasks.import_licenses")
    @patch("application.background_tasks.periodic_tasks.license_tasks.Settings.load")
    def test_task_spdx_license_import_disabled(
        self,
        mock_settings_load,
        mock_import_licenses,
        mock_import_scancode_licensedb,
        mock_import_choosealicense,
    ):
        # Setup
        mock_import_licenses.return_value = "Licenses imported"
        mock_import_scancode_licensedb.return_value = "ScanCode imported"
        mock_import_choosealicense.return_value = "choosealicense.com imported"
        settings = Settings()
        settings.feature_license_management = False
        mock_settings_load.return_value = settings

        # Execute
        task_spdx_license_import()

        # Assert
        self.assertEqual(mock_settings_load.call_count, 2)
        mock_import_licenses.assert_not_called()
        mock_import_scancode_licensedb.assert_not_called()
        mock_import_choosealicense.assert_not_called()
