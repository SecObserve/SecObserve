import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from json import dumps, loads
from typing import Callable, Optional

import requests
from packageurl import PackageURL

from application.core.models import Branch, Observation, Product
from application.core.types import OSVLinuxDistribution
from application.import_observations.models import OSV_Cache
from application.import_observations.parsers.base_parser import BaseParser
from application.import_observations.parsers.osv.rpm import RpmVersion
from application.import_observations.types import ExtendedSemVer, Parser_Type
from application.licenses.models import License_Component

logger = logging.getLogger("secobserve.import_observations")


@dataclass(frozen=True)
class OSV_Vulnerability:
    id: str
    modified: datetime


@dataclass
class OSV_Component:
    license_component: License_Component
    vulnerabilities: set[OSV_Vulnerability]


@dataclass
class Event:
    type: str
    introduced: str
    fixed: str


OSV_Non_Linux_Ecosystems = {
    "bitnami": "Bitnami",
    "conan": "ConanCenter",
    "cran": "CRAN",
    "cargo": "crates.io",
    "golang": "Go",
    "hackage": "Hackage",
    "hex": "Hex",
    "maven": "Maven",
    "npm": "npm",
    "nuget": "NuGet",
    "pub": "Pub",
    "pypi": "PyPI",
    "gem": "RubyGems",
    "swift": "SwiftURL",
}


class OSVParser(BaseParser):
    @classmethod
    def get_name(cls) -> str:
        return "OSV (Open Source Vulnerabilities)"

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_SCA

    def get_observations(  # pylint: disable=too-many-locals
        self, data: list[OSV_Component], product: Product, branch: Optional[Branch]
    ) -> tuple[list[Observation], str]:
        observations = []

        for osv_component in data:
            ordered_vulnerabilities = sorted(osv_component.vulnerabilities, key=lambda x: x.id)
            osv_cache = self._fill_osv_cache(ordered_vulnerabilities)

            for vulnerability in ordered_vulnerabilities:
                osv_cache_item = osv_cache.get(vulnerability.id)
                if not osv_cache_item:
                    logger.warning("OSV vulnerability %s not found", vulnerability.id)
                    continue

                osv_vulnerability = loads(osv_cache_item.data)
                if osv_vulnerability.get("withdrawn"):
                    continue

                vulnerability_id, vulnerability_id_aliases = self._get_osv_ids(osv_vulnerability)
                osv_cvss3_vector, osv_cvss4_vector = self._get_cvss(osv_vulnerability)

                try:
                    parsed_purl = PackageURL.from_string(osv_component.license_component.component_purl)
                except ValueError as e:
                    logger.error("Invalid PURL %s: %s", osv_component.license_component.component_purl, str(e))
                    continue

                affected_ecosystems = self._get_affected_ecosystems(parsed_purl, osv_vulnerability, product, branch)

                component_in_versions = None
                component_in_ranges = None
                recommendation = ""
                events = []

                for affected_ecosystem in affected_ecosystems:
                    component_in_versions = self._is_version_in_affected(
                        osv_component.license_component.component_version, affected_ecosystem
                    )
                    component_in_ranges, fixed_version, affected_events = self._is_version_in_ranges(
                        parsed_purl,
                        osv_component.license_component.component_version,
                        affected_ecosystem,
                    )

                    events.extend(affected_events)

                    if component_in_versions or component_in_ranges:
                        affected_cvss3_vector, affected_cvss4_vector = self._get_affected_cvss(affected_ecosystem)
                        if affected_cvss3_vector:
                            osv_cvss3_vector = affected_cvss3_vector
                        if affected_cvss4_vector:
                            osv_cvss4_vector = affected_cvss4_vector

                        if fixed_version:
                            recommendation = f"Update to version {fixed_version}"

                        break

                if affected_ecosystems and (
                    (component_in_versions is None and component_in_ranges is None)
                    or component_in_versions is True
                    or component_in_ranges is not False
                ):
                    observation = Observation(
                        title=vulnerability_id,
                        description=self._get_description(
                            osv_vulnerability,
                            component_in_versions,
                            component_in_ranges,
                            events,
                        ),
                        recommendation=recommendation,
                        cvss3_vector=osv_cvss3_vector,
                        cvss4_vector=osv_cvss4_vector,
                        vulnerability_id=vulnerability_id,
                        vulnerability_id_aliases=vulnerability_id_aliases,
                        origin_component_name=osv_component.license_component.component_name,
                        origin_component_version=osv_component.license_component.component_version,
                        origin_component_purl=osv_component.license_component.component_purl,
                        origin_component_cpe=osv_component.license_component.component_cpe,
                        origin_component_cyclonedx_bom_link=osv_component.license_component.component_cyclonedx_bom_link,  # noqa: E501 pylint: disable=line-too-long
                        origin_component_dependencies=osv_component.license_component.component_dependencies,
                    )
                    observations.append(observation)

                    observation.unsaved_references = self._get_references(osv_vulnerability)

                    evidence = []
                    evidence.append("OSV Vulnerability")
                    evidence.append(dumps(osv_vulnerability))
                    observation.unsaved_evidences.append(evidence)

        return observations, self.get_name()

    def _fill_osv_cache(self, ordered_vulnerabilities: list[OSV_Vulnerability]) -> dict[str, OSV_Cache]:
        vulnerability_ids_tmp = {vulnerability.id: vulnerability.modified for vulnerability in ordered_vulnerabilities}
        vulnerabilities_from_cache = list(OSV_Cache.objects.filter(osv_id__in=vulnerability_ids_tmp))
        valid_vulnerability_ids = [
            vulnerability.osv_id
            for vulnerability in vulnerabilities_from_cache
            if vulnerability.modified >= vulnerability_ids_tmp[vulnerability.osv_id]
        ]
        invalid_vulnerability_ids = [
            vulnerability.osv_id
            for vulnerability in vulnerabilities_from_cache
            if vulnerability.modified < vulnerability_ids_tmp[vulnerability.osv_id]
        ]
        OSV_Cache.objects.filter(osv_id__in=invalid_vulnerability_ids).delete()
        missing_osv_vulnerabilities = []
        for osv_vulnerability in ordered_vulnerabilities:
            if osv_vulnerability.id not in valid_vulnerability_ids:
                missing_osv_vulnerabilities.append(osv_vulnerability)

        def _read_osv_vulnerability(osv_vulnerability: OSV_Vulnerability) -> OSV_Cache:
            response = requests.get(
                url=f"https://api.osv.dev/v1/vulns/{osv_vulnerability.id}",
                timeout=60,
            )
            response.raise_for_status()
            return OSV_Cache(osv_id=osv_vulnerability.id, modified=osv_vulnerability.modified, data=response.text)

            # max number of threads to use

        MAX_THREADS = 100

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            osv_cache_items_from_osv = list(executor.map(_read_osv_vulnerability, missing_osv_vulnerabilities))

        if osv_cache_items_from_osv:
            OSV_Cache.objects.bulk_create(osv_cache_items_from_osv)

        valid_osv_cache_items = [
            vulnerability
            for vulnerability in vulnerabilities_from_cache
            if vulnerability.osv_id not in invalid_vulnerability_ids
        ]

        relevant_osv_cache_items = valid_osv_cache_items + osv_cache_items_from_osv
        osv_cache = {osv_cache_item.osv_id: osv_cache_item for osv_cache_item in relevant_osv_cache_items}
        return osv_cache

    def _get_osv_ids(self, osv_vulnerability: dict) -> tuple[str, str]:
        osv_id = str(osv_vulnerability.get("id", ""))

        aliases: list[str] = []
        cve_to_swap = None
        cve_found = False
        for alias in osv_vulnerability.get("aliases", []):
            aliases.append(str(alias))
            if not osv_id.startswith("CVE-") and str(alias).startswith("CVE-"):
                if cve_found:
                    cve_to_swap = None
                else:
                    cve_to_swap = str(alias)
                    cve_found = True
        for alias in osv_vulnerability.get("upstream", []):
            aliases.append(str(alias))
            if not osv_id.startswith("CVE-") and str(alias).startswith("CVE-"):
                if cve_found:
                    cve_to_swap = None
                else:
                    cve_to_swap = str(alias)
                    cve_found = True

        if cve_to_swap:
            aliases.insert(0, osv_id)
            osv_id = cve_to_swap
            aliases = [x for x in aliases if x != cve_to_swap]

        aliases.sort()
        return osv_id, ", ".join(aliases)

    def _get_description(
        self,
        osv_vulnerability: dict,
        component_in_versions: Optional[bool],
        component_in_ranges: Optional[bool],
        events: list[Event],
    ) -> str:
        osv_description_parts: list[str] = []
        if osv_vulnerability.get("summary"):
            osv_description_parts.append(str(osv_vulnerability.get("summary")))
        if osv_vulnerability.get("details"):
            osv_description_parts.append(str(osv_vulnerability.get("details")))

        if component_in_versions:
            osv_description_parts.append("**Confidence: High** (Component found in affected versions)")
        elif component_in_ranges:
            osv_description_parts.append("**Confidence: High** (Component found in affected ranges)")
        elif component_in_versions is None and component_in_ranges is None:
            osv_description_parts.append("**Confidence: Low** (No information about affected versions or ranges)")
        elif component_in_ranges is None:
            osv_description_parts.append("**Confidence: Low** (Events could not be evaluated)")
            osv_description_parts.append("**Events:**")
            for event in events:
                osv_description_parts.append(f"* {event.type}: Introduced: {event.introduced} - Fixed: {event.fixed}")

        return "\n\n".join(osv_description_parts)

    def _get_cvss(self, osv_vulnerability: dict) -> tuple[str, str]:
        cvss3_vector = ""
        cvss4_vector = ""

        severities = osv_vulnerability.get("severity", [])
        for severity in severities:
            if severity.get("type") == "CVSS_V3":
                cvss3_vector = severity.get("score")
            if severity.get("type") == "CVSS_V4":
                cvss4_vector = severity.get("score")

        return cvss3_vector, cvss4_vector

    def _get_references(self, osv_vulnerability: dict) -> list[str]:
        references = []
        for reference in osv_vulnerability.get("references", []):
            references.append(reference.get("url"))
        return references

    def _get_affected_ecosystems(
        self,
        parsed_purl: PackageURL,
        osv_vulnerability: dict,
        product: Product,
        branch: Optional[Branch],
    ) -> list[dict]:

        affected = []

        package_type = parsed_purl.type
        package_name = self._get_package_name(parsed_purl)

        package_osv_ecosystem = OSV_Non_Linux_Ecosystems.get(package_type)

        if not package_osv_ecosystem and branch and branch.osv_linux_distribution and branch.osv_linux_release:
            package_osv_ecosystem = f"{branch.osv_linux_distribution}:{branch.osv_linux_release}"
        if not package_osv_ecosystem and branch and branch.osv_linux_distribution:
            package_osv_ecosystem = branch.osv_linux_distribution

        if not package_osv_ecosystem and product.osv_linux_distribution and product.osv_linux_release:
            package_osv_ecosystem = f"{product.osv_linux_distribution}:{product.osv_linux_release}"
        if not package_osv_ecosystem and product.osv_linux_distribution:
            package_osv_ecosystem = product.osv_linux_distribution

        package_osv_ecosystem = self._get_linux_package_osv_ecosystem(parsed_purl, package_osv_ecosystem)

        for affected_item in osv_vulnerability.get("affected", []):
            package = affected_item.get("package", {})
            affected_ecosystem = package.get("ecosystem")
            affected_name = package.get("name")

            if (
                affected_ecosystem
                and package_osv_ecosystem
                and affected_ecosystem.startswith(package_osv_ecosystem)
                and package_name == affected_name
            ):
                affected.append(affected_item)

        return affected

    def _get_linux_package_osv_ecosystem(
        self, parsed_purl: PackageURL, package_osv_ecosystem: Optional[str]
    ) -> Optional[str]:
        if not package_osv_ecosystem:
            package_osv_ecosystem = self._get_linux_package_osv_ecosystem_apk(parsed_purl)
        if not package_osv_ecosystem:
            package_osv_ecosystem = self._get_linux_package_osv_ecosystem_deb(parsed_purl)
        return package_osv_ecosystem

    def _get_linux_package_osv_ecosystem_apk(self, parsed_purl: PackageURL) -> Optional[str]:
        package_osv_ecosystem = None

        if parsed_purl.qualifiers and isinstance(parsed_purl.qualifiers, dict):
            package_type = parsed_purl.type
            if package_type == "apk" and parsed_purl.namespace == "alpine":
                distro = parsed_purl.qualifiers.get("distro")
                if distro:
                    if distro.startswith("alpine-"):
                        distro = distro[7:]
                    distro_parts = distro.split(".")
                    if len(distro_parts) >= 2 and distro_parts[0].isdigit() and distro_parts[1].isdigit():
                        distro_version = f"{distro_parts[0]}.{distro_parts[1]}"
                        package_osv_ecosystem = f"{OSVLinuxDistribution.DISTRIBUTION_ALPINE}:v{distro_version}"
            elif package_type == "apk" and parsed_purl.namespace == "chainguard":
                package_osv_ecosystem = OSVLinuxDistribution.DISTRIBUTION_CHAINGUARD
            elif package_type == "apk" and parsed_purl.namespace == "wolfi":
                package_osv_ecosystem = OSVLinuxDistribution.DISTRIBUTION_WOLFI

        return package_osv_ecosystem

    def _get_linux_package_osv_ecosystem_deb(self, parsed_purl: PackageURL) -> Optional[str]:
        package_osv_ecosystem = None

        if parsed_purl.qualifiers and isinstance(parsed_purl.qualifiers, dict):
            package_type = parsed_purl.type
            if package_type == "deb" and parsed_purl.namespace == "debian":
                distro = parsed_purl.qualifiers.get("distro")
                if distro:
                    if distro.startswith("debian-"):
                        distro = distro[7:]
                    distro_parts = distro.split(".")
                    if len(distro_parts) >= 1 and distro_parts[0].isdigit():
                        package_osv_ecosystem = f"{OSVLinuxDistribution.DISTRIBUTION_DEBIAN}:{distro_parts[0]}"
            elif package_type == "deb" and parsed_purl.namespace == "ubuntu":
                distro = parsed_purl.qualifiers.get("distro")
                if distro:
                    if distro.startswith("ubuntu-"):
                        distro = distro[7:]
                    distro_parts = distro.split(".")
                    if len(distro_parts) >= 2:
                        if distro_parts[0].isdigit() and int(distro_parts[0]) % 2 == 0 and distro_parts[1] == "04":
                            package_osv_ecosystem = (
                                f"{OSVLinuxDistribution.DISTRIBUTION_UBUNTU}:{distro_parts[0]}.{distro_parts[1]}:LTS"
                            )
                        else:
                            package_osv_ecosystem = (
                                f"{OSVLinuxDistribution.DISTRIBUTION_UBUNTU}:{distro_parts[0]}.{distro_parts[1]}"
                            )

        return package_osv_ecosystem

    def _get_package_name(self, parsed_purl: PackageURL) -> str:
        package_name = parsed_purl.name
        package_namespace = parsed_purl.namespace
        package_type = parsed_purl.type
        if package_namespace and OSV_Non_Linux_Ecosystems.get(package_type):
            if package_type == "maven":
                package_name = f"{package_namespace}:{package_name}"
            else:
                package_name = f"{package_namespace}/{package_name}"
        return package_name

    def _get_affected_cvss(self, affected: dict) -> tuple[str, str]:
        cvss3_vector = ""
        cvss4_vector = ""

        severity = affected.get("severity")
        if severity:
            if severity.get("type") == "CVSS_V3":
                cvss3_vector = severity.get("score")
            if severity.get("type") == "CVSS_V4":
                cvss4_vector = severity.get("score")

        return cvss3_vector, cvss4_vector

    def _is_version_in_affected(self, version: str, affected: dict) -> bool:
        if not version:
            return True

        versions = affected.get("versions", [])
        return version in versions

    def _is_version_in_ranges(
        self, parsed_purl: PackageURL, version: str, affected: dict
    ) -> tuple[Optional[bool], Optional[str], list[Event]]:
        if not version:
            return None, None, []

        version_parser: Callable[[str | None], ExtendedSemVer | RpmVersion | None] = ExtendedSemVer.parse
        if parsed_purl.type == "rpm":
            version_parser = RpmVersion.parse

        events = self._get_events(affected)

        version_semver = version_parser(version)
        if not version_semver:
            return None, None, events

        num_rejected_events = 0
        for event in events:
            if event.type in ("ECOSYSTEM", "SEMVER"):
                introduced_semver = version_parser(event.introduced)
                fixed_semver = version_parser(event.fixed)

                if not introduced_semver:
                    introduced_semver = version_parser("0.0.0")
                if not fixed_semver:
                    continue

                if introduced_semver <= version_semver < fixed_semver:
                    return True, event.fixed, events

                num_rejected_events += 1

        if num_rejected_events == len(events):
            return False, None, events

        return None, None, events

    def _get_events(self, affected: dict) -> list[Event]:
        events = []

        osv_ranges = affected.get("ranges", [])
        for osv_range in osv_ranges:
            event = Event(osv_range.get("type", ""), introduced="", fixed="")
            for osv_event in osv_range.get("events", []):
                introduced = osv_event.get("introduced", "")
                if introduced:
                    event.introduced = introduced
                fixed = osv_event.get("fixed", "")
                if fixed:
                    event.fixed = fixed
                if event.introduced and event.fixed:
                    events.append(event)
                    event = Event(osv_range.get("type", ""), introduced="", fixed="")
        return events
