from typing import Any, Optional, Tuple

import jsonpickle

from application.commons.models import Settings
from application.core.models import Branch, Product, Service
from application.import_observations.models import Vulnerability_Check
from application.import_observations.parsers.base_parser import BaseParser
from application.import_observations.queries.parser import get_parser_by_name
from application.import_observations.services.import_observations import (
    ImportParameters,
    _process_data,
)
from application.licenses.models import License_Component


class ScanException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BaseScanner:
    def __init__(self) -> None:
        self.parser: Optional[BaseParser] = None

    def scan_product(self, product: Product) -> Tuple[int, int, int]:
        numbers: Tuple[int, int, int] = (0, 0, 0)

        new, updated, resolved = self._scan_no_branch_no_service(product)
        numbers = (
            numbers[0] + new,
            numbers[1] + updated,
            numbers[2] + resolved,
        )

        branches = Branch.objects.filter(product=product)
        for branch in branches:
            new, updated, resolved = self._scan_branch_no_service(branch)
            numbers = (
                numbers[0] + new,
                numbers[1] + updated,
                numbers[2] + resolved,
            )

        services = Service.objects.filter(product=product)
        for service in services:
            new, updated, resolved = self._scan_no_branch_but_service(product, service)
            numbers = (
                numbers[0] + new,
                numbers[1] + updated,
                numbers[2] + resolved,
            )

            for branch in branches:
                new, updated, resolved = self._scan_branch_and_service(branch, service)
                numbers = (
                    numbers[0] + new,
                    numbers[1] + updated,
                    numbers[2] + resolved,
                )

        return numbers

    def scan_branch(self, branch: Branch) -> Tuple[int, int, int]:
        numbers: Tuple[int, int, int] = (0, 0, 0)

        new, updated, resolved = self._scan_branch_no_service(branch)
        numbers = (
            numbers[0] + new,
            numbers[1] + updated,
            numbers[2] + resolved,
        )

        services = Service.objects.filter(product=branch.product)
        for service in services:
            new, updated, resolved = self._scan_branch_and_service(branch, service)
            numbers = (
                numbers[0] + new,
                numbers[1] + updated,
                numbers[2] + resolved,
            )

        return numbers

    def _scan_no_branch_no_service(self, product: Product) -> Tuple[int, int, int]:
        license_components = list(
            License_Component.objects.filter(product=product, branch__isnull=True, origin_service__isnull=True).exclude(
                component_purl=""
            )
        )
        return self._scan_license_components(license_components, product, None, None)

    def _scan_branch_no_service(self, branch: Branch) -> Tuple[int, int, int]:
        license_components = list(
            License_Component.objects.filter(branch=branch, origin_service__isnull=True).exclude(component_purl="")
        )
        return self._scan_license_components(license_components, branch.product, branch, None)

    def _scan_no_branch_but_service(self, product: Product, service: Service) -> Tuple[int, int, int]:
        license_components = list(
            License_Component.objects.filter(product=product, branch__isnull=True, origin_service=service).exclude(
                component_purl=""
            )
        )
        return self._scan_license_components(license_components, product, None, service)

    def _scan_branch_and_service(self, branch: Branch, service: Service) -> Tuple[int, int, int]:
        license_components = list(
            License_Component.objects.filter(branch=branch, origin_service=service).exclude(component_purl="")
        )
        return self._scan_license_components(license_components, branch.product, branch, service)

    def _scan_license_components(
        self,
        license_components: list[License_Component],
        product: Product,
        branch: Optional[Branch],
        service: Optional[Service],
    ) -> Tuple[int, int, int]:
        if not self.parser:
            raise ScanException("No parser set in scanner class")

        if not license_components:
            return 0, 0, 0

        jsonpickle.set_encoder_options("json", ensure_ascii=False)

        scan_result = self._do_scan(license_components)

        observations, scanner = self.parser.get_observations(data=scan_result, product=product, branch=branch)

        db_parser = get_parser_by_name(self.parser.get_name())
        if db_parser is None:
            raise ScanException(f"Parser {self.parser.get_name()} not found")

        import_parameters = ImportParameters(
            product=product,
            branch=branch,
            service=service,
            parser=db_parser,
            filename="",
            api_configuration_name="",
            docker_image_name_tag="",
            endpoint_url="",
            kubernetes_cluster="",
            kubernetes_namespace="",
            kubernetes_resource_type="",
            kubernetes_resource_name="",
            imported_observations=observations,
        )
        numbers: Tuple[int, int, int] = _process_data(import_parameters, Settings.load())

        Vulnerability_Check.objects.update_or_create(
            product=product,
            branch=branch,
            service=service,
            filename="",
            api_configuration_name="",
            defaults={
                "last_import_observations_new": numbers[0],
                "last_import_observations_updated": numbers[1],
                "last_import_observations_resolved": numbers[2],
                "scanner": scanner,
            },
        )

        return numbers[0], numbers[1], numbers[2]

    def _do_scan(self, license_components: list[License_Component]) -> Any:
        raise NotImplementedError("scan_license_components() must be overridden")
