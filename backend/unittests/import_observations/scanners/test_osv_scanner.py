from datetime import datetime, timezone
from json import loads
from unittest.mock import MagicMock, call, patch

from django.core.management import call_command

from application.commons.models import Settings
from application.core.models import Branch, Observation, Product, Service
from application.import_observations.models import Parser
from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
)
from application.import_observations.scanners.osv_scanner import OSVScanner
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

    @patch("requests.post")
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

    @patch("requests.post")
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

    @patch("requests.post")
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

    def _component(self, purl):
        return License_Component(component_name="component", component_purl=purl)

    def _response(self, number_of_results):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"results": [{"vulns": []} for _ in range(number_of_results)]}
        return response

    @patch("requests.post")
    def test_a_purl_is_queried_once_per_scanner(self, mock_requests_post):
        mock_requests_post.return_value = self._response(1)
        scanner = OSVScanner()

        # Two scans of different products that use the same purl
        scanner._do_scan([self._component("pkg:pypi/django@5.1.8")])
        scanner._do_scan([self._component("pkg:pypi/django@5.1.8")])

        mock_requests_post.assert_called_once()

    @patch("requests.post")
    def test_a_purl_is_queried_once_per_scan(self, mock_requests_post):
        mock_requests_post.return_value = self._response(2)
        scanner = OSVScanner()

        osv_components = scanner._do_scan(
            [
                self._component("pkg:pypi/django@5.1.8"),
                self._component("pkg:golang/golang.org/x/net@v0.25.1"),
                self._component("pkg:pypi/django@5.1.8"),
            ]
        )

        # Three components, but only two purls are sent to OSV
        self.assertEqual(3, len(osv_components))
        self.assertEqual(
            '{"queries": [{"package": {"purl": "pkg:pypi/django@5.1.8"}, "page_token": null}, '
            '{"package": {"purl": "pkg:golang/golang.org/x/net@v0.25.1"}, "page_token": null}]}',
            mock_requests_post.call_args.kwargs["data"],
        )

    @patch("requests.post")
    def test_components_do_not_share_the_cached_vulnerabilities(self, mock_requests_post):
        mock_requests_post.return_value = self._response(1)
        scanner = OSVScanner()

        osv_components = scanner._do_scan([self._component("pkg:pypi/django@5.1.8")])
        osv_components[0].vulnerabilities.add(
            OSV_Vulnerability(id="CVE-2020-0001", modified=datetime(2024, 1, 1, tzinfo=timezone.utc))
        )

        self.assertEqual((), scanner.vulnerabilities_by_purl["pkg:pypi/django@5.1.8"])
