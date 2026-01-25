from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

import jsonpickle
import requests

from application.commons.models import Settings
from application.core.models import Branch, Product, Service
from application.import_observations.models import Vulnerability_Check
from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
    OSVParser,
)
from application.import_observations.queries.parser import get_parser_by_name
from application.import_observations.services.import_observations import (
    ImportParameters,
    _process_data,
)
from application.licenses.models import License_Component


@dataclass
class RequestPURL:
    purl: str


@dataclass
class RequestPackage:
    package: RequestPURL
    page_token: Optional[str]


@dataclass
class RequestQueries:
    queries: list[RequestPackage]


class OSVException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def scan_product(product: Product) -> Tuple[int, int, int]:
    numbers: Tuple[int, int, int] = (0, 0, 0)

    new, updated, resolved = scan_no_branch_no_service(product)
    numbers = (
        numbers[0] + new,
        numbers[1] + updated,
        numbers[2] + resolved,
    )

    branches = Branch.objects.filter(product=product)
    for branch in branches:
        new, updated, resolved = scan_branch_no_service(branch)
        numbers = (
            numbers[0] + new,
            numbers[1] + updated,
            numbers[2] + resolved,
        )

    services = Service.objects.filter(product=product)
    for service in services:
        new, updated, resolved = scan_no_branch_but_service(product, service)
        numbers = (
            numbers[0] + new,
            numbers[1] + updated,
            numbers[2] + resolved,
        )

        for branch in branches:
            new, updated, resolved = scan_branch_and_service(branch, service)
            numbers = (
                numbers[0] + new,
                numbers[1] + updated,
                numbers[2] + resolved,
            )

    return numbers


def scan_branch(branch: Branch) -> Tuple[int, int, int]:
    numbers: Tuple[int, int, int] = (0, 0, 0)

    new, updated, resolved = scan_branch_no_service(branch)
    numbers = (
        numbers[0] + new,
        numbers[1] + updated,
        numbers[2] + resolved,
    )

    services = Service.objects.filter(product=branch.product)
    for service in services:
        new, updated, resolved = scan_branch_and_service(branch, service)
        numbers = (
            numbers[0] + new,
            numbers[1] + updated,
            numbers[2] + resolved,
        )

    return numbers


def scan_no_branch_no_service(product: Product) -> Tuple[int, int, int]:
    license_components = list(
        License_Component.objects.filter(product=product, branch__isnull=True, origin_service__isnull=True).exclude(
            component_purl=""
        )
    )
    return scan_license_components(license_components, product, None, None)


def scan_branch_no_service(branch: Branch) -> Tuple[int, int, int]:
    license_components = list(
        License_Component.objects.filter(branch=branch, origin_service__isnull=True).exclude(component_purl="")
    )
    return scan_license_components(license_components, branch.product, branch, None)


def scan_no_branch_but_service(product: Product, service: Service) -> Tuple[int, int, int]:
    license_components = list(
        License_Component.objects.filter(product=product, branch__isnull=True, origin_service=service).exclude(
            component_purl=""
        )
    )
    return scan_license_components(license_components, product, None, service)


def scan_branch_and_service(branch: Branch, service: Service) -> Tuple[int, int, int]:
    license_components = list(
        License_Component.objects.filter(branch=branch, origin_service=service).exclude(component_purl="")
    )
    return scan_license_components(license_components, branch.product, branch, service)


def scan_license_components(
    license_components: list[License_Component], product: Product, branch: Optional[Branch], service: Optional[Service]
) -> Tuple[int, int, int]:
    if not license_components:
        return 0, 0, 0

    jsonpickle.set_encoder_options("json", ensure_ascii=False)

    next_pages: dict[License_Component, str] = {}
    osv_components, next_pages = _do_scan(license_components, next_pages)

    while next_pages:
        new_osv_components, next_pages = _do_scan(list(next_pages.keys()), next_pages)
        osv_components += new_osv_components

    osv_parser = OSVParser()
    observations, scanner = osv_parser.get_observations(osv_components, product, branch)

    parser = get_parser_by_name(osv_parser.get_name())
    if parser is None:
        raise OSVException(f"Parser {osv_parser.get_name()} not found")  # pylint: disable=broad-exception-raised

    import_parameters = ImportParameters(
        product=product,
        branch=branch,
        service=service,
        parser=parser,
        filename="",
        api_configuration_name="",
        docker_image_name_tag="",
        endpoint_url="",
        kubernetes_cluster="",
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


def _do_scan(
    license_components: list[License_Component],
    next_pages: dict[License_Component, str],
) -> Tuple[list[OSV_Component], dict]:

    osv_components = [
        OSV_Component(
            license_component=license_component,
            vulnerabilities=set(),
        )
        for license_component in license_components
    ]

    slice_actual = 0
    slice_size = 500
    results = []

    while slice_actual * slice_size < len(license_components):
        queries = RequestQueries(
            queries=[
                RequestPackage(
                    RequestPURL(purl=license_component.component_purl),
                    next_pages[license_component] if next_pages else None,
                )
                for license_component in license_components[
                    (slice_actual * slice_size) : ((slice_actual + 1) * slice_size)  # noqa: E203
                ]
            ]
        )

        response = requests.post(  # nosec B113
            # This is a false positive, there is a timeout of 5 minutes
            url="https://api.osv.dev/v1/querybatch",
            data=jsonpickle.encode(queries, unpicklable=False),
            timeout=5 * 60,
        )

        response.raise_for_status()
        results.extend(response.json().get("results", []))

        slice_actual += 1

    if len(osv_components) != len(results):

        print("---------------------------------------")
        print(osv_components)
        print(results)
        print("---------------------------------------")

        raise OSVException(  # pylint: disable=broad-exception-raised
            "Number of results is different than number of components"
        )

    new_next_pages: dict[License_Component, str] = {}
    for i, result in enumerate(results):
        for vuln in result.get("vulns", []):
            osv_components[i].vulnerabilities.add(
                OSV_Vulnerability(
                    id=vuln.get("id"),
                    modified=datetime.fromisoformat(vuln.get("modified")),
                )
            )
        if result.get("next_page_token"):
            new_next_pages[osv_components[i].license_component] = result.get("next_page_token")

    return osv_components, new_next_pages
