from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Tuple

import jsonpickle
import requests

from application.import_observations.parsers.osv.parser import (
    OSV_Component,
    OSV_Vulnerability,
    OSVParser,
)
from application.import_observations.scanners.base_scanner import (
    BaseScanner,
    ScanException,
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


class OSVScanner(BaseScanner):
    def __init__(self) -> None:
        super().__init__()
        self.parser = OSVParser()

    def _do_scan(self, license_components: list[License_Component]) -> Any:
        next_pages: dict[License_Component, str] = {}
        osv_components, next_pages = self._do_scan_page(license_components, next_pages)

        while next_pages:
            new_osv_components, next_pages = self._do_scan_page(list(next_pages.keys()), next_pages)
            osv_components += new_osv_components
        return osv_components

    def _do_scan_page(
        self,
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
            raise ScanException(  # pylint: disable=broad-exception-raised
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
