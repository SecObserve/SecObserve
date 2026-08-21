import logging
from dataclasses import dataclass
from json import dumps
from typing import Optional, Tuple

from packageurl import PackageURL

from application.core.models import Branch, Observation, Product
from application.import_observations.parsers.base_parser import BaseParser
from application.import_observations.types import Parser_Type
from application.licenses.models import License_Component

logger = logging.getLogger("secobserve.import_observations")


@dataclass
class VulnerableCodeComponent:
    component: License_Component
    advisory: dict


class VulnerableCodeParser(BaseParser):
    @classmethod
    def get_name(cls) -> str:
        return "VulnerableCode"

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_SCA

    def get_observations(
        self, data: list[VulnerableCodeComponent], product: Product, branch: Optional[Branch]
    ) -> tuple[list[Observation], str]:
        observations: list[Observation] = []
        for vc_component in data:
            title = self._get_title(vc_component.advisory)
            summary = vc_component.advisory.get("summary", "")
            cvss3_vector, cvss4_vector = self._get_severities(vc_component.advisory)

            observation = Observation(
                title=title,
                description=summary,
                recommendation=self._get_recommendation(vc_component.advisory),
                cvss3_vector=cvss3_vector,
                cvss4_vector=cvss4_vector,
                vulnerability_id=title,
                vulnerability_id_aliases=self._get_aliases(vc_component.advisory, title),
                origin_component_name=vc_component.component.component_name,
                origin_component_version=vc_component.component.component_version,
                origin_component_type=vc_component.component.component_type,
                origin_component_purl=vc_component.component.component_purl,
                origin_component_cpe=vc_component.component.component_cpe,
                origin_component_cyclonedx_bom_link=vc_component.component.component_cyclonedx_bom_link,  # noqa: E501 pylint: disable=line-too-long
                origin_component_dependencies=vc_component.component.component_dependencies,
            )
            observations.append(observation)

            observation.unsaved_references = self._get_references(vc_component.advisory)

            evidence = []
            evidence.append("Advisory")
            evidence.append(dumps(vc_component.advisory))
            observation.unsaved_evidences.append(evidence)

        return observations, self.get_name()

    def _get_title(self, advisory: dict) -> str:
        title = ""

        advisory_uid = advisory.get("advisory_uid") or ""
        if "/" in advisory_uid:
            title = advisory_uid.rsplit("/", 1)[-1]

        aliases = advisory.get("aliases") or []
        cve_aliases = [alias for alias in aliases if alias.startswith("CVE")]
        if len(cve_aliases) == 1:
            title = cve_aliases[0]

        if not title and aliases:
            title = aliases[0]

        return title or "No title"

    def _get_aliases(self, advisory: dict, title: str) -> str:
        aliases = []

        for alias in advisory.get("aliases", []):
            if alias != title:
                aliases.append(alias)

        return ", ".join(aliases) if aliases else ""

    def _get_severities(self, advisory: dict) -> Tuple[str, str]:
        cvss3 = ""
        cvss4 = ""

        for severity in advisory.get("severities", []):
            vector = severity.get("scoring_elements", "")
            cvss3 = vector if vector.startswith("CVSS:3") and not cvss3 else cvss3
            cvss4 = vector if vector.startswith("CVSS:4") and not cvss4 else cvss4

        return cvss3, cvss4

    def _get_recommendation(self, advisory: dict) -> str:
        recommendations = []

        fixed_by_packages = advisory.get("fixed_by_packages")
        fixed_by_packages = fixed_by_packages if isinstance(fixed_by_packages, list) else ""
        for fixed_by_package in fixed_by_packages:
            try:
                parsed_purl = PackageURL.from_string(fixed_by_package)
                recommendation = parsed_purl.version if parsed_purl.version else f"`{fixed_by_package}`"
                recommendations.append(recommendation)
            except ValueError:
                recommendations.append(f"`{fixed_by_package}`")

        version_string = "version" if len(recommendations) == 1 else "versions"
        return f"Update to {version_string} {", ".join(recommendations)}" if recommendations else ""

    def _get_references(self, advisory: dict) -> list:
        references = []

        if advisory.get("url"):
            references.append(advisory.get("url"))
        for reference in advisory.get("references", []):
            if reference.get("url"):
                references.append(reference.get("url"))

        return references
