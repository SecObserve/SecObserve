from dataclasses import dataclass
from typing import Any, Optional

import jsonpickle
import requests

from application.commons.models import Settings
from application.import_observations.parsers.vulnerablecode.parser import (
    VulnerableCodeComponent,
    VulnerableCodeParser,
)
from application.import_observations.scanners.base_scanner import (
    BaseScanner,
    ScanException,
)
from application.licenses.models import License_Component


@dataclass
class RequestPackages:
    purls: list[str]
    details: Optional[bool] = True
    ignore_qualifiers_subpath: Optional[bool] = False
    max_advisories: Optional[int] = 100
    reachability: Optional[bool] = False


@dataclass
class RequestAdvisories:
    purls: list[str]


class VulnerableCodeScanner(BaseScanner):
    def __init__(self) -> None:
        super().__init__()
        self.parser = VulnerableCodeParser()

        settings = Settings.load()
        self.base_url = settings.vulnerablecode_base_url
        self.headers = {
            "User-Agent": "VCIO_API_AGENT",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if settings.vulnerablecode_api_key:
            self.headers["Authorization"] = f"Token {settings.vulnerablecode_api_key}"

    def _do_scan(self, license_components: list[License_Component]) -> Any:
        if not license_components:
            return []

        vulnerablecode_components: list[VulnerableCodeComponent] = []

        jsonpickle.set_encoder_options("json", ensure_ascii=False)

        license_components_dict: dict[str, License_Component] = {
            license_component.component_purl: license_component
            for license_component in license_components
            if license_component.component_purl
        }

        packages_request_data = RequestPackages(purls=list(license_components_dict.keys()))
        packages_url = f"{self.base_url}/api/v3/packages/"

        while packages_url:
            response = requests.post(  # nosec B113
                # This is a false positive, there is a timeout of 5 minutes
                url=packages_url,
                headers=self.headers,
                data=jsonpickle.encode(packages_request_data, unpicklable=False),
                timeout=5 * 60,
            )

            response.raise_for_status()

            packages_url = response.json().get("next")
            results = response.json().get("results", [])

            affected_advisories: dict[str, list[str]] = {}

            for result in results:
                for affected_by_vulnerability in result.get("affected_by_vulnerabilities", []):
                    purl_list = affected_advisories.get(affected_by_vulnerability.get("advisory_uid"))
                    if purl_list:
                        purl_list.append(result.get("purl"))
                    else:
                        affected_advisories[affected_by_vulnerability.get("advisory_uid")] = [result.get("purl")]

            affected_purls = set()
            for purl_list in affected_advisories.values():
                for purl in purl_list:
                    affected_purls.add(purl)

            if not affected_purls:
                continue

            self._get_advisories(
                vulnerablecode_components=vulnerablecode_components,
                license_components=license_components_dict,
                # affected_advisories=affected_advisories,
                affected_purls=affected_purls,
            )

        return vulnerablecode_components

    def _get_advisories(
        self,
        vulnerablecode_components: list[VulnerableCodeComponent],
        license_components: dict[str, License_Component],
        affected_purls: set[str],
    ) -> None:
        advisories_url_base = f"{self.base_url}/api/v3/affected-by-advisories"

        for purl in affected_purls:
            license_component = license_components.get(purl)
            if license_component is None:
                raise ScanException(f"No license component found for purl {purl}")

            advisories_url = f"{advisories_url_base}?purl={purl}"

            while advisories_url:
                response = requests.get(  # nosec B113
                    # This is a false positive, there is a timeout of 5 minutes
                    url=advisories_url,
                    headers=self.headers,
                    timeout=5 * 60,
                )

                response.raise_for_status()

                advisories_url = response.json().get("next")
                results = response.json().get("results", [])
                for result in results:
                    vulnerablecode_components.append(
                        VulnerableCodeComponent(component=license_component, advisory=result)
                    )

    def _get_advisories_1(  # pragma: no cover
        # Alternative implementation, not called at the moment
        self,
        vulnerablecode_components: list[VulnerableCodeComponent],
        license_components: dict[str, License_Component],
        affected_advisories: dict[str, list[str]],
        affected_purls: set[str],
    ) -> None:
        advisories_request_data = RequestAdvisories(purls=list(affected_purls))
        advisories_url = f"{self.base_url}/api/v3/advisories/"

        while advisories_url:
            response = requests.post(  # nosec B113
                # This is a false positive, there is a timeout of 5 minutes
                url=advisories_url,
                headers=self.headers,
                data=jsonpickle.encode(advisories_request_data, unpicklable=False),
                timeout=5 * 60,
            )

            response.raise_for_status()

            advisories_url = response.json().get("next")
            results = response.json().get("results", [])

            for result in results:
                advisory_uid = result.get("advisory_uid")
                affected_purls_for_advisory = affected_advisories.get(advisory_uid)
                if affected_purls_for_advisory:
                    for purl in affected_purls_for_advisory:
                        license_component = license_components.get(purl)
                        if license_component is None:
                            raise ScanException(f"No license component found for purl {purl}")
                        vulnerablecode_components.append(
                            VulnerableCodeComponent(component=license_component, advisory=result)
                        )
