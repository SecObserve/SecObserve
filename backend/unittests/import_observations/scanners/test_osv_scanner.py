from datetime import datetime, timezone
from json import loads
from unittest.mock import call, patch

from django.core.management import call_command

from application.commons.models import Settings
from application.core.models import Branch, Observation, Product, Service
from application.import_observations.models import Parser
from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
)
from application.import_observations.scanners.osv_scanner import (
    scan_branch,
    scan_license_components,
    scan_product,
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


class TestImportObservations(BaseTestCase):
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

        self.product = Product.objects.get(id=1)

        self.license_component = License_Component.objects.get(product=self.product)
        self.license_component.component_purl = "pkg:pypi/django@5.1.8"
        self.license_component.component_purl_type = "pypi"
        self.license_component.save()

        self.branch_main = Branch.objects.get(product=self.product, name="db_branch_internal_main")
        self.branch_dev = Branch.objects.get(product=self.product, name="db_branch_internal_dev")

        self.service_frontend = Service.objects.get(product=self.product, name="db_service_internal_frontend")
        self.service_backend = Service.objects.get(product=self.product, name="db_service_internal_backend")

    @patch("application.import_observations.scanners.osv_scanner.scan_license_components")
    def test_scan_product_no_branch_no_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = None
        self.license_component.origin_service = None
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        scan_product(self.product)

        expected_calls = [
            call([self.license_component], self.product, None, None),
            call([], self.product, self.branch_dev, None),
            call([], self.product, self.branch_main, None),
            call([], self.product, None, self.service_backend),
            call([], self.product, self.branch_dev, self.service_backend),
            call([], self.product, self.branch_main, self.service_backend),
            call([], self.product, None, self.service_frontend),
            call([], self.product, self.branch_dev, self.service_frontend),
            call([], self.product, self.branch_main, self.service_frontend),
        ]
        mock_scan_license_components.assert_has_calls(expected_calls)

    @patch("application.import_observations.scanners.osv_scanner.scan_license_components")
    def test_scan_product_branch_no_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = self.branch_dev
        self.license_component.origin_service = None
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        scan_product(self.product)

        expected_calls = [
            call([], self.product, None, None),
            call([self.license_component], self.product, self.branch_dev, None),
            call([], self.product, self.branch_main, None),
            call([], self.product, None, self.service_backend),
            call([], self.product, self.branch_dev, self.service_backend),
            call([], self.product, self.branch_main, self.service_backend),
            call([], self.product, None, self.service_frontend),
            call([], self.product, self.branch_dev, self.service_frontend),
            call([], self.product, self.branch_main, self.service_frontend),
        ]
        mock_scan_license_components.assert_has_calls(expected_calls)

    @patch("application.import_observations.scanners.osv_scanner.scan_license_components")
    def test_scan_product_no_branch_but_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = None
        self.license_component.origin_service = self.service_frontend
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        scan_product(self.product)

        expected_calls = [
            call([], self.product, None, None),
            call([], self.product, self.branch_dev, None),
            call([], self.product, self.branch_main, None),
            call([], self.product, None, self.service_backend),
            call([], self.product, self.branch_dev, self.service_backend),
            call([], self.product, self.branch_main, self.service_backend),
            call([self.license_component], self.product, None, self.service_frontend),
            call([], self.product, self.branch_dev, self.service_frontend),
            call([], self.product, self.branch_main, self.service_frontend),
        ]
        mock_scan_license_components.assert_has_calls(expected_calls)

    @patch("application.import_observations.scanners.osv_scanner.scan_license_components")
    def test_scan_product_branch_and_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = self.branch_main
        self.license_component.origin_service = self.service_frontend
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        scan_product(self.product)

        expected_calls = [
            call([], self.product, None, None),
            call([], self.product, self.branch_dev, None),
            call([], self.product, self.branch_main, None),
            call([], self.product, None, self.service_backend),
            call([], self.product, self.branch_dev, self.service_backend),
            call([], self.product, self.branch_main, self.service_backend),
            call([], self.product, None, self.service_frontend),
            call([], self.product, self.branch_dev, self.service_frontend),
            call([self.license_component], self.product, self.branch_main, self.service_frontend),
        ]
        mock_scan_license_components.assert_has_calls(expected_calls)

    @patch("application.import_observations.scanners.osv_scanner.scan_license_components")
    def test_scan_branch(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = self.branch_main
        self.license_component.origin_service = self.service_frontend
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        scan_branch(self.branch_main)

        expected_calls = [
            call([], self.product, self.branch_main, None),
            call([], self.product, self.branch_main, self.service_backend),
            call([self.license_component], self.product, self.branch_main, self.service_frontend),
        ]
        mock_scan_license_components.assert_has_calls(expected_calls)

    @patch("requests.post")
    @patch("application.import_observations.scanners.osv_scanner.OSVParser.get_observations")
    @patch("application.import_observations.scanners.osv_scanner._process_data")
    def test_scan_license_components_no_license_components(
        self, mock_process_data, mock_get_observations, mock_requests_post
    ):
        product = Product.objects.get(id=1)

        numbers = scan_license_components([], product, None, None)

        self.assertEqual((0, 0, 0), numbers)
        mock_requests_post.assert_not_called()
        mock_get_observations.assert_not_called()
        mock_process_data.assert_not_called()

    @patch("requests.post")
    @patch("application.import_observations.scanners.osv_scanner.OSVParser.get_observations")
    @patch("application.import_observations.scanners.osv_scanner._process_data")
    @patch("application.import_observations.scanners.osv_scanner.Vulnerability_Check.objects.update_or_create")
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
            scan_license_components(license_components, product, branch, None)

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
    @patch("application.import_observations.scanners.osv_scanner._process_data")
    @patch("application.import_observations.scanners.osv_scanner.Vulnerability_Check.objects.update_or_create")
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

        scan_license_components(license_components, product, branch, None)

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
                    [
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
                        OSV_Component(
                            license_component=license_components[0],
                            vulnerabilities={
                                OSV_Vulnerability(
                                    id="CVE-2025-00001",
                                    modified=datetime(2024, 10, 30, 19, 23, 43, 662562, tzinfo=timezone.utc),
                                )
                            },
                        ),
                    ],
                    product,
                    branch,
                )
            ]
        )
        mock_process_data.assert_called_once()
        mock_vulnerability_check.assert_called_once()

    @patch("requests.post")
    @patch("application.import_observations.scanners.osv_scanner.OSVParser.get_observations")
    @patch("application.import_observations.scanners.osv_scanner._process_data")
    @patch("application.import_observations.scanners.osv_scanner.Vulnerability_Check.objects.update_or_create")
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

        numbers = scan_license_components(license_components, product, branch, service)

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

        mock_get_observations.assert_called_with(osv_components, product, branch)
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
