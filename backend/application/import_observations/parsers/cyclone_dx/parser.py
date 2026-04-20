import logging
from dataclasses import dataclass
from json import dumps
from typing import Any, Optional

from application.core.models import Branch, Observation, Product
from application.core.types import Severity
from application.import_observations.parsers.base_parser import (
    BaseFileParser,
    BaseParser,
)
from application.import_observations.types import Parser_Filetype, Parser_Type
from application.licenses.models import License_Component
from application.licenses.types import Component_Type

logger = logging.getLogger("secobserve.import_observations.cyclone_dx.dependencies")

type_mapping = {
    "application": Component_Type.TYPE_APPLICATION,
    "framework": Component_Type.TYPE_FRAMEWORK,
    "library": Component_Type.TYPE_LIBRARY,
    "container": Component_Type.TYPE_CONTAINER,
    "platform": Component_Type.TYPE_PLATFORM,
    "operating-system": Component_Type.TYPE_OPERATING_SYSTEM,
    "device": Component_Type.TYPE_DEVICE,
    "device-driver": Component_Type.TYPE_DEVICE_DRIVER,
    "firmware": Component_Type.TYPE_FIRMWARE,
    "file": Component_Type.TYPE_FILE,
    "machine-learning-model": Component_Type.TYPE_MACHINE_LEARNING_MODEL,
    "data": Component_Type.TYPE_DATA,
    "cryptographic-asset": Component_Type.TYPE_CRYPROGHRAPHIC_ASSET,
}


@dataclass
class Component:
    bom_ref: str
    name: str
    version: str
    type: str
    purl: str
    cpe: str
    cyclonedx_bom_link: str
    json: dict[str, str]
    unsaved_declared_licenses: list[str]
    unsaved_concluded_licenses: list[str]


@dataclass
class Metadata:
    serial_number: str
    version: int
    scanner: str
    container_name: str
    container_tag: str
    container_digest: str
    file: str


class CycloneDXParser(BaseParser, BaseFileParser):
    def __init__(self) -> None:
        self.metadata = Metadata("", 1, "", "", "", "", "")
        self.components: dict[str, Component] = {}
        self.dependencies: dict[str, list[str]] = {}

    @classmethod
    def get_name(cls) -> str:
        return "CycloneDX"

    @classmethod
    def get_filetype(cls) -> str:
        return Parser_Filetype.FILETYPE_JSON

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_SCA

    @classmethod
    def sbom(cls) -> bool:
        return True

    def check_format(self, data: Any) -> bool:
        if isinstance(data, dict) and data.get("bomFormat") == "CycloneDX":
            return True
        return False

    def get_observations(self, data: dict, product: Product, branch: Optional[Branch]) -> tuple[list[Observation], str]:
        self.metadata = self._get_metadata(data)
        self.components = self._get_components(data)
        self.dependencies = self._get_dependencies(data)

        observations = self._create_observations(data)

        return observations, self.metadata.scanner

    def get_license_components(self, data: dict) -> tuple[list[License_Component], str]:
        self.metadata = self._get_metadata(data)
        if not self.components:
            self.components = self._get_components(data)
        if not self.dependencies:
            self.dependencies = self._get_dependencies(data)

        components = []

        for component in self.components.values():
            observation_component_dependencies = self._get_component_dependencies(
                component.bom_ref, self.components, self.dependencies
            )
            model_component = License_Component(
                component_name=component.name,
                component_version=component.version,
                component_type=component.type,
                component_purl=component.purl,
                component_cpe=component.cpe,
                component_cyclonedx_bom_link=component.cyclonedx_bom_link,
                component_dependencies=observation_component_dependencies,
            )
            model_component.unsaved_declared_licenses = component.unsaved_declared_licenses
            model_component.unsaved_concluded_licenses = component.unsaved_concluded_licenses

            self._add_license_component_evidence(component, model_component)
            components.append(model_component)

        return components, self.metadata.scanner

    def _add_license_component_evidence(
        self,
        component: Component,
        license_component: License_Component,
    ) -> None:
        evidence = []
        evidence.append("Component")
        evidence.append(dumps(component.json))
        license_component.unsaved_evidences.append(evidence)

    def _get_components(self, data: dict) -> dict[str, Component]:
        components_dict = {}
        components_list: list[Component] = []

        root_components = self._get_root_component_with_subs(data)
        components_list.extend(root_components)

        sbom_components = data.get("components", [])
        for sbom_component in sbom_components:
            components = self._get_sbom_component_with_subs(sbom_component)
            components_list.extend(components)

        for component in components_list:
            components_dict[component.bom_ref] = component

        return components_dict

    def _get_root_component_with_subs(self, data: dict) -> list[Component]:
        metadata_component = data.get("metadata", {}).get("component")
        if not metadata_component:
            return []

        return self._get_sbom_component_with_subs(metadata_component)

    def _get_sbom_component_with_subs(self, component_data: dict[str, Any]) -> list[Component]:
        components: list[Component] = []
        component = self._get_component(component_data)
        if component:
            components.append(component)

        for sub_component in component_data.get("components", []):
            components.extend(self._get_sbom_component_with_subs(sub_component))

        return components

    def _get_component(self, component_data: dict[str, Any]) -> Optional[Component]:

        bom_ref = component_data.get("bom-ref")
        if not bom_ref:
            return None

        declared_licenses: list[str] = []
        concluded_licenses: list[str] = []
        licenses = component_data.get("licenses", [])
        if licenses and licenses[0].get("expression"):
            acknowledgement = licenses[0].get("acknowledgement")
            if acknowledgement == "concluded":
                concluded_licenses.append(licenses[0].get("expression"))
            else:
                declared_licenses.append(licenses[0].get("expression"))
        else:
            for my_license in licenses:
                component_license = my_license.get("license", {}).get("id")
                if not component_license:
                    component_license = my_license.get("license", {}).get("name")
                if not component_license:
                    continue

                acknowledgement = my_license.get("license", {}).get("acknowledgement")
                if acknowledgement == "concluded":
                    if component_license and component_license not in concluded_licenses:
                        concluded_licenses.append(component_license)
                else:
                    if component_license and component_license not in declared_licenses:
                        declared_licenses.append(component_license)

        bom_link = ""
        if self.metadata.serial_number:
            bom_link = f"urn:cdx:{self.metadata.serial_number}/{str(self.metadata.version)}#{bom_ref}"

        return Component(
            bom_ref=bom_ref,
            name=component_data.get("name", ""),
            version=component_data.get("version", ""),
            type=type_mapping.get(component_data.get("type", ""), ""),
            purl=component_data.get("purl", ""),
            cpe=component_data.get("cpe", ""),
            cyclonedx_bom_link=bom_link,
            json=component_data,
            unsaved_declared_licenses=declared_licenses,
            unsaved_concluded_licenses=concluded_licenses,
        )

    def _create_observations(self, data: dict) -> list[Observation]:  # pylint: disable=too-many-locals
        observations = []

        for vulnerability in data.get("vulnerabilities", []):
            vulnerability_id = vulnerability.get("id")
            cvss3_score, cvss3_vector = self._get_cvss(vulnerability, 3)
            cvss4_score, cvss4_vector = self._get_cvss(vulnerability, 4)
            severity = ""
            if not cvss3_score and not cvss4_score:
                severity = self._get_highest_severity(vulnerability)
            cwe = self._get_cwe(vulnerability)
            description = vulnerability.get("description")
            detail = vulnerability.get("detail")
            if detail:
                description += f"\n\n{detail}"
            recommendation = vulnerability.get("recommendation")
            for affected in vulnerability.get("affects", []):
                ref = affected.get("ref")
                if ref:
                    component = self.components.get(ref)
                    if component:
                        title = vulnerability_id

                        observation_component_dependencies = self._get_component_dependencies(
                            ref, self.components, self.dependencies
                        )

                        observation = Observation(
                            title=title,
                            description=description,
                            recommendation=recommendation,
                            parser_severity=severity,
                            vulnerability_id=vulnerability_id,
                            vulnerability_id_aliases=self._get_aliases(vulnerability),
                            origin_component_name=component.name,
                            origin_component_version=component.version,
                            origin_component_type=component.type,
                            origin_component_purl=component.purl,
                            origin_component_cpe=component.cpe,
                            origin_component_cyclonedx_bom_link=component.cyclonedx_bom_link,
                            origin_component_dependencies=observation_component_dependencies,
                            cvss3_score=cvss3_score,
                            cvss3_vector=cvss3_vector,
                            cvss4_score=cvss4_score,
                            cvss4_vector=cvss4_vector,
                            cwe=cwe,
                            scanner=self.metadata.scanner,
                            origin_docker_image_name=self.metadata.container_name,
                            origin_docker_image_tag=self.metadata.container_tag,
                            origin_docker_image_digest=self.metadata.container_digest,
                            origin_source_file=self.metadata.file,
                        )

                        self._add_references(vulnerability, observation)

                        self._add_evidences(
                            vulnerability,
                            component,
                            observation,
                        )

                        observations.append(observation)

        return observations

    def _get_metadata(self, data: dict) -> Metadata:  # pylint: disable=too-many-branches
        scanner = ""
        container_name = ""
        container_tag = ""
        container_digest = ""
        file = ""

        serial_number = data.get("serialNumber", "")
        if serial_number.startswith("urn:uuid:"):
            serial_number = serial_number.replace("urn:uuid:", "")
        else:
            serial_number = ""

        tools = data.get("metadata", {}).get("tools")
        if tools:
            if isinstance(tools, dict):
                components_or_services = tools.get("components", [])
                if not components_or_services:
                    components_or_services = tools.get("services", [])
                if components_or_services:
                    scanner = components_or_services[0].get("name", "")
                    version = components_or_services[0].get("version")
                    if version:
                        scanner += " / " + version

            if isinstance(tools, list):
                scanner = tools[0].get("name", "")
                version = tools[0].get("version")
                if version:
                    scanner += " / " + version

        component_type = data.get("metadata", {}).get("component", {}).get("type")
        component_name = data.get("metadata", {}).get("component", {}).get("name", "")
        component_version = data.get("metadata", {}).get("component", {}).get("version", "")
        if component_type == "container":
            container_name = component_name
            if component_version and component_version.startswith("sha256:"):
                container_digest = component_version
            elif component_version:
                container_tag = component_version
        if component_type == "file":
            file = component_name

        return Metadata(
            serial_number=serial_number,
            version=data.get("version", 1),
            scanner=scanner,
            container_name=container_name,
            container_tag=container_tag,
            container_digest=container_digest,
            file=file,
        )

    def _get_cvss(self, vulnerability: dict, version: int) -> tuple[Optional[float], str]:
        ratings = vulnerability.get("ratings", [])
        if ratings:
            cvss_score = 0
            cvss_vector = ""
            for rating in ratings:
                method = rating.get("method")
                if method and method.lower().startswith(f"cvssv{str(version)}"):
                    current_cvss_score = rating.get("score", 0)
                    if current_cvss_score > cvss_score:
                        cvss_score = current_cvss_score
                        cvss_vector = str(rating.get("vector"))
            if cvss_score > 0:
                return cvss_score, cvss_vector
        return None, ""

    def _get_highest_severity(self, vulnerability: dict) -> str:
        current_severity = Severity.SEVERITY_UNKNOWN
        current_numerical_severity = 999
        ratings = vulnerability.get("ratings", [])
        if ratings:
            for rating in ratings:
                severity = rating.get("severity", Severity.SEVERITY_UNKNOWN).capitalize()
                numerical_severity = Severity.NUMERICAL_SEVERITIES.get(severity, 99)
                if numerical_severity < current_numerical_severity:
                    current_severity = severity
        return current_severity

    def _get_cwe(self, vulnerability: dict) -> Optional[str]:
        cwes = vulnerability.get("cwes", [])
        if len(cwes) >= 1:
            return cwes[0]

        return None

    def _get_aliases(self, vulnerability: dict) -> str:
        aliases = []
        references = vulnerability.get("references", [])
        for reference in references:
            reference_id = reference.get("id")
            if reference_id and reference_id != vulnerability.get("id") and reference_id not in aliases:
                aliases.append(reference_id)
        if aliases:
            return ", ".join(aliases)
        return ""

    def _add_references(self, vulnerability: dict, observation: Observation) -> None:
        advisories = vulnerability.get("advisories", [])
        if advisories:
            for advisory in advisories:
                observation.unsaved_references.append(advisory.get("url"))

    def _add_evidences(
        self,
        vulnerability: dict,
        component: Component,
        observation: Observation,
    ) -> None:
        evidence = []
        evidence.append("Vulnerability")
        evidence.append(dumps(vulnerability))
        observation.unsaved_evidences.append(evidence)

        evidence = []
        evidence.append("Component")
        evidence.append(dumps(component.json))
        observation.unsaved_evidences.append(evidence)

    def _get_dependencies(self, data: dict) -> dict[str, list[str]]:
        dependency_dict: dict[str, list[str]] = {}

        for dependency in data.get("dependencies", {}):
            for dependency_key in dependency.get("dependsOn", []):
                if dependency_key not in dependency_dict:
                    dependency_dict[dependency_key] = [dependency.get("ref")]
                else:
                    dependency_dict[dependency_key].append(dependency.get("ref"))

        return dependency_dict

    def _get_component_dependencies(
        self,
        component_bom_ref: str,
        component_dict: dict[str, Component],
        dependency_dict: dict[str, list[str]],
    ) -> str:
        dependencies: list[str] = []
        self._get_dependencies_recursive(component_bom_ref, component_dict, dependency_dict, dependencies)

        dependencies.sort()
        return "\n".join(dependencies)

    def _get_dependencies_recursive(
        self,
        component_bom_ref: str,
        component_dict: dict[str, Component],
        dependency_dict: dict[str, list[str]],
        dependencies: list[str],
    ) -> None:
        if component_bom_ref in dependency_dict.keys():
            for dependency_id in dependency_dict[component_bom_ref]:
                translated_dependency_id = self._translate_package_id(dependency_id, component_dict)
                translated_package_id = self._translate_package_id(component_bom_ref, component_dict)
                dependency = f"{translated_dependency_id} --> {translated_package_id}"
                if dependency not in dependencies:
                    dependencies.append(dependency)
                    self._get_dependencies_recursive(dependency_id, component_dict, dependency_dict, dependencies)

    def _translate_package_id(self, component_bom_ref: str, component_dict: dict[str, Component]) -> str:
        component = component_dict.get(component_bom_ref)
        if not component:
            logger.warning("Component with BOM ref %s not found", component_bom_ref)
            return ""

        if component.version:
            return f"{component.name}:{component.version}"

        return component.name
