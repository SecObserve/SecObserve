from json import dumps
from unittest.mock import MagicMock, patch

from application.licenses.models import License
from application.licenses.services.license import import_licenses
from unittests.base_test_case import BaseTestCase


def _response(licenses: list[dict]) -> MagicMock:
    response = MagicMock()
    response.content = dumps({"licenses": licenses}).encode()
    return response


def _spdx_license(spdx_id: str, name: str) -> dict:
    return {
        "licenseId": spdx_id,
        "name": name,
        "reference": f"https://spdx.org/licenses/{spdx_id}.html",
        "isOsiApproved": True,
        "isDeprecatedLicenseId": False,
    }


class TestImportLicenses(BaseTestCase):
    @patch("application.licenses.services.license.requests.get")
    def test_import_licenses_create(self, mock_get):
        mock_get.return_value = _response([_spdx_license("Test-License-1", "Test License 1")])

        result = import_licenses()

        self.assertEqual("Licenses updated: 0, licenses created: 1", result)
        license = License.objects.get(spdx_id="Test-License-1")
        self.assertEqual("Test License 1", license.name)
        self.assertEqual("https://spdx.org/licenses/Test-License-1.html", license.reference)
        self.assertTrue(license.is_osi_approved)
        self.assertFalse(license.is_deprecated)

    @patch("application.licenses.services.license.requests.get")
    def test_import_licenses_update(self, mock_get):
        License.objects.create(
            spdx_id="Test-License-1",
            name="Old name",
            reference="https://spdx.org/licenses/Test-License-1.html",
            is_osi_approved=True,
            is_deprecated=False,
        )
        mock_get.return_value = _response([_spdx_license("Test-License-1", "Test License 1")])

        result = import_licenses()

        self.assertEqual("Licenses updated: 1, licenses created: 0", result)
        self.assertEqual("Test License 1", License.objects.get(spdx_id="Test-License-1").name)

    @patch("application.licenses.services.license.requests.get")
    def test_import_licenses_unchanged(self, mock_get):
        License.objects.create(
            spdx_id="Test-License-1",
            name="Test License 1",
            reference="https://spdx.org/licenses/Test-License-1.html",
            is_osi_approved=True,
            is_deprecated=False,
        )
        mock_get.return_value = _response([_spdx_license("Test-License-1", "Test License 1")])

        result = import_licenses()

        self.assertEqual("Licenses updated: 0, licenses created: 0", result)
