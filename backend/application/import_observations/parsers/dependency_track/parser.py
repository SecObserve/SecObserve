import json
from typing import Optional

import requests

from application.core.models import Branch, Observation, Product
from application.core.types import Severity, Status
from application.import_observations.models import Api_Configuration
from application.import_observations.parsers.base_parser import (
    BaseAPIParser,
    BaseParser,
)
from application.import_observations.types import Parser_Type

STATUS_MAPPING = {
    "NOT_SET": "",
    "EXPLOITABLE": Status.STATUS_OPEN,
    "IN_TRIAGE": Status.STATUS_IN_REVIEW,
    "RESOLVED": Status.STATUS_RESOLVED,
    "FALSE_POSITIVE": Status.STATUS_FALSE_POSITIVE,
    "NOT_AFFECTED": Status.STATUS_NOT_AFFECTED,
}

PAGE_SIZE = 100


class DependencyTrack(BaseParser, BaseAPIParser):
    def __init__(self) -> None:
        self.api_configuration: Optional[Api_Configuration] = None

    @classmethod
    def get_name(cls) -> str:
        return "Dependency Track"

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_SCA

    def check_connection(self, api_configuration: Api_Configuration) -> tuple[bool, list[str], dict | list]:
        self.api_configuration = api_configuration

        dependency_track_base_url = api_configuration.base_url
        dependency_track_api_key = api_configuration.api_key
        dependency_track_project_key = api_configuration.project_key
        dependency_track_verify_ssl = api_configuration.verify_ssl

        if not dependency_track_base_url.endswith("/"):
            dependency_track_base_url += "/"

        dependency_track_base_url += f"api/v1/finding/project/{dependency_track_project_key}?suppressed=false"

        headers = {
            "X-Api-Key": dependency_track_api_key,
        }
        findings: list[dict] = []
        page_number = 1
        try:
            while True:
                response = requests.get(
                    dependency_track_base_url,
                    headers=headers,
                    params={"pageNumber": page_number, "pageSize": PAGE_SIZE},
                    timeout=60,
                    verify=dependency_track_verify_ssl,
                )
                response.raise_for_status()

                page = response.json()
                findings.extend(page)

                # Dependency-Track 5 paginates the findings and returns their total number in the X-Total-Count
                # header. Dependency-Track 4 returns all findings in one response.
                total_count = response.headers.get("X-Total-Count")
                if not page or not total_count or len(findings) >= int(total_count):
                    break
                page_number += 1
        except Exception as e:
            return False, [f"Cannot access Dependency Track API: {str(e)}"], {}

        return True, [], findings

    def get_observations(  # pylint: disable=too-many-locals
        self, data: list[dict], product: Product, branch: Optional[Branch]
    ) -> tuple[list[Observation], str]:
        observations = []

        scanner, version = self.get_about()
        if version:
            scanner += " / " + version

        for finding in data:
            component_name = finding.get("component", []).get("name")
            component_version = finding.get("component", []).get("version")
            component_purl = finding.get("component", []).get("purl")
            component_cpe = finding.get("component", []).get("cpe")

            vulnerability_id = finding.get("vulnerability", {}).get("vulnId", "")
            cvss_v3_base_score = finding.get("vulnerability", {}).get("cvssV3BaseScore")
            cvss_v3_vector = finding.get("vulnerability", {}).get("cvssV3Vector")
            severity = finding.get("vulnerability", {}).get("severity", Severity.SEVERITY_UNKNOWN)
            description = finding.get("vulnerability", {}).get("description")

            state = finding.get("analysis", {}).get("state")
            reference_url = finding.get("attribution", {}).get("referenceUrl")
            cwes = finding.get("vulnerability", {}).get("cwes", [])

            observation = Observation(
                title=vulnerability_id,
                description=description,
                parser_severity=self.get_severity(severity),
                parser_status=self.get_status(state),
                vulnerability_id=vulnerability_id,
                origin_component_name=component_name,
                origin_component_version=component_version,
                origin_component_purl=component_purl,
                origin_component_cpe=component_cpe,
                cvss3_score=cvss_v3_base_score,
                cvss3_vector=cvss_v3_vector,
                cwe=self.get_cwe(cwes),
                scanner=scanner,
            )

            evidence = []
            evidence.append("Vulnerability")
            evidence.append(json.dumps(finding))
            observation.unsaved_evidences.append(evidence)

            if reference_url:
                observation.unsaved_references = [reference_url]

            observations.append(observation)

        return observations, scanner

    def get_status(self, state: str) -> str:
        if not state:
            return ""

        return STATUS_MAPPING.get(state, "")

    def get_severity(self, severity: str) -> str:
        if (
            severity.capitalize(),
            severity.capitalize(),
        ) in Severity.SEVERITY_CHOICES:
            return severity.capitalize()

        return Severity.SEVERITY_UNKNOWN

    def get_cwe(self, cwes: list[dict]) -> int | None:
        if cwes:
            return cwes[0].get("cweId")

        return None

    def get_about(self) -> tuple[str, Optional[str]]:
        if not self.api_configuration:
            return "Dependency-Track", None

        dependency_track_verify_ssl = self.api_configuration.verify_ssl
        dependency_track_base_url = self.api_configuration.base_url

        if not dependency_track_base_url.endswith("/"):
            dependency_track_base_url += "/"
        dependency_track_base_url += "api/version"

        try:
            response = requests.get(
                dependency_track_base_url,
                timeout=60,
                verify=dependency_track_verify_ssl,
            )
            response.raise_for_status()
        except Exception:
            return "Dependency-Track", None

        application = response.json().get("application", "Dependency-Track")
        version = response.json().get("version")

        return application, version
