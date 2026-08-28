from unittest.mock import call, patch

from application.commons.models import Settings
from application.import_observations.parsers.vulnerablecode.parser import (
    VulnerableCodeComponent,
    VulnerableCodeParser,
)
from application.import_observations.scanners.base_scanner import ScanException
from application.import_observations.scanners.vulnerablecode_scanner import (
    VulnerableCodeScanner,
)
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase

BASE_URL = "https://vulnerablecode.example.com"
PACKAGES_URL = f"{BASE_URL}/api/v3/packages/"
ADVISORIES_URL_BASE = f"{BASE_URL}/api/v3/affected-by-advisories"

PURL_DJANGO = "pkg:pypi/django@5.1.8"
PURL_JSON = "pkg:maven/org.json/json@20190722"

PACKAGES_REQUEST_BODY = (
    '{"purls": ["%s"], "details": true, "ignore_qualifiers_subpath": false, '
    '"max_advisories": 100, "reachability": false}' % PURL_DJANGO
)

EXPECTED_HEADERS = {
    "User-Agent": "VCIO_API_AGENT",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
EXPECTED_HEADERS_WITH_API_KEY = {**EXPECTED_HEADERS, "Authorization": "Token api_key"}

ADVISORY = {
    "advisory_uid": "pysec/PYSEC-2024-157",
    "aliases": ["CVE-2024-53908"],
    "summary": "Potential SQL injection in HasKey lookup",
}


class MockResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class TestVulnerableCodeScanner(BaseTestCase):
    def setUp(self):
        super().setUp()

        self.settings = Settings()
        self.settings.vulnerablecode_base_url = BASE_URL
        self.settings.vulnerablecode_api_key = ""

        self.license_component = License_Component(
            product=self.product_1,
            component_name="django",
            component_version="5.1.8",
            component_purl=PURL_DJANGO,
            component_purl_type="pypi",
        )

    def _packages_result(self, purl=PURL_DJANGO, advisory_uid="pysec/PYSEC-2024-157"):
        return {"purl": purl, "affected_by_vulnerabilities": [{"advisory_uid": advisory_uid}]}

    # ---------------------------------------------------------------
    # __init__
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    def test_parser_is_set(self, mock_settings_load):
        mock_settings_load.return_value = self.settings

        self.assertIsInstance(VulnerableCodeScanner().parser, VulnerableCodeParser)

    # ---------------------------------------------------------------
    # _do_scan
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_no_license_components(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        self.assertEqual([], VulnerableCodeScanner()._do_scan([]))

        mock_post.assert_not_called()
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_no_affected_advisories(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        mock_post.return_value = MockResponse(
            {"next": None, "results": [{"purl": PURL_DJANGO, "affected_by_vulnerabilities": []}]}
        )

        self.assertEqual([], VulnerableCodeScanner()._do_scan([self.license_component]))

        mock_post.assert_called_once_with(
            url=PACKAGES_URL, headers=EXPECTED_HEADERS, data=PACKAGES_REQUEST_BODY, timeout=300
        )
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_success(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        mock_post.return_value = MockResponse({"next": None, "results": [self._packages_result()]})
        mock_get.return_value = MockResponse({"next": None, "results": [ADVISORY]})

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual([VulnerableCodeComponent(component=self.license_component, advisory=ADVISORY)], components)

        mock_post.assert_called_once_with(
            url=PACKAGES_URL, headers=EXPECTED_HEADERS, data=PACKAGES_REQUEST_BODY, timeout=300
        )
        mock_get.assert_called_once_with(
            url=f"{ADVISORIES_URL_BASE}?purl={PURL_DJANGO}", headers=EXPECTED_HEADERS, timeout=300
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_component_without_purl_is_skipped(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        mock_post.return_value = MockResponse({"next": None, "results": [self._packages_result()]})
        mock_get.return_value = MockResponse({"next": None, "results": [ADVISORY]})

        without_purl = License_Component(product=self.product_1, component_name="no-purl", component_purl="")

        VulnerableCodeScanner()._do_scan([self.license_component, without_purl])

        # Only the component with a purl is sent to the API
        mock_post.assert_called_once_with(
            url=PACKAGES_URL, headers=EXPECTED_HEADERS, data=PACKAGES_REQUEST_BODY, timeout=300
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_packages_pagination(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{PACKAGES_URL}?page=2"
        mock_post.side_effect = [
            MockResponse({"next": next_url, "results": [self._packages_result()]}),
            MockResponse({"next": None, "results": [self._packages_result()]}),
        ]
        mock_get.return_value = MockResponse({"next": None, "results": [ADVISORY]})

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual(2, len(components))
        mock_post.assert_has_calls(
            [
                call(url=PACKAGES_URL, headers=EXPECTED_HEADERS, data=PACKAGES_REQUEST_BODY, timeout=300),
                call(url=next_url, headers=EXPECTED_HEADERS, data=PACKAGES_REQUEST_BODY, timeout=300),
            ]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_empty_first_page_continues_pagination(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{PACKAGES_URL}?page=2"
        mock_post.side_effect = [
            MockResponse({"next": next_url, "results": [{"purl": PURL_DJANGO, "affected_by_vulnerabilities": []}]}),
            MockResponse({"next": None, "results": [self._packages_result()]}),
        ]
        mock_get.return_value = MockResponse({"next": None, "results": [ADVISORY]})

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # A page without affected purls must not abandon the remaining pages
        self.assertEqual([VulnerableCodeComponent(component=self.license_component, advisory=ADVISORY)], components)
        mock_post.assert_has_calls(
            [
                call(url=PACKAGES_URL, headers=EXPECTED_HEADERS, data=PACKAGES_REQUEST_BODY, timeout=300),
                call(url=next_url, headers=EXPECTED_HEADERS, data=PACKAGES_REQUEST_BODY, timeout=300),
            ]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_empty_last_page_keeps_earlier_results(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{PACKAGES_URL}?page=2"
        mock_post.side_effect = [
            MockResponse({"next": next_url, "results": [self._packages_result()]}),
            MockResponse({"next": None, "results": [{"purl": PURL_DJANGO, "affected_by_vulnerabilities": []}]}),
        ]
        mock_get.return_value = MockResponse({"next": None, "results": [ADVISORY]})

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # A later page without affected purls must not discard what earlier pages found
        self.assertEqual([VulnerableCodeComponent(component=self.license_component, advisory=ADVISORY)], components)

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_advisories_pagination(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        second_advisory = {"advisory_uid": "ghsa/GHSA-xxxx", "aliases": ["CVE-2024-53907"]}
        next_url = f"{ADVISORIES_URL_BASE}?purl={PURL_DJANGO}&page=2"
        mock_post.return_value = MockResponse({"next": None, "results": [self._packages_result()]})
        mock_get.side_effect = [
            MockResponse({"next": next_url, "results": [ADVISORY]}),
            MockResponse({"next": None, "results": [second_advisory]}),
        ]

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual(
            [
                VulnerableCodeComponent(component=self.license_component, advisory=ADVISORY),
                VulnerableCodeComponent(component=self.license_component, advisory=second_advisory),
            ],
            components,
        )
        mock_get.assert_has_calls(
            [
                call(url=f"{ADVISORIES_URL_BASE}?purl={PURL_DJANGO}", headers=EXPECTED_HEADERS, timeout=300),
                call(url=next_url, headers=EXPECTED_HEADERS, timeout=300),
            ]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_two_purls_share_an_advisory(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        component_json = License_Component(
            product=self.product_1,
            component_name="json",
            component_version="20190722",
            component_purl=PURL_JSON,
            component_purl_type="maven",
        )
        mock_post.return_value = MockResponse(
            {
                "next": None,
                "results": [self._packages_result(), self._packages_result(purl=PURL_JSON)],
            }
        )
        mock_get.return_value = MockResponse({"next": None, "results": [ADVISORY]})

        components = VulnerableCodeScanner()._do_scan([self.license_component, component_json])

        # affected_purls is a set, so the order the advisories come back in is not defined
        self.assertEqual(2, len(components))
        self.assertEqual(
            {PURL_DJANGO, PURL_JSON},
            {vc_component.component.component_purl for vc_component in components},
        )
        for vc_component in components:
            self.assertEqual(ADVISORY, vc_component.advisory)

        self.assertEqual(
            sorted(
                [
                    f"{ADVISORIES_URL_BASE}?purl={PURL_DJANGO}",
                    f"{ADVISORIES_URL_BASE}?purl={PURL_JSON}",
                ]
            ),
            sorted(kwargs["url"] for _, kwargs in mock_get.call_args_list),
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_without_api_key_sets_no_authorization_header(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        mock_post.return_value = MockResponse({"next": None, "results": []})

        scanner = VulnerableCodeScanner()
        scanner._do_scan([self.license_component])

        self.assertEqual(EXPECTED_HEADERS, scanner.headers)
        self.assertEqual(EXPECTED_HEADERS, mock_post.call_args.kwargs["headers"])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    @patch("requests.post")
    def test_do_scan_with_api_key_sets_authorization_header(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_api_key = "api_key"
        mock_settings_load.return_value = self.settings
        mock_post.return_value = MockResponse({"next": None, "results": []})

        scanner = VulnerableCodeScanner()
        scanner._do_scan([self.license_component])

        self.assertEqual(EXPECTED_HEADERS_WITH_API_KEY, scanner.headers)
        self.assertEqual(EXPECTED_HEADERS_WITH_API_KEY, mock_post.call_args.kwargs["headers"])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    def test_api_key_does_not_leak_between_scanners(self, mock_settings_load):
        self.settings.vulnerablecode_api_key = "api_key"
        mock_settings_load.return_value = self.settings
        scanner_with_key = VulnerableCodeScanner()

        self.settings.vulnerablecode_api_key = ""
        scanner_without_key = VulnerableCodeScanner()

        # Each scanner builds its own headers, so clearing the API key takes effect immediately
        self.assertEqual(EXPECTED_HEADERS_WITH_API_KEY, scanner_with_key.headers)
        self.assertEqual(EXPECTED_HEADERS, scanner_without_key.headers)

    # ---------------------------------------------------------------
    # _get_advisories
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.get")
    def test_get_advisories_unknown_purl(self, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        with self.assertRaises(ScanException) as e:
            VulnerableCodeScanner()._get_advisories(
                vulnerablecode_components=[],
                license_components={PURL_DJANGO: self.license_component},
                affected_purls={PURL_JSON},
            )

        self.assertEqual(f"No license component found for purl {PURL_JSON}", str(e.exception))
        mock_get.assert_not_called()
