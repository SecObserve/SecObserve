from typing import Any, Optional
from unittest.mock import call, patch

from django.core.management import call_command

from application.commons.models import Settings
from application.core.models import Branch, Observation, Product, Service
from application.import_observations.models import Parser, Vulnerability_Check
from application.import_observations.parsers.base_parser import BaseParser
from application.import_observations.scanners.base_scanner import (
    BaseScanner,
    ScanException,
)
from application.import_observations.services.import_observations import (
    ImportParameters,
)
from application.import_observations.types import Parser_Type
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase

PARSER_NAME = "Scanner Stub"


class ParserStub(BaseParser):
    @classmethod
    def get_name(cls) -> str:
        return PARSER_NAME

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_SCA

    def get_observations(self, data: Any, product: Product, branch: Optional[Branch]) -> tuple[list[Observation], str]:
        return [], PARSER_NAME


class ScannerStub(BaseScanner):
    def __init__(self) -> None:
        super().__init__()
        self.parser = ParserStub()

    def _do_scan(self, license_components: list[License_Component]) -> Any:
        return "scan_result"


class TestBaseScanner(BaseTestCase):
    def setUp(self):
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )
        Parser.objects.create(name=PARSER_NAME, type="SCA", source="Other")

        self.product = Product.objects.get(id=1)

        self.license_component = License_Component.objects.get(product=self.product)
        self.license_component.component_purl = "pkg:pypi/django@5.1.8"
        self.license_component.component_purl_type = "pypi"
        self.license_component.save()

        self.branch_main = Branch.objects.get(product=self.product, name="db_branch_internal_main")
        self.branch_dev = Branch.objects.get(product=self.product, name="db_branch_internal_dev")

        self.service_frontend = Service.objects.get(product=self.product, name="db_service_internal_frontend")
        self.service_backend = Service.objects.get(product=self.product, name="db_service_internal_backend")

    # ---------------------------------------------------------------
    # scan_product
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.base_scanner.BaseScanner._scan_license_components")
    def test_scan_product_no_branch_no_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = None
        self.license_component.origin_service = None
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        ScannerStub().scan_product(self.product)

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

    @patch("application.import_observations.scanners.base_scanner.BaseScanner._scan_license_components")
    def test_scan_product_branch_no_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = self.branch_dev
        self.license_component.origin_service = None
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        ScannerStub().scan_product(self.product)

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

    @patch("application.import_observations.scanners.base_scanner.BaseScanner._scan_license_components")
    def test_scan_product_no_branch_but_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = None
        self.license_component.origin_service = self.service_frontend
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        ScannerStub().scan_product(self.product)

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

    @patch("application.import_observations.scanners.base_scanner.BaseScanner._scan_license_components")
    def test_scan_product_branch_and_service(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = self.branch_main
        self.license_component.origin_service = self.service_frontend
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        ScannerStub().scan_product(self.product)

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

    @patch("application.import_observations.scanners.base_scanner.BaseScanner._scan_license_components")
    def test_scan_product_sums_numbers(self, mock_scan_license_components):
        mock_scan_license_components.return_value = (1, 2, 3)

        numbers = ScannerStub().scan_product(self.product)

        # 1 product + 2 branches + 2 services + 2 services * 2 branches = 9 calls
        self.assertEqual(9, mock_scan_license_components.call_count)
        self.assertEqual((9, 18, 27), numbers)

    # ---------------------------------------------------------------
    # scan_branch
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.base_scanner.BaseScanner._scan_license_components")
    def test_scan_branch(
        self,
        mock_scan_license_components,
    ):
        self.license_component.branch = self.branch_main
        self.license_component.origin_service = self.service_frontend
        self.license_component.save()

        mock_scan_license_components.return_value = (0, 0, 0)
        ScannerStub().scan_branch(self.branch_main)

        expected_calls = [
            call([], self.product, self.branch_main, None),
            call([], self.product, self.branch_main, self.service_backend),
            call([self.license_component], self.product, self.branch_main, self.service_frontend),
        ]
        mock_scan_license_components.assert_has_calls(expected_calls)

    @patch("application.import_observations.scanners.base_scanner.BaseScanner._scan_license_components")
    def test_scan_branch_sums_numbers(self, mock_scan_license_components):
        mock_scan_license_components.return_value = (1, 2, 3)

        numbers = ScannerStub().scan_branch(self.branch_main)

        # 1 branch without service + 2 services = 3 calls
        self.assertEqual(3, mock_scan_license_components.call_count)
        self.assertEqual((3, 6, 9), numbers)

    # ---------------------------------------------------------------
    # _scan_license_components
    # ---------------------------------------------------------------

    @patch("application.import_observations.scanners.base_scanner._process_data")
    def test_scan_license_components_no_license_components(self, mock_process_data):
        numbers = ScannerStub()._scan_license_components([], self.product, None, None)

        self.assertEqual((0, 0, 0), numbers)
        mock_process_data.assert_not_called()

    @patch("application.import_observations.scanners.base_scanner._process_data")
    def test_scan_license_components_no_parser(self, mock_process_data):
        scanner = ScannerStub()
        scanner.parser = None

        with self.assertRaises(ScanException) as e:
            scanner._scan_license_components([], self.product, None, None)

        self.assertEqual("No parser set in scanner class", str(e.exception))
        mock_process_data.assert_not_called()

    @patch("application.import_observations.scanners.base_scanner._process_data")
    def test_scan_license_components_parser_not_found(self, mock_process_data):
        Parser.objects.filter(name=PARSER_NAME).delete()

        with self.assertRaises(ScanException) as e:
            ScannerStub()._scan_license_components([self.license_component], self.product, None, None)

        self.assertEqual(f"Parser {PARSER_NAME} not found", str(e.exception))
        mock_process_data.assert_not_called()

    @patch("application.import_observations.scanners.base_scanner._process_data")
    def test_scan_license_components_success(self, mock_process_data):
        mock_process_data.return_value = (1, 2, 3)

        numbers = ScannerStub()._scan_license_components(
            [self.license_component], self.product, self.branch_main, self.service_frontend
        )

        self.assertEqual((1, 2, 3), numbers)

        mock_process_data.assert_called_once_with(
            ImportParameters(
                product=self.product,
                branch=self.branch_main,
                service=self.service_frontend,
                parser=Parser.objects.get(name=PARSER_NAME),
                filename="",
                api_configuration_name="",
                docker_image_name_tag="",
                endpoint_url="",
                kubernetes_cluster="",
                kubernetes_namespace="",
                kubernetes_resource_type="",
                kubernetes_resource_name="",
                imported_observations=[],
            ),
            Settings.load(),
        )

        vulnerability_check = Vulnerability_Check.objects.get(
            product=self.product,
            branch=self.branch_main,
            service=self.service_frontend,
            filename="",
            api_configuration_name="",
        )
        self.assertEqual(1, vulnerability_check.last_import_observations_new)
        self.assertEqual(2, vulnerability_check.last_import_observations_updated)
        self.assertEqual(3, vulnerability_check.last_import_observations_resolved)
        self.assertEqual(PARSER_NAME, vulnerability_check.scanner)

    # ---------------------------------------------------------------
    # _do_scan
    # ---------------------------------------------------------------

    def test_do_scan_not_implemented(self):
        with self.assertRaises(NotImplementedError) as e:
            BaseScanner()._do_scan([])

        self.assertEqual("scan_license_components() must be overridden", str(e.exception))
