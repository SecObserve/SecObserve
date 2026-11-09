from datetime import datetime, timezone
from json import dumps, loads
from unittest.mock import MagicMock, call, patch

from django.core.management import call_command

from application.commons.models import Settings
from application.core.models import Branch, Observation, Product, Service
from application.import_observations.models import OSV_Cache, Parser
from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
    create_osv_session,
)
from application.import_observations.scanners.osv_scanner import (
    OSV_QUERYBATCH_READ_RETRIES,
    OSVQuery,
    OSVScanner,
    RequestPURL,
    release_run_cache,
)
from application.import_observations.services.import_observations import (
    ImportParameters,
)
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase


class MockResponse:
    def __init__(self, filename):
        self.filename = filename
        self.next_page_token_first_call = True

    def raise_for_status(self):
        pass

    def json(self):
        if self.filename == "osv_querybatch_next_page_token_first.json":
            if self.next_page_token_first_call:
                self.next_page_token_first_call = False
            else:
                self.filename = "osv_querybatch_next_page_token second.json"

        with open(f"unittests/import_observations/services/files/{self.filename}") as file:
            return loads(file.read())


class TestOSVScanner(BaseTestCase):
    def setUp(self):
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )
        Parser.objects.create(name="OSV (Open Source Vulnerabilities)", type="SCA", source="Other")
        # The settings have to exist in the database, otherwise every Settings.load() returns a new
        # unsaved instance, and unsaved model instances are never equal to each other
        Settings.load().save()

        self.product = Product.objects.get(id=1)

        self.license_component = License_Component.objects.get(product=self.product)
        self.license_component.component_purl = "pkg:pypi/django@5.1.8"
        self.license_component.component_purl_type = "pypi"
        self.license_component.save()

        self.branch_main = Branch.objects.get(product=self.product, name="db_branch_internal_main")
        self.branch_dev = Branch.objects.get(product=self.product, name="db_branch_internal_dev")

        self.service_frontend = Service.objects.get(product=self.product, name="db_service_internal_frontend")
        self.service_backend = Service.objects.get(product=self.product, name="db_service_internal_backend")

    @patch("requests.Session.post")
    @patch("application.import_observations.scanners.osv_scanner.OSVParser.get_observations")
    @patch("application.import_observations.scanners.base_scanner._process_data")
    @patch("application.import_observations.scanners.base_scanner.Vulnerability_Check.objects.update_or_create")
    def test_scan_license_components_error_length(
        self,
        mock_vulnerability_check,
        mock_process_data,
        mock_get_observations,
        mock_requests_post,
    ):
        license_components: list[License_Component] = list(License_Component.objects.all())
        license_components[0].component_purl = "pkg:pypi/django@4.2.11"
        license_components[1].component_purl = "pkg:golang/golang.org/x/net@v0.25.1-0.20240603202750-6249541f2a6c"
        product = Product.objects.get(id=1)
        branch = Branch.objects.get(id=1)

        response = MockResponse("osv_querybatch_error_length.json")
        mock_requests_post.return_value = response

        with self.assertRaises(Exception) as e:
            OSVScanner()._scan_license_components(license_components, product, branch, None)

        self.assertEqual(
            "Number of results is different than number of components",
            str(e.exception),
        )

        mock_requests_post.assert_called_with(
            url="https://api.osv.dev/v1/querybatch",
            data='{"queries": [{"package": {"purl": "pkg:pypi/django@4.2.11"}, "page_token": null}, {"package": {"purl": "pkg:golang/golang.org/x/net@v0.25.1-0.20240603202750-6249541f2a6c"}, "page_token": null}]}',
            timeout=300,
        )

        mock_get_observations.assert_not_called()
        mock_process_data.assert_not_called()
        mock_vulnerability_check.assert_not_called()

    @patch("requests.Session.post")
    @patch("application.import_observations.scanners.osv_scanner.OSVParser.get_observations")
    @patch("application.import_observations.scanners.base_scanner._process_data")
    @patch("application.import_observations.scanners.base_scanner.Vulnerability_Check.objects.update_or_create")
    def test_scan_license_components_error_next_page_token(
        self,
        mock_vulnerability_check,
        mock_process_data,
        mock_get_observations,
        mock_requests_post,
    ):
        license_components: list[License_Component] = list(License_Component.objects.all())
        license_components[0].component_purl = "pkg:pypi/django@4.2.11"
        license_components[1].component_purl = "pkg:golang/golang.org/x/net@v0.25.1-0.20240603202750-6249541f2a6c"
        product = Product.objects.get(id=1)
        branch = Branch.objects.get(id=1)

        response = MockResponse("osv_querybatch_next_page_token_first.json")
        mock_requests_post.return_value = response
        mock_get_observations.return_value = [], "OSV (Open Source Vulnerabilities)"

        OSVScanner()._scan_license_components(license_components, product, branch, None)

        mock_requests_post.assert_has_calls(
            [
                call(
                    url="https://api.osv.dev/v1/querybatch",
                    data='{"queries": [{"package": {"purl": "pkg:pypi/django@4.2.11"}, "page_token": null}, {"package": {"purl": "pkg:golang/golang.org/x/net@v0.25.1-0.20240603202750-6249541f2a6c"}, "page_token": null}]}',
                    timeout=300,
                ),
                call(
                    url="https://api.osv.dev/v1/querybatch",
                    data='{"queries": [{"package": {"purl": "pkg:pypi/django@4.2.11"}, "page_token": "token for query 1"}]}',
                    timeout=300,
                ),
            ]
        )

        mock_get_observations.assert_has_calls(
            [
                call(
                    data=[
                        OSV_Component(
                            license_component=license_components[0],
                            vulnerabilities={
                                OSV_Vulnerability(
                                    id="GHSA-795c-9xpc-xw6g",
                                    modified=datetime(2024, 8, 7, 20, 1, 58, 452618, tzinfo=timezone.utc),
                                ),
                                OSV_Vulnerability(
                                    id="GHSA-5hgc-2vfp-mqvc",
                                    modified=datetime(2024, 10, 30, 19, 23, 43, 662562, tzinfo=timezone.utc),
                                ),
                                # The second page is merged into the component instead of being
                                # appended as a second component for the same purl
                                OSV_Vulnerability(
                                    id="CVE-2025-00001",
                                    modified=datetime(2024, 10, 30, 19, 23, 43, 662562, tzinfo=timezone.utc),
                                ),
                            },
                        ),
                        OSV_Component(
                            license_component=license_components[1],
                            vulnerabilities={
                                OSV_Vulnerability(
                                    id="GO-2024-3333", modified=datetime(2024, 12, 20, 20, 37, 27, tzinfo=timezone.utc)
                                )
                            },
                        ),
                    ],
                    product=product,
                    branch=branch,
                )
            ]
        )
        mock_process_data.assert_called_once()
        mock_vulnerability_check.assert_called_once()

    @patch("requests.Session.post")
    @patch("application.import_observations.scanners.osv_scanner.OSVParser.get_observations")
    @patch("application.import_observations.scanners.base_scanner._process_data")
    @patch("application.import_observations.scanners.base_scanner.Vulnerability_Check.objects.update_or_create")
    def test_scan_license_components_success(
        self,
        mock_vulnerability_check,
        mock_process_data,
        mock_get_observations,
        mock_requests_post,
    ):
        license_components: list[License_Component] = list(License_Component.objects.all())
        license_components[0].component_purl = "pkg:pypi/django@4.2.11"
        license_components[1].component_purl = "pkg:golang/golang.org/x/net@v0.25.1-0.20240603202750-6249541f2a6c"
        product = Product.objects.get(id=1)
        branch = Branch.objects.get(id=1)
        service = Service.objects.get(id=1)
        observation = Observation.objects.get(id=1)

        response = MockResponse("osv_querybatch_success.json")
        mock_requests_post.return_value = response
        mock_process_data.return_value = (1, 2, 3)
        mock_get_observations.return_value = [observation], "OSV (Open Source Vulnerabilities)"

        numbers = OSVScanner()._scan_license_components(license_components, product, branch, service)

        self.assertEqual((1, 2, 3), numbers)

        mock_requests_post.assert_called_with(
            url="https://api.osv.dev/v1/querybatch",
            data='{"queries": [{"package": {"purl": "pkg:pypi/django@4.2.11"}, "page_token": null}, {"package": {"purl": "pkg:golang/golang.org/x/net@v0.25.1-0.20240603202750-6249541f2a6c"}, "page_token": null}]}',
            timeout=300,
        )

        osv_components = [
            OSV_Component(
                license_component=license_components[0],
                vulnerabilities={
                    OSV_Vulnerability(
                        id="GHSA-795c-9xpc-xw6g",
                        modified=datetime(2024, 8, 7, 20, 1, 58, 452618, timezone.utc),
                    ),
                    OSV_Vulnerability(
                        id="GHSA-5hgc-2vfp-mqvc",
                        modified=datetime(2024, 10, 30, 19, 23, 43, 662562, timezone.utc),
                    ),
                },
            ),
            OSV_Component(
                license_component=license_components[1],
                vulnerabilities={
                    OSV_Vulnerability(
                        id="GO-2024-3333",
                        modified=datetime(2024, 12, 20, 20, 37, 27, 0, timezone.utc),
                    ),
                },
            ),
        ]

        mock_get_observations.assert_called_with(data=osv_components, product=product, branch=branch)
        mock_process_data.assert_called_with(
            ImportParameters(
                product=product,
                branch=branch,
                service=service,
                parser=Parser.objects.get(name="OSV (Open Source Vulnerabilities)"),
                filename="",
                api_configuration_name="",
                docker_image_name_tag="",
                endpoint_url="",
                kubernetes_cluster="",
                kubernetes_namespace="",
                kubernetes_resource_type="",
                kubernetes_resource_name="",
                imported_observations=[observation],
            ),
            Settings.load(),
        )
        mock_vulnerability_check.assert_called_with(
            product=product,
            branch=branch,
            service=service,
            filename="",
            api_configuration_name="",
            defaults={
                "last_import_observations_new": 1,
                "last_import_observations_updated": 2,
                "last_import_observations_resolved": 3,
                "scanner": "OSV (Open Source Vulnerabilities)",
            },
        )


class TestOSVScannerPurlCache(BaseTestCase):
    """The scanner asks OSV for a purl once, however many components and products use it."""

    def setUp(self):
        super().setUp()
        self.product = Product(name="product")
        # The caches of the runs are kept by the module, a run of another test must not answer the queries
        for run_id in ("run_1", "run_2"):
            release_run_cache(run_id)

    def _component(self, purl):
        return License_Component(component_name="component", component_purl=purl)

    def _response(self, number_of_results):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"results": [{"vulns": []} for _ in range(number_of_results)]}
        return response

    @patch("requests.Session.post")
    def test_a_purl_is_queried_once_per_scanner(self, mock_requests_post):
        mock_requests_post.return_value = self._response(1)
        scanner = OSVScanner()

        # Two scans of different products that use the same purl
        scanner._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)
        scanner._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)

        mock_requests_post.assert_called_once()

    @patch("requests.Session.post")
    @patch(
        "application.import_observations.scanners.osv_scanner.create_osv_session",
        wraps=create_osv_session,
    )
    def test_querybatch_limits_read_retries(self, mock_create_osv_session, mock_requests_post):
        mock_requests_post.return_value = self._response(1)
        scanner = OSVScanner()

        scanner._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)

        mock_create_osv_session.assert_called_once_with(read_retries=OSV_QUERYBATCH_READ_RETRIES)

    @patch("requests.Session.post")
    def test_a_purl_is_queried_once_per_scan(self, mock_requests_post):
        mock_requests_post.return_value = self._response(2)
        scanner = OSVScanner()

        osv_components = scanner._do_scan(
            [
                self._component("pkg:pypi/django@5.1.8"),
                self._component("pkg:golang/golang.org/x/net@v0.25.1"),
                self._component("pkg:pypi/django@5.1.8"),
            ],
            self.product,
            None,
        )

        # Three components, but only two purls are sent to OSV
        self.assertEqual(3, len(osv_components))
        self.assertEqual(
            '{"queries": [{"package": {"purl": "pkg:pypi/django@5.1.8"}, "page_token": null}, '
            '{"package": {"purl": "pkg:golang/golang.org/x/net@v0.25.1"}, "page_token": null}]}',
            mock_requests_post.call_args.kwargs["data"],
        )

    @patch("requests.Session.post")
    def test_components_do_not_share_the_cached_vulnerabilities(self, mock_requests_post):
        mock_requests_post.return_value = self._response(1)
        scanner = OSVScanner()

        osv_components = scanner._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)
        osv_components[0].vulnerabilities.add(
            OSV_Vulnerability(id="CVE-2020-0001", modified=datetime(2024, 1, 1, tzinfo=timezone.utc))
        )

        self.assertEqual((), scanner.vulnerabilities_by_query[OSVQuery(RequestPURL(purl="pkg:pypi/django@5.1.8"))])

    @patch("requests.Session.post")
    def test_scanners_of_a_run_share_the_cache(self, mock_requests_post):
        mock_requests_post.return_value = self._response(1)

        # The scans of two products of the same run, each in its own background task
        OSVScanner("run_1")._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)
        OSVScanner("run_1")._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)

        mock_requests_post.assert_called_once()

    @patch("requests.Session.post")
    def test_a_new_run_queries_again(self, mock_requests_post):
        mock_requests_post.return_value = self._response(1)

        OSVScanner("run_1")._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)
        OSVScanner("run_2")._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)
        # Without a run, e.g. a manual scan, the scanner keeps its purls for itself
        OSVScanner()._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)

        self.assertEqual(3, mock_requests_post.call_count)

    @patch("requests.Session.post")
    def test_a_released_run_queries_again(self, mock_requests_post):
        mock_requests_post.return_value = self._response(1)

        OSVScanner("run_1")._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)
        release_run_cache("run_1")
        OSVScanner("run_1")._do_scan([self._component("pkg:pypi/django@5.1.8")], self.product, None)

        self.assertEqual(2, mock_requests_post.call_count)


def _component(purl, version=""):
    return License_Component(component_name="component", component_version=version, component_purl=purl)


def _response(results):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": results}
    return response


def _vulnerability(osv_id):
    return {"id": osv_id, "modified": "2024-01-01T00:00:00Z"}


class TestOSVScannerLinuxQueries(BaseTestCase):
    """Linux packages are queried by name, ecosystem and version, if the ecosystem is known."""

    def setUp(self):
        super().setUp()
        for run_id in ("run_1", "run_2"):
            release_run_cache(run_id)

    def _query(self, purl, product=None, branch=None):
        with patch("requests.Session.post") as mock_requests_post:
            mock_requests_post.return_value = _response([{}])
            OSVScanner()._do_scan([_component(purl)], product or Product(), branch)
        return loads(mock_requests_post.call_args.kwargs["data"])["queries"][0]

    def _assert_name_query(self, purl, name, ecosystem, version, product=None, branch=None):
        self.assertEqual(
            {"package": {"name": name, "ecosystem": ecosystem}, "version": version, "page_token": None},
            self._query(purl, product, branch),
        )

    def _assert_purl_query(self, purl, product=None, branch=None):
        self.assertEqual({"package": {"purl": purl}, "page_token": None}, self._query(purl, product, branch))

    def test_autodetection_debian(self):
        self._assert_name_query(
            "pkg:deb/debian/vim@2:9.0.1378-2?arch=amd64&distro=debian-12.4", "vim", "Debian:12", "2:9.0.1378-2"
        )
        self._assert_name_query("pkg:deb/debian/vim@9.0-1?distro=12", "vim", "Debian:12", "9.0-1")

    def test_autodetection_alpine(self):
        self._assert_name_query(
            "pkg:apk/alpine/openssl@3.1.4-r0?arch=x86_64&distro=alpine-3.18.4", "openssl", "Alpine:v3.18", "3.1.4-r0"
        )
        self._assert_name_query("pkg:apk/alpine/openssl@3.1.4-r0?distro=3.18.4", "openssl", "Alpine:v3.18", "3.1.4-r0")

    def test_request_json(self):
        with patch("requests.Session.post") as mock_requests_post:
            mock_requests_post.return_value = _response([{}])
            OSVScanner()._do_scan([_component("pkg:deb/debian/vim@9.0-1?distro=debian-12")], Product(), None)

        self.assertEqual(
            '{"queries": [{"package": {"name": "vim", "ecosystem": "Debian:12"}, "version": "9.0-1", '
            '"page_token": null}]}',
            mock_requests_post.call_args.kwargs["data"],
        )

    def test_no_autodetection(self):
        for purl in (
            # OSV can read the purls of these distributions
            "pkg:deb/ubuntu/openssl@3.0.2-0ubuntu1?arch=amd64&distro=ubuntu-22.04",
            "pkg:apk/chainguard/openssl@3.1.4-r0?arch=x86_64",
            "pkg:apk/wolfi/openssl@3.1.4-r0?arch=x86_64",
            "pkg:rpm/redhat/openssl@3.0.7-1.el9?arch=x86_64&distro=rhel-9.2",
            # The distribution cannot be determined
            "pkg:deb/debian/vim@9.0-1",
            "pkg:deb/debian/vim@9.0-1?distro=bookworm",
            "pkg:apk/alpine/openssl@3.1.4-r0",
        ):
            with self.subTest(purl=purl):
                self._assert_purl_query(purl)

    def test_non_linux_package_with_configured_distribution(self):
        self._assert_purl_query(
            "pkg:pypi/django@5.1.8", Product(osv_linux_distribution="Debian", osv_linux_release="12")
        )

    def test_invalid_purl(self):
        self._assert_purl_query("not a purl", Product(osv_linux_distribution="Debian", osv_linux_release="12"))

    def test_configured_branch_before_product_before_autodetection(self):
        purl = "pkg:deb/debian/vim@9.0-1?distro=debian-12"
        product = Product(osv_linux_distribution="Debian", osv_linux_release="11")
        branch = Branch(osv_linux_distribution="Debian", osv_linux_release="10")

        self._assert_name_query(purl, "vim", "Debian:10", "9.0-1", product, branch)
        self._assert_name_query(purl, "vim", "Debian:11", "9.0-1", product, Branch())
        self._assert_name_query(purl, "vim", "Debian:11", "9.0-1", product)
        self._assert_name_query(purl, "vim", "Debian:12", "9.0-1")

    def test_configured_distribution_without_release(self):
        self._assert_name_query(
            "pkg:deb/debian/vim@9.0-1?distro=debian-12",
            "vim",
            "Debian",
            "9.0-1",
            Product(osv_linux_distribution="Debian"),
        )

    def test_configured_for_package_without_autodetection(self):
        self._assert_name_query(
            "pkg:rpm/rocky/openssl@3.0.7-1.el9?distro=rocky-9",
            "openssl",
            "Rocky Linux:9",
            "3.0.7-1.el9",
            Product(osv_linux_distribution="Rocky Linux", osv_linux_release="9"),
        )
        self._assert_name_query(
            "pkg:deb/ubuntu/openssl@3.0.2-0ubuntu1?distro=ubuntu-22.04",
            "openssl",
            "Ubuntu:Pro:24.04:LTS",
            "3.0.2-0ubuntu1",
            Product(osv_linux_distribution="Ubuntu", osv_linux_release="Pro:24.04:LTS"),
        )

    def test_distributions_queried_without_release(self):
        for distribution, release in (
            ("Red Hat", "enterprise_linux:9"),
            ("Red Hat", "enterprise_linux:9::baseos"),
            ("SUSE", "Linux Enterprise Server 15"),
            ("openSUSE", "Leap"),
            ("openSUSE", "Leap 15.5"),
        ):
            with self.subTest(distribution=distribution, release=release):
                self._assert_name_query(
                    "pkg:rpm/redhat/openssl@3.0.7-1.el9",
                    "openssl",
                    distribution,
                    "3.0.7-1.el9",
                    Product(osv_linux_distribution=distribution, osv_linux_release=release),
                )

    def test_rpm_version_with_epoch(self):
        product = Product(osv_linux_distribution="Rocky Linux", osv_linux_release="9")

        self._assert_name_query(
            "pkg:rpm/rocky/openssl@3.0.7-1.el9?epoch=1", "openssl", "Rocky Linux:9", "1:3.0.7-1.el9", product
        )

    def test_purl_without_version(self):
        self._assert_name_query("pkg:deb/debian/vim?distro=debian-12", "vim", "Debian:12", None)

    @patch("requests.Session.post")
    def test_mixed_batch_maps_results_to_components(self, mock_requests_post):
        mock_requests_post.return_value = _response(
            [{"vulns": [_vulnerability("PYSEC-1")]}, {"vulns": [_vulnerability("DEBIAN-1")]}]
        )
        components = [
            _component("pkg:pypi/django@5.1.8"),
            _component("pkg:deb/debian/vim@9.0-1?distro=debian-12"),
        ]

        osv_components = OSVScanner()._do_scan(components, Product(), None)

        self.assertEqual(
            '{"queries": [{"package": {"purl": "pkg:pypi/django@5.1.8"}, "page_token": null}, '
            '{"package": {"name": "vim", "ecosystem": "Debian:12"}, "version": "9.0-1", "page_token": null}]}',
            mock_requests_post.call_args.kwargs["data"],
        )
        self.assertEqual(components[0], osv_components[0].license_component)
        self.assertEqual({"PYSEC-1"}, {vulnerability.id for vulnerability in osv_components[0].vulnerabilities})
        self.assertEqual(components[1], osv_components[1].license_component)
        self.assertEqual({"DEBIAN-1"}, {vulnerability.id for vulnerability in osv_components[1].vulnerabilities})

    @patch("requests.Session.post")
    def test_pagination(self, mock_requests_post):
        mock_requests_post.side_effect = [
            _response([{"vulns": [_vulnerability("DEBIAN-1")], "next_page_token": "token"}]),
            _response([{"vulns": [_vulnerability("DEBIAN-2")]}]),
        ]

        osv_components = OSVScanner()._do_scan(
            [_component("pkg:deb/debian/vim@9.0-1?distro=debian-12")], Product(), None
        )

        self.assertEqual(
            '{"queries": [{"package": {"name": "vim", "ecosystem": "Debian:12"}, "version": "9.0-1", '
            '"page_token": "token"}]}',
            mock_requests_post.call_args.kwargs["data"],
        )
        self.assertEqual(
            {"DEBIAN-1", "DEBIAN-2"}, {vulnerability.id for vulnerability in osv_components[0].vulnerabilities}
        )

    @patch("requests.Session.post")
    def test_same_purl_different_branches_are_queried_separately(self, mock_requests_post):
        mock_requests_post.side_effect = [
            _response([{"vulns": [_vulnerability("DEBIAN-11")]}]),
            _response([{"vulns": [_vulnerability("DEBIAN-12")]}]),
        ]
        scanner = OSVScanner()
        purl = "pkg:deb/debian/vim@9.0-1"

        osv_components_11 = scanner._do_scan(
            [_component(purl)], Product(), Branch(osv_linux_distribution="Debian", osv_linux_release="11")
        )
        osv_components_12 = scanner._do_scan(
            [_component(purl)], Product(), Branch(osv_linux_distribution="Debian", osv_linux_release="12")
        )

        self.assertEqual(2, mock_requests_post.call_count)
        self.assertEqual({"DEBIAN-11"}, {vulnerability.id for vulnerability in osv_components_11[0].vulnerabilities})
        self.assertEqual({"DEBIAN-12"}, {vulnerability.id for vulnerability in osv_components_12[0].vulnerabilities})

    @patch("requests.Session.post")
    def test_same_purl_different_products_of_a_run_are_queried_separately(self, mock_requests_post):
        mock_requests_post.return_value = _response([{}])
        purl = "pkg:deb/debian/vim@9.0-1"
        product_11 = Product(osv_linux_distribution="Debian", osv_linux_release="11")
        product_12 = Product(osv_linux_distribution="Debian", osv_linux_release="12")

        OSVScanner("run_1")._do_scan([_component(purl)], product_11, None)
        OSVScanner("run_1")._do_scan([_component(purl)], product_12, None)
        OSVScanner("run_1")._do_scan([_component(purl)], product_12, None)

        self.assertEqual(2, mock_requests_post.call_count)

    @patch("requests.Session.post")
    def test_different_releases_queried_without_release_share_a_query(self, mock_requests_post):
        mock_requests_post.return_value = _response([{}])
        purl = "pkg:rpm/redhat/openssl@3.0.7-1.el9"
        product_8 = Product(osv_linux_distribution="Red Hat", osv_linux_release="enterprise_linux:8")
        product_9 = Product(osv_linux_distribution="Red Hat", osv_linux_release="enterprise_linux:9")

        OSVScanner("run_1")._do_scan([_component(purl)], product_8, None)
        OSVScanner("run_1")._do_scan([_component(purl)], product_9, None)

        mock_requests_post.assert_called_once()

    @patch("requests.Session.post")
    def test_architectures_of_a_package_share_a_query(self, mock_requests_post):
        mock_requests_post.return_value = _response([{"vulns": [_vulnerability("DEBIAN-1")]}])

        osv_components = OSVScanner()._do_scan(
            [
                _component("pkg:deb/debian/vim@9.0-1?arch=amd64&distro=debian-12"),
                _component("pkg:deb/debian/vim@9.0-1?arch=arm64&distro=debian-12"),
            ],
            Product(),
            None,
        )

        mock_requests_post.assert_called_once()
        self.assertEqual(1, len(loads(mock_requests_post.call_args.kwargs["data"])["queries"]))
        self.assertEqual(2, len(osv_components))
        for osv_component in osv_components:
            self.assertEqual({"DEBIAN-1"}, {vulnerability.id for vulnerability in osv_component.vulnerabilities})


class TestOSVScannerRedHatObservations(BaseTestCase):
    """The query of the scanner and the release filter of the parser work together."""

    MODIFIED = datetime(2024, 1, 1, tzinfo=timezone.utc)

    def setUp(self):
        super().setUp()
        self._advisory("RHSA-RHEL9-BASEOS", "Red Hat:enterprise_linux:9::baseos", "1:3.0.7-27.el9")
        self._advisory("RHSA-RHEL9-APPSTREAM", "Red Hat:enterprise_linux:9::appstream", "1:3.0.7-28.el9")
        self._advisory("RHSA-RHEL8", "Red Hat:enterprise_linux:8::baseos", "1:3.0.7-27.el8")
        self._advisory("RHSA-RHEL9-OLD", "Red Hat:enterprise_linux:9::baseos", "1:3.0.1-1.el9")

    def _advisory(self, osv_id, ecosystem, fixed):
        OSV_Cache.objects.create(
            osv_id=osv_id,
            modified=self.MODIFIED,
            data=dumps(
                {
                    "id": osv_id,
                    "affected": [
                        {
                            "package": {"name": "openssl", "ecosystem": ecosystem},
                            "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": fixed}]}],
                        }
                    ],
                }
            ),
        )

    def _observation_ids(self, release):
        product = Product(osv_linux_distribution="Red Hat", osv_linux_release=release)
        scanner = OSVScanner()
        component = _component("pkg:rpm/redhat/openssl@3.0.7-1.el9?epoch=1", "3.0.7-1.el9")

        with patch("requests.Session.post") as mock_requests_post:
            mock_requests_post.return_value = _response(
                [
                    {
                        "vulns": [
                            _vulnerability("RHSA-RHEL9-BASEOS"),
                            _vulnerability("RHSA-RHEL9-APPSTREAM"),
                            _vulnerability("RHSA-RHEL8"),
                            _vulnerability("RHSA-RHEL9-OLD"),
                        ]
                    }
                ]
            )
            osv_components = scanner._do_scan([component], product, None)

        self.assertEqual(
            {"name": "openssl", "ecosystem": "Red Hat"},
            loads(mock_requests_post.call_args.kwargs["data"])["queries"][0]["package"],
        )

        observations, _ = scanner.parser.get_observations(osv_components, product, None)
        return {observation.vulnerability_id for observation in observations}

    def test_partial_release(self):
        # The advisories of other releases and an advisory fixed before the installed version are filtered out
        self.assertEqual({"RHSA-RHEL9-BASEOS", "RHSA-RHEL9-APPSTREAM"}, self._observation_ids("enterprise_linux:9"))

    def test_complete_release(self):
        self.assertEqual({"RHSA-RHEL9-BASEOS"}, self._observation_ids("enterprise_linux:9::baseos"))
