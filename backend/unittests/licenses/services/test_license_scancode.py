from unittest.mock import MagicMock, patch

import requests

from application.licenses.models import License
from application.licenses.services.license_scancode import (
    enrich_licenses_from_scancode,
)
from unittests.base_test_case import BaseTestCase

DETAILS = {
    "test-1": {
        "key": "test-1",
        "owner": "Owner 1",
        "homepage_url": "https://example.com/home_1",
        "osi_url": "https://example.com/osi_1",
        "faq_url": "https://example.com/faq_1",
        "text_urls": ["https://example.com/text_1"],
    },
    "test-2": {
        "key": "test-2",
        "owner": "Owner 2",
    },
}


def _entry(license_key: str, spdx_license_key: str | None, other_spdx_license_keys: list | None = None) -> dict:
    return {
        "license_key": license_key,
        "category": "Permissive",
        "spdx_license_key": spdx_license_key,
        "other_spdx_license_keys": other_spdx_license_keys or [],
        "json": f"{license_key}.json",
    }


def _session_get(url: str, timeout: int) -> MagicMock:  # pylint: disable=unused-argument
    license_key = url.rsplit("/", 1)[-1].removesuffix(".json")
    if license_key not in DETAILS:
        raise requests.ConnectionError("connection failed")
    response = MagicMock()
    response.json.return_value = DETAILS[license_key]
    return response


class TestEnrichLicensesFromScancode(BaseTestCase):
    def setUp(self):
        super().setUp()
        # The patch is started here instead of decorating the class, because other test classes
        # change patch.TEST_PREFIX, which would make a class decorator patch setUpClass as well.
        patcher = patch("application.licenses.services.license_scancode.requests.Session")
        self.addCleanup(patcher.stop)
        self.session = patcher.start().return_value.__enter__.return_value
        self.session.get.side_effect = _session_get

        self.license_1 = License.objects.create(spdx_id="Test-ScanCode-1", name="Test ScanCode 1")
        self.license_2 = License.objects.create(spdx_id="Test-ScanCode-2", name="Test ScanCode 2")

    def test_primary_match(self):
        result = enrich_licenses_from_scancode([_entry("test-1", "Test-ScanCode-1")])

        self.assertIn("licenses enriched: 1, cleared: 0, failed: 0", result)
        self.session.get.assert_called_once_with("https://scancode-licensedb.aboutcode.org/test-1.json", timeout=60)
        self.license_1.refresh_from_db()
        self.assertEqual("test-1", self.license_1.scancode_key)
        self.assertEqual("Permissive", self.license_1.scancode_category)
        self.assertEqual("Owner 1", self.license_1.scancode_owner)
        self.assertEqual("https://example.com/home_1", self.license_1.scancode_homepage_url)
        self.assertEqual("https://example.com/osi_1", self.license_1.scancode_osi_url)
        self.assertEqual("https://example.com/faq_1", self.license_1.scancode_faq_url)
        self.assertEqual(["https://example.com/text_1"], self.license_1.scancode_text_urls)
        self.license_2.refresh_from_db()
        self.assertEqual("", self.license_2.scancode_key)

    def test_unchanged(self):
        index = [_entry("test-1", "Test-ScanCode-1")]
        enrich_licenses_from_scancode(index)

        result = enrich_licenses_from_scancode(index)

        self.assertIn("licenses enriched: 0, cleared: 0, failed: 0", result)

    def test_missing_detail_fields(self):
        enrich_licenses_from_scancode([_entry("test-2", "Test-ScanCode-2")])

        self.license_2.refresh_from_db()
        self.assertEqual("test-2", self.license_2.scancode_key)
        self.assertEqual("Owner 2", self.license_2.scancode_owner)
        self.assertEqual("", self.license_2.scancode_homepage_url)
        self.assertEqual([], self.license_2.scancode_text_urls)

    def test_other_spdx_license_key_match(self):
        result = enrich_licenses_from_scancode([_entry("test-1", "Test-ScanCode-1", ["Test-ScanCode-2"])])

        self.assertIn("licenses enriched: 2, cleared: 0, failed: 0", result)
        self.license_2.refresh_from_db()
        self.assertEqual("test-1", self.license_2.scancode_key)
        self.assertEqual("Owner 1", self.license_2.scancode_owner)

    def test_primary_match_wins_over_other_spdx_license_key(self):
        enrich_licenses_from_scancode(
            [
                _entry("test-1", "Test-ScanCode-1", ["Test-ScanCode-2"]),
                _entry("test-2", "Test-ScanCode-2"),
            ]
        )

        self.license_1.refresh_from_db()
        self.assertEqual("test-1", self.license_1.scancode_key)
        self.license_2.refresh_from_db()
        self.assertEqual("test-2", self.license_2.scancode_key)

    def test_ignored_keys(self):
        License.objects.create(spdx_id="LicenseRef-Test-ScanCode", name="LicenseRef Test ScanCode")

        result = enrich_licenses_from_scancode(
            [
                _entry("test-1", None, ["LicenseRef-Test-ScanCode", None]),
                _entry("test-2", "Test-ScanCode-Unknown"),
            ]
        )

        self.assertIn("licenses enriched: 0, cleared: 0, failed: 0", result)
        self.session.get.assert_not_called()

    def test_failed_request_keeps_data(self):
        self.license_1.scancode_key = "test-unavailable"
        self.license_1.scancode_owner = "Old owner"
        self.license_1.save()

        result = enrich_licenses_from_scancode([_entry("test-unavailable", "Test-ScanCode-1")])

        self.assertIn("licenses enriched: 0, cleared: 0, failed: 1", result)
        self.license_1.refresh_from_db()
        self.assertEqual("test-unavailable", self.license_1.scancode_key)
        self.assertEqual("Old owner", self.license_1.scancode_owner)

    def test_invalid_json_counts_as_failed(self):
        self.session.get.side_effect = None
        self.session.get.return_value.json.side_effect = ValueError("invalid JSON")

        result = enrich_licenses_from_scancode([_entry("test-1", "Test-ScanCode-1")])

        self.assertIn("licenses enriched: 0, cleared: 0, failed: 1", result)

    def test_unmatched_license_is_cleared(self):
        self.license_2.scancode_key = "test-old"
        self.license_2.scancode_category = "Copyleft"
        self.license_2.scancode_owner = "Old owner"
        self.license_2.save()

        result = enrich_licenses_from_scancode([_entry("test-1", "Test-ScanCode-1")])

        self.assertIn("licenses enriched: 1, cleared: 1, failed: 0", result)
        self.license_2.refresh_from_db()
        self.assertEqual("", self.license_2.scancode_key)
        self.assertEqual("", self.license_2.scancode_category)
        self.assertEqual("", self.license_2.scancode_owner)
        self.assertEqual("", self.license_2.scancode_homepage_url)

    def _enrich_with_details(self, details: dict) -> License:
        self.session.get.side_effect = None
        self.session.get.return_value.json.return_value = details
        enrich_licenses_from_scancode([_entry("test-1", "Test-ScanCode-1")])
        self.license_1.refresh_from_db()
        return self.license_1

    def test_duplicate_homepage_and_text_url(self):
        spdx_license = self._enrich_with_details(
            {
                "homepage_url": "http://example.com/license",
                "text_urls": ["http://example.com/license"],
            }
        )

        self.assertEqual(["http://example.com/license"], spdx_license.scancode_text_urls)
        self.assertEqual("", spdx_license.scancode_homepage_url)

    def test_duplicate_osi_and_faq_url(self):
        spdx_license = self._enrich_with_details(
            {
                "osi_url": "https://example.com/osi",
                "faq_url": "https://example.com/osi",
                "homepage_url": "https://example.com/home",
            }
        )

        self.assertEqual("https://example.com/osi", spdx_license.scancode_osi_url)
        self.assertEqual("", spdx_license.scancode_faq_url)
        self.assertEqual("https://example.com/home", spdx_license.scancode_homepage_url)

    def test_duplicate_faq_and_homepage_url(self):
        spdx_license = self._enrich_with_details(
            {
                "faq_url": "https://example.com/faq",
                "homepage_url": "https://example.com/faq",
            }
        )

        self.assertEqual("https://example.com/faq", spdx_license.scancode_faq_url)
        self.assertEqual("", spdx_license.scancode_homepage_url)

    def test_duplicate_ignores_scheme_trailing_slash_and_case(self):
        spdx_license = self._enrich_with_details(
            {
                "text_urls": ["http://example.com/License"],
                "osi_url": "HTTPS://Example.com/license/",
                "homepage_url": "https://example.com/license/",
            }
        )

        self.assertEqual(["http://example.com/License"], spdx_license.scancode_text_urls)
        self.assertEqual("", spdx_license.scancode_osi_url)
        self.assertEqual("", spdx_license.scancode_homepage_url)

    def test_duplicates_within_text_urls(self):
        spdx_license = self._enrich_with_details(
            {
                "text_urls": [
                    "http://example.com/text_1",
                    "https://example.com/text_2",
                    "https://example.com/text_1/",
                    "https://example.com/text_2",
                ],
            }
        )

        self.assertEqual(
            ["http://example.com/text_1", "https://example.com/text_2"],
            spdx_license.scancode_text_urls,
        )
