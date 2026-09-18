from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from application.commons.models import Settings
from application.import_observations.models import VulnerableCode_Cache
from application.import_observations.parsers.vulnerablecode.parser import (
    VulnerableCodeComponent,
    VulnerableCodeParser,
)
from application.import_observations.scanners.base_scanner import ScanException
from application.import_observations.scanners.vulnerablecode_scanner import (
    VULNERABLECODE_BACKOFF_FACTOR,
    VULNERABLECODE_MAX_RETRIES,
    VULNERABLECODE_MAX_RETRY_AFTER,
    VulnerableCodeRetry,
    VulnerableCodeScanner,
)
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase

BASE_URL = "https://vulnerablecode.example.com"
PACKAGES_URL = f"{BASE_URL}/api/v3/packages/"
ADVISORIES_URL = f"{BASE_URL}/api/v3/advisories/"

PURL_DJANGO = "pkg:pypi/django@5.1.8"
PURL_JSON = "pkg:maven/org.json/json@20190722"

# Purls as an SBOM has them, with the parts that are cut off before they are sent
PURL_DJANGO_QUALIFIERS = f"{PURL_DJANGO}?arch=amd64&distro=bookworm"
PURL_DJANGO_SUBPATH = f"{PURL_DJANGO}#src/django"
PURL_DJANGO_QUALIFIERS_SUBPATH = f"{PURL_DJANGO}?arch=amd64#src/django"

ADVISORY_UID = "pysec/PYSEC-2024-157"
ADVISORY_UID_2 = "ghsa/GHSA-m9g8-fxxm-xg86"
RESOURCE_URL = f"{BASE_URL}/advisories/{ADVISORY_UID}"
ADVISORY_URL = f"{BASE_URL}/api/v3/advisories/{ADVISORY_UID}"
CVSS3_VECTOR = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"

# The URL that VulnerableCode returns instead of the advisories when a package
# is affected by more than max_advisories advisories
FALLBACK_URL = f"{BASE_URL}/api/v3/affected-by-advisories/?purl={PURL_DJANGO}"


def other_host(url):
    """VulnerableCode builds URLs from the scheme and host it sees, which behind a proxy
    is neither the scheme nor the host that SecObserve is configured with."""
    return url.replace(BASE_URL, "http://vulnerablecode.internal")


def packages_request_body(*purls):
    purl_list = ", ".join(f'"{purl}"' for purl in purls)
    return (
        f'{{"purls": [{purl_list}], "details": true, "ignore_qualifiers_subpath": false, '
        '"max_advisories": 100, "reachability": false}'
    )


def advisories_request_body(*purls):
    purl_list = ", ".join(f'"{purl}"' for purl in purls)
    return f'{{"purls": [{purl_list}]}}'


PACKAGES_REQUEST_BODY = packages_request_body(PURL_DJANGO)
ADVISORIES_REQUEST_BODY = advisories_request_body(PURL_DJANGO)

EXPECTED_HEADERS = {
    "User-Agent": "VCIO_API_AGENT",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
EXPECTED_HEADERS_WITH_API_KEY = {**EXPECTED_HEADERS, "Authorization": "Token api_key"}


def packages_advisory(advisory_uid=ADVISORY_UID, fixed_by_packages=None):
    """An advisory as the packages endpoint returns it: no severities, no references,
    no url, but fixed_by_packages for the purl it was requested with."""
    return {
        "advisory_id": advisory_uid.rsplit("/", 1)[-1],
        "advisory_uid": advisory_uid,
        "aliases": ["CVE-2024-53908"],
        "summary": "Potential SQL injection in HasKey lookup",
        "fixed_by_packages": ["pkg:pypi/django@5.1.4"] if fixed_by_packages is None else fixed_by_packages,
        "resource_url": RESOURCE_URL,
        "risk_score": 8.5,
    }


def advisory_details(advisory_uid=ADVISORY_UID):
    """An advisory as the advisories endpoint returns it: with severities and references,
    but without fixed_by_packages."""
    return {
        "advisory_id": advisory_uid.rsplit("/", 1)[-1],
        "advisory_uid": advisory_uid,
        "aliases": ["CVE-2024-53908", "GHSA-m9g8-fxxm-xg86"],
        "summary": "Potential SQL injection in HasKey lookup",
        "severities": [{"scoring_elements": CVSS3_VECTOR}],
        "references": [{"url": "https://www.djangoproject.com/weblog/2024/dec/04/security-releases/"}],
        "url": ADVISORY_URL,
    }


def merged_advisory(advisory_uid=ADVISORY_UID, fixed_by_packages=None):
    return {
        **packages_advisory(advisory_uid, fixed_by_packages),
        **advisory_details(advisory_uid),
    }


# An advisory as the affected-by-advisories endpoint returns it, which is already complete
FALLBACK_ADVISORY = {**advisory_details(), "fixed_by_packages": ["pkg:pypi/django@5.1.4"]}


class MockRetryAfterResponse:
    def __init__(self, retry_after=None):
        self.headers = {} if retry_after is None else {"Retry-After": retry_after}


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
        # The cache is disabled by default, the tests for it enable it explicitly
        self.settings.vulnerablecode_cache_ttl_hours = 0

        self.license_component = self._component_django()

    def _component_django(self, purl=PURL_DJANGO):
        return License_Component(
            product=self.product_1,
            component_name="django",
            component_version="5.1.8",
            component_purl=purl,
            component_purl_type="pypi",
        )

    def _component_json(self):
        return License_Component(
            product=self.product_1,
            component_name="json",
            component_version="20190722",
            component_purl=PURL_JSON,
            component_purl_type="maven",
        )

    def _packages_result(self, purl=PURL_DJANGO, advisories=None):
        if advisories is None:
            advisories = [packages_advisory()]
        return {"purl": purl, "affected_by_vulnerabilities": advisories}

    def _mock_post(self, mock_post, packages=None, advisories=None):
        """requests.post serves both the packages and the advisories endpoint,
        so the responses are dispatched by URL."""
        responses = {
            PACKAGES_URL: list(packages or []),
            ADVISORIES_URL: list(advisories or []),
        }

        def dispatch(url=None, **kwargs):  # pylint: disable=unused-argument
            for endpoint, remaining in responses.items():
                if url.startswith(endpoint):
                    if not remaining:
                        raise AssertionError(f"Unexpected additional POST to {url}")
                    return remaining.pop(0)
            raise AssertionError(f"Unexpected POST to {url}")

        mock_post.side_effect = dispatch

    def _post_calls(self, mock_post, endpoint):
        return [kwargs for _, kwargs in mock_post.call_args_list if kwargs["url"].startswith(endpoint)]

    # ---------------------------------------------------------------
    # __init__
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    def test_parser_is_set(self, mock_settings_load):
        mock_settings_load.return_value = self.settings

        self.assertIsInstance(VulnerableCodeScanner().parser, VulnerableCodeParser)

    # ---------------------------------------------------------------
    # _create_session
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    def test_retries_are_configured_for_both_schemes(self, mock_settings_load):
        mock_settings_load.return_value = self.settings
        session = VulnerableCodeScanner().session

        # The base URL is configured by an administrator and can be plain http
        for url in ("https://vulnerablecode.example.com", "http://vulnerablecode.internal"):
            retry = session.get_adapter(url).max_retries

            self.assertIsInstance(retry, VulnerableCodeRetry)
            self.assertEqual(VULNERABLECODE_MAX_RETRIES, retry.total)
            self.assertEqual(VULNERABLECODE_BACKOFF_FACTOR, retry.backoff_factor)
            self.assertIn(429, retry.status_forcelist)
            # raise_for_status() shall surface the error, not a urllib3 MaxRetryError
            self.assertFalse(retry.raise_on_status)

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    def test_post_requests_are_retried(self, mock_settings_load):
        mock_settings_load.return_value = self.settings
        session = VulnerableCodeScanner().session

        # urllib3 only retries idempotent methods by default, which would leave the
        # packages and the advisories endpoint without retries
        retry = session.get_adapter("https://vulnerablecode.example.com").max_retries
        self.assertIn("POST", retry.allowed_methods)
        self.assertIn("GET", retry.allowed_methods)

    def test_retry_after_is_capped(self):
        # DRF throttling reports the remaining window, which can be an hour
        self.assertEqual(
            VULNERABLECODE_MAX_RETRY_AFTER, VulnerableCodeRetry().get_retry_after(MockRetryAfterResponse("3600"))
        )

    def test_retry_after_below_the_cap_is_kept(self):
        self.assertEqual(10, VulnerableCodeRetry().get_retry_after(MockRetryAfterResponse("10")))

    def test_no_retry_after_header(self):
        self.assertIsNone(VulnerableCodeRetry().get_retry_after(MockRetryAfterResponse()))

    # ---------------------------------------------------------------
    # _do_scan
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_no_license_components(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        self.assertEqual([], VulnerableCodeScanner()._do_scan([]))

        mock_post.assert_not_called()
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_no_affected_advisories(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result(advisories=[])]})],
        )

        self.assertEqual([], VulnerableCodeScanner()._do_scan([self.license_component]))

        # No advisories are requested when no package is affected
        self.assertEqual(
            [{"url": PACKAGES_URL, "headers": EXPECTED_HEADERS, "data": PACKAGES_REQUEST_BODY, "timeout": 300}],
            self._post_calls(mock_post, PACKAGES_URL),
        )
        self.assertEqual([], self._post_calls(mock_post, ADVISORIES_URL))
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_success(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # The advisory of the packages endpoint is completed with severities,
        # references and url from the advisories endpoint
        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory())], components
        )
        advisory = components[0].advisory
        self.assertEqual([{"scoring_elements": CVSS3_VECTOR}], advisory["severities"])
        self.assertEqual(ADVISORY_URL, advisory["url"])
        # fixed_by_packages only comes from the packages endpoint and must survive the merge
        self.assertEqual(["pkg:pypi/django@5.1.4"], advisory["fixed_by_packages"])

        self.assertEqual(
            [{"url": PACKAGES_URL, "headers": EXPECTED_HEADERS, "data": PACKAGES_REQUEST_BODY, "timeout": 300}],
            self._post_calls(mock_post, PACKAGES_URL),
        )
        self.assertEqual(
            [{"url": ADVISORIES_URL, "headers": EXPECTED_HEADERS, "data": ADVISORIES_REQUEST_BODY, "timeout": 300}],
            self._post_calls(mock_post, ADVISORIES_URL),
        )
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_component_without_purl_is_skipped(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        without_purl = License_Component(product=self.product_1, component_name="no-purl", component_purl="")

        VulnerableCodeScanner()._do_scan([self.license_component, without_purl])

        # Only the component with a purl is sent to the API
        self.assertEqual(PACKAGES_REQUEST_BODY, self._post_calls(mock_post, PACKAGES_URL)[0]["data"])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_packages_pagination(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{PACKAGES_URL}?page=2"
        self._mock_post(
            mock_post,
            packages=[
                MockResponse({"next": next_url, "results": [self._packages_result()]}),
                MockResponse({"next": None, "results": [self._packages_result()]}),
            ],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # The advisories of all pages are collected before they are completed,
        # so a purl returned on more than one page only yields one set of advisories
        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory())], components
        )
        self.assertEqual(
            [PACKAGES_URL, next_url], [kwargs["url"] for kwargs in self._post_calls(mock_post, PACKAGES_URL)]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_empty_first_page_continues_pagination(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{PACKAGES_URL}?page=2"
        self._mock_post(
            mock_post,
            packages=[
                MockResponse({"next": next_url, "results": [self._packages_result(advisories=[])]}),
                MockResponse({"next": None, "results": [self._packages_result()]}),
            ],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # A page without affected purls must not abandon the remaining pages
        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory())], components
        )
        self.assertEqual(
            [PACKAGES_URL, next_url], [kwargs["url"] for kwargs in self._post_calls(mock_post, PACKAGES_URL)]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_empty_last_page_keeps_earlier_results(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{PACKAGES_URL}?page=2"
        self._mock_post(
            mock_post,
            packages=[
                MockResponse({"next": next_url, "results": [self._packages_result()]}),
                MockResponse({"next": None, "results": [self._packages_result(advisories=[])]}),
            ],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # A later page without affected purls must not discard what earlier pages found
        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory())], components
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_advisories_pagination(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{ADVISORIES_URL}?page=2"
        self._mock_post(
            mock_post,
            packages=[
                MockResponse(
                    {
                        "next": None,
                        "results": [
                            self._packages_result(
                                advisories=[packages_advisory(), packages_advisory(advisory_uid=ADVISORY_UID_2)]
                            )
                        ],
                    }
                )
            ],
            advisories=[
                MockResponse({"next": next_url, "results": [advisory_details()]}),
                MockResponse({"next": None, "results": [advisory_details(advisory_uid=ADVISORY_UID_2)]}),
            ],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual(
            [
                VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory()),
                VulnerableCodeComponent(
                    component=self.license_component, advisory=merged_advisory(advisory_uid=ADVISORY_UID_2)
                ),
            ],
            components,
        )
        self.assertEqual(
            [ADVISORIES_URL, next_url], [kwargs["url"] for kwargs in self._post_calls(mock_post, ADVISORIES_URL)]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_two_purls_share_an_advisory(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[
                MockResponse(
                    {
                        "next": None,
                        "results": [self._packages_result(), self._packages_result(purl=PURL_JSON)],
                    }
                )
            ],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component, self._component_json()])

        self.assertEqual(2, len(components))
        self.assertEqual(
            {PURL_DJANGO, PURL_JSON},
            {vc_component.component.component_purl for vc_component in components},
        )
        for vc_component in components:
            self.assertEqual(merged_advisory(), vc_component.advisory)

        # One request for all affected purls instead of one request per purl
        advisories_calls = self._post_calls(mock_post, ADVISORIES_URL)
        self.assertEqual(1, len(advisories_calls))
        self.assertEqual(advisories_request_body(PURL_DJANGO, PURL_JSON), advisories_calls[0]["data"])
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_without_api_key_sets_no_authorization_header(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(mock_post, packages=[MockResponse({"next": None, "results": []})])

        scanner = VulnerableCodeScanner()
        scanner._do_scan([self.license_component])

        self.assertEqual(EXPECTED_HEADERS, scanner.headers)
        self.assertEqual(EXPECTED_HEADERS, mock_post.call_args.kwargs["headers"])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_do_scan_with_api_key_sets_authorization_header(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_api_key = "api_key"
        mock_settings_load.return_value = self.settings
        self._mock_post(mock_post, packages=[MockResponse({"next": None, "results": []})])

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
    # _merge_advisories
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_fixed_by_packages_is_not_shared_between_purls(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[
                MockResponse(
                    {
                        "next": None,
                        "results": [
                            self._packages_result(advisories=[packages_advisory(fixed_by_packages=["django@5.1.4"])]),
                            self._packages_result(
                                purl=PURL_JSON, advisories=[packages_advisory(fixed_by_packages=["json@20231013"])]
                            ),
                        ],
                    }
                )
            ],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component, self._component_json()])

        # The same advisory has a different fixed_by_packages per purl, so the merged
        # advisories must not be the same dict
        fixed_by_packages = {
            vc_component.component.component_purl: vc_component.advisory["fixed_by_packages"]
            for vc_component in components
        }
        self.assertEqual({PURL_DJANGO: ["django@5.1.4"], PURL_JSON: ["json@20231013"]}, fixed_by_packages)

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_advisory_without_details_falls_back_to_resource_url(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            # The advisories endpoint does not return the advisory of the packages endpoint
            advisories=[MockResponse({"next": None, "results": []})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # The advisory is kept, with resource_url as url, so that it still has a reference
        self.assertEqual(1, len(components))
        self.assertEqual({**packages_advisory(), "url": RESOURCE_URL}, components[0].advisory)

    # ---------------------------------------------------------------
    # affected_by_vulnerabilities_url
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_affected_by_vulnerabilities_url_is_followed(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[
                MockResponse(
                    {"next": None, "results": [{"purl": PURL_DJANGO, "affected_by_vulnerabilities_url": FALLBACK_URL}]}
                )
            ],
        )
        mock_get.return_value = MockResponse({"next": None, "results": [FALLBACK_ADVISORY]})

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # A package with more than max_advisories advisories must not be treated as unaffected
        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=FALLBACK_ADVISORY)], components
        )
        mock_get.assert_called_once_with(url=FALLBACK_URL, headers=EXPECTED_HEADERS, timeout=300)
        # Those advisories are already complete, so no details are requested
        self.assertEqual([], self._post_calls(mock_post, ADVISORIES_URL))

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_affected_by_vulnerabilities_url_pagination(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{FALLBACK_URL}&page=2"
        second_advisory = advisory_details(advisory_uid=ADVISORY_UID_2)
        self._mock_post(
            mock_post,
            packages=[
                MockResponse(
                    {"next": None, "results": [{"purl": PURL_DJANGO, "affected_by_vulnerabilities_url": FALLBACK_URL}]}
                )
            ],
        )
        mock_get.side_effect = [
            MockResponse({"next": next_url, "results": [FALLBACK_ADVISORY]}),
            MockResponse({"next": None, "results": [second_advisory]}),
        ]

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual(
            [
                VulnerableCodeComponent(component=self.license_component, advisory=FALLBACK_ADVISORY),
                VulnerableCodeComponent(component=self.license_component, advisory=second_advisory),
            ],
            components,
        )
        self.assertEqual([FALLBACK_URL, next_url], [kwargs["url"] for _, kwargs in mock_get.call_args_list])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_affected_by_vulnerabilities_url_is_not_cached_as_empty(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[
                MockResponse(
                    {"next": None, "results": [{"purl": PURL_DJANGO, "affected_by_vulnerabilities_url": FALLBACK_URL}]}
                )
            ],
        )
        mock_get.return_value = MockResponse({"next": None, "results": [FALLBACK_ADVISORY]})

        VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual([FALLBACK_ADVISORY], VulnerableCode_Cache.objects.get(purl=PURL_DJANGO).data)

    # ---------------------------------------------------------------
    # _rebuild_url
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_packages_next_url_is_rebuilt(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{PACKAGES_URL}?page=2"
        self._mock_post(
            mock_post,
            packages=[
                MockResponse({"next": other_host(next_url), "results": [self._packages_result()]}),
                MockResponse({"next": None, "results": []}),
            ],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        VulnerableCodeScanner()._do_scan([self.license_component])

        # The next page is requested from the configured instance, not from the host of
        # the next link, which would redirect and turn the POST into a GET
        self.assertEqual(
            [PACKAGES_URL, next_url], [kwargs["url"] for kwargs in self._post_calls(mock_post, PACKAGES_URL)]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_advisories_next_url_is_rebuilt(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{ADVISORIES_URL}?page=2"
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[
                MockResponse({"next": other_host(next_url), "results": [advisory_details()]}),
                MockResponse({"next": None, "results": []}),
            ],
        )

        VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual(
            [ADVISORIES_URL, next_url], [kwargs["url"] for kwargs in self._post_calls(mock_post, ADVISORIES_URL)]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_affected_by_vulnerabilities_url_is_rebuilt(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        next_url = f"{FALLBACK_URL}&page=2"
        self._mock_post(
            mock_post,
            packages=[
                MockResponse(
                    {
                        "next": None,
                        "results": [{"purl": PURL_DJANGO, "affected_by_vulnerabilities_url": other_host(FALLBACK_URL)}],
                    }
                )
            ],
        )
        mock_get.side_effect = [
            MockResponse({"next": other_host(next_url), "results": [FALLBACK_ADVISORY]}),
            MockResponse({"next": None, "results": []}),
        ]

        VulnerableCodeScanner()._do_scan([self.license_component])

        # Both the url from the packages endpoint and its next link keep path and query,
        # but are requested from the configured instance
        self.assertEqual([FALLBACK_URL, next_url], [kwargs["url"] for _, kwargs in mock_get.call_args_list])

    # ---------------------------------------------------------------
    # _strip_purl
    # ---------------------------------------------------------------

    def _scan_with_stripped_purl(self, mock_post, license_components):
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan(license_components)

        # Everything behind the version is cut off before the purl is sent
        self.assertEqual(PACKAGES_REQUEST_BODY, self._post_calls(mock_post, PACKAGES_URL)[0]["data"])
        self.assertEqual(ADVISORIES_REQUEST_BODY, self._post_calls(mock_post, ADVISORIES_URL)[0]["data"])
        return components

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_purl_qualifiers_are_stripped(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        components = self._scan_with_stripped_purl(mock_post, [self._component_django(PURL_DJANGO_QUALIFIERS)])

        # The observation keeps the full purl of the component
        self.assertEqual(1, len(components))
        self.assertEqual(PURL_DJANGO_QUALIFIERS, components[0].component.component_purl)
        self.assertEqual(merged_advisory(), components[0].advisory)

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_purl_subpath_is_stripped(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        components = self._scan_with_stripped_purl(mock_post, [self._component_django(PURL_DJANGO_SUBPATH)])

        self.assertEqual([PURL_DJANGO_SUBPATH], [component.component.component_purl for component in components])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_purl_qualifiers_and_subpath_are_stripped(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        components = self._scan_with_stripped_purl(mock_post, [self._component_django(PURL_DJANGO_QUALIFIERS_SUBPATH)])

        self.assertEqual(
            [PURL_DJANGO_QUALIFIERS_SUBPATH], [component.component.component_purl for component in components]
        )

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_components_with_the_same_stripped_purl(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        components = self._scan_with_stripped_purl(
            mock_post,
            [
                self._component_django(PURL_DJANGO_QUALIFIERS),
                self._component_django(PURL_DJANGO_SUBPATH),
                self._component_django(),
            ],
        )

        # The purl is requested once, but every component gets its own observation
        self.assertEqual(
            [PURL_DJANGO_QUALIFIERS, PURL_DJANGO_SUBPATH, PURL_DJANGO],
            [component.component.component_purl for component in components],
        )
        for component in components:
            self.assertEqual(merged_advisory(), component.advisory)

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_cache_is_keyed_by_the_stripped_purl(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        VulnerableCodeScanner()._do_scan([self._component_django(PURL_DJANGO_QUALIFIERS)])

        self.assertEqual([PURL_DJANGO], [cache_item.purl for cache_item in VulnerableCode_Cache.objects.all()])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_cache_hit_for_purl_with_qualifiers(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        VulnerableCode_Cache.objects.create(purl=PURL_DJANGO, data=[merged_advisory()])

        components = VulnerableCodeScanner()._do_scan([self._component_django(PURL_DJANGO_QUALIFIERS)])

        # The stripped purl hits the cache entry of the component without qualifiers
        self.assertEqual(
            [VulnerableCodeComponent(component=components[0].component, advisory=merged_advisory())], components
        )
        self.assertEqual(PURL_DJANGO_QUALIFIERS, components[0].component.component_purl)
        mock_post.assert_not_called()
        mock_get.assert_not_called()

    # ---------------------------------------------------------------
    # _get_advisories
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_get_advisories_unknown_purl(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        with self.assertRaises(ScanException) as e:
            VulnerableCodeScanner()._get_advisories(
                license_components={PURL_DJANGO: [self.license_component]},
                packages_advisories={PURL_JSON: [packages_advisory()]},
                fallback_urls={},
            )

        self.assertEqual(f"No license component found for purl {PURL_JSON}", str(e.exception))
        mock_post.assert_not_called()
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_get_advisories_unknown_purl_from_fallback_url(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings

        with self.assertRaises(ScanException) as e:
            VulnerableCodeScanner()._get_advisories(
                license_components={PURL_DJANGO: [self.license_component]},
                packages_advisories={},
                fallback_urls={PURL_JSON: FALLBACK_URL},
            )

        self.assertEqual(f"No license component found for purl {PURL_JSON}", str(e.exception))
        mock_post.assert_not_called()
        mock_get.assert_not_called()

    # ---------------------------------------------------------------
    # VulnerableCode_Cache
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_cache_hit_makes_no_requests(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        VulnerableCode_Cache.objects.create(purl=PURL_DJANGO, data=[merged_advisory()])

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory())], components
        )
        mock_post.assert_not_called()
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_cache_hit_without_advisories_makes_no_requests(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        VulnerableCode_Cache.objects.create(purl=PURL_DJANGO, data=[])

        # A purl that is known not to be affected is not requested again either
        self.assertEqual([], VulnerableCodeScanner()._do_scan([self.license_component]))
        mock_post.assert_not_called()
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_cache_hit_for_one_of_two_purls(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        VulnerableCode_Cache.objects.create(purl=PURL_DJANGO, data=[merged_advisory()])
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result(purl=PURL_JSON)]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component, self._component_json()])

        self.assertEqual(
            {PURL_DJANGO, PURL_JSON},
            {vc_component.component.component_purl for vc_component in components},
        )
        # Only the uncached purl is sent to the API
        self.assertEqual(packages_request_body(PURL_JSON), self._post_calls(mock_post, PACKAGES_URL)[0]["data"])
        self.assertEqual(advisories_request_body(PURL_JSON), self._post_calls(mock_post, ADVISORIES_URL)[0]["data"])

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_expired_cache_entry_is_refreshed(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        cache_item = VulnerableCode_Cache.objects.create(purl=PURL_DJANGO, data=[])
        expired = timezone.now() - timedelta(hours=24)
        VulnerableCode_Cache.objects.filter(pk=cache_item.pk).update(last_updated=expired)
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory())], components
        )

        # The expired entry is updated in place, not duplicated
        self.assertEqual(1, VulnerableCode_Cache.objects.filter(purl=PURL_DJANGO).count())
        cache_item.refresh_from_db()
        self.assertEqual([merged_advisory()], cache_item.data)
        self.assertGreater(cache_item.last_updated, expired)

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_advisories_are_written_to_cache(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        VulnerableCodeScanner()._do_scan([self.license_component])

        # The merged advisories are cached, so that a cache hit needs no completion
        self.assertEqual([merged_advisory()], VulnerableCode_Cache.objects.get(purl=PURL_DJANGO).data)

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_purl_without_advisories_is_written_to_cache(self, mock_post, mock_get, mock_settings_load):
        self.settings.vulnerablecode_cache_ttl_hours = 23
        mock_settings_load.return_value = self.settings
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result(advisories=[])]})],
        )

        VulnerableCodeScanner()._do_scan([self.license_component])

        # Negative result, so that the purl can be skipped on the next scan
        self.assertEqual([], VulnerableCode_Cache.objects.get(purl=PURL_DJANGO).data)
        self.assertEqual([], self._post_calls(mock_post, ADVISORIES_URL))
        mock_get.assert_not_called()

    @patch("application.import_observations.scanners.vulnerablecode_scanner.Settings.load")
    @patch("requests.Session.get")
    @patch("requests.Session.post")
    def test_cache_ttl_zero_disables_the_cache(self, mock_post, mock_get, mock_settings_load):
        mock_settings_load.return_value = self.settings
        VulnerableCode_Cache.objects.create(purl=PURL_DJANGO, data=[])
        self._mock_post(
            mock_post,
            packages=[MockResponse({"next": None, "results": [self._packages_result()]})],
            advisories=[MockResponse({"next": None, "results": [advisory_details()]})],
        )

        components = VulnerableCodeScanner()._do_scan([self.license_component])

        # The existing entry is neither read ...
        self.assertEqual(
            [VulnerableCodeComponent(component=self.license_component, advisory=merged_advisory())], components
        )
        # ... nor written
        self.assertEqual([], VulnerableCode_Cache.objects.get(purl=PURL_DJANGO).data)
