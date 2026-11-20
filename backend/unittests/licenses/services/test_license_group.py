from json import dumps
from unittest.mock import MagicMock, patch

from application.licenses.models import License, License_Group
from application.licenses.services.license_group import import_scancode_licensedb
from unittests.base_test_case import BaseTestCase


class TestImportScancodeLicensedb(BaseTestCase):
    @patch("application.licenses.services.license_group.enrich_licenses_from_scancode")
    @patch("application.licenses.services.license_group.requests.get")
    def test_import_scancode_licensedb(self, mock_get, mock_enrich):
        index = [
            {
                "license_key": "test-group-1",
                "category": "Test Category",
                "spdx_license_key": "Test-Group-1",
                "other_spdx_license_keys": [],
            }
        ]
        response = MagicMock()
        response.content = dumps(index).encode()
        mock_get.return_value = response
        mock_enrich.return_value = "ScanCode LicenseDB: licenses enriched: 1, cleared: 0, failed: 0"
        spdx_license = License.objects.create(spdx_id="Test-Group-1", name="Test Group 1")

        result = import_scancode_licensedb()

        self.assertEqual(
            "License Groups from ScanCode LicenseDB imported\n"
            + "ScanCode LicenseDB: licenses enriched: 1, cleared: 0, failed: 0",
            result,
        )
        mock_enrich.assert_called_once_with(index)
        license_group = License_Group.objects.get(name="Test Category (ScanCode LicenseDB)")
        self.assertEqual([spdx_license], list(license_group.licenses.all()))
