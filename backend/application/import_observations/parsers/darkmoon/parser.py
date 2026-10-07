from json import dumps
from typing import Any, Optional

from cvss import CVSS3, CVSS4, CVSSError

from application.core.models import Branch, Observation, Product
from application.core.types import Severity
from application.import_observations.parsers.base_parser import (
    BaseFileParser,
    BaseParser,
)
from application.import_observations.types import Parser_Filetype, Parser_Type

SEVERITIES = {
    "critical": Severity.SEVERITY_CRITICAL,
    "high": Severity.SEVERITY_HIGH,
    "medium": Severity.SEVERITY_MEDIUM,
    "low": Severity.SEVERITY_LOW,
    "info": Severity.SEVERITY_NONE,
    "informational": Severity.SEVERITY_NONE,
}

# Darkmoon labels every finding with the outcome of its exploitation attempt
EXPLOITATION_STATUSES = ["exploited", "confirmed", "unconfirmed"]

MAX_TITLE_LENGTH = 255


class DarkmoonParser(BaseParser, BaseFileParser):
    """
    Parser for the JSON findings of Darkmoon, an open source autonomous AI
    penetration testing platform (https://github.com/ASCIT31/Dark-Moon).

    The file is either a list of findings or an object with a "findings" list.
    """

    @classmethod
    def get_name(cls) -> str:
        return "Darkmoon"

    @classmethod
    def get_filetype(cls) -> str:
        return Parser_Filetype.FILETYPE_JSON

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_DAST

    def check_format(self, data: Any) -> bool:
        findings = self._get_findings(data)
        if not findings:
            return False

        # "discovered_by_agent" and the exploitation "status" are specific to Darkmoon
        for finding in findings:
            if not (
                isinstance(finding, dict)
                and finding.get("title")
                and finding.get("discovered_by_agent")
                and str(finding.get("status", "")).lower() in EXPLOITATION_STATUSES
            ):
                return False

        return True

    def get_observations(  # pylint: disable=too-many-locals
        self, data: Any, product: Product, branch: Optional[Branch]
    ) -> tuple[list[Observation], str]:
        observations = []

        for finding in self._get_findings(data):
            status = str(finding.get("status", "")).lower()

            cvss3_vector, cvss4_vector = self._get_cvss_vectors(finding.get("cvss_vector"))

            observation = Observation(
                title=str(finding.get("title"))[:MAX_TITLE_LENGTH],
                description=self._get_description(finding, status, bool(cvss3_vector or cvss4_vector)),
                recommendation=finding.get("remediation") or "",
                parser_severity=SEVERITIES.get(str(finding.get("severity", "")).lower(), Severity.SEVERITY_UNKNOWN),
                origin_endpoint_url=finding.get("endpoint") or "",
                vulnerability_id=finding.get("cve") or "",
                cvss3_vector=cvss3_vector,
                cvss4_vector=cvss4_vector,
                scanner=self.get_name(),
            )

            self._add_references(finding, observation)
            self._add_evidences(finding, observation)

            observations.append(observation)

        return observations, self.get_name()

    def _get_findings(self, data: Any) -> list:
        if isinstance(data, dict):
            data = data.get("findings")
        if isinstance(data, list):
            return data
        return []

    def _get_cvss_vectors(self, cvss_vector: Optional[str]) -> tuple[str, str]:
        cvss3_vector = ""
        cvss4_vector = ""

        if cvss_vector and isinstance(cvss_vector, str):
            try:
                if cvss_vector.startswith("CVSS:4.0/"):
                    CVSS4(cvss_vector)
                    cvss4_vector = cvss_vector
                elif cvss_vector.startswith("CVSS:3"):
                    CVSS3(cvss_vector)
                    cvss3_vector = cvss_vector
            except CVSSError:
                pass

        return cvss3_vector, cvss4_vector

    def _get_description(self, finding: dict, status: str, has_cvss_vector: bool) -> str:
        description = finding.get("description") or ""

        description += f"\n\n**Exploitation status:** {status.capitalize()}"
        if status == "exploited":
            description += " (proven with a working exploit)"

        if finding.get("category"):
            description += f"\n\n**Category:** {finding.get('category')}"
        if finding.get("discovered_by_agent"):
            description += f"\n\n**Discovered by agent:** {finding.get('discovered_by_agent')}"
        if finding.get("plugin_or_component"):
            description += f"\n\n**Plugin or component:** {finding.get('plugin_or_component')}"

        if not has_cvss_vector and finding.get("cvss_score") is not None:
            description += f"\n\n**CVSS score:** {finding.get('cvss_score')}"

        if finding.get("mitre_attack_id"):
            mitre = str(finding.get("mitre_attack_id"))
            if finding.get("mitre_attack_name"):
                mitre += f" ({finding.get('mitre_attack_name')})"
            description += f"\n\n**MITRE ATT&CK:** {mitre}"
        if finding.get("iso27001_control"):
            description += f"\n\n**ISO 27001 control:** {finding.get('iso27001_control')}"

        if finding.get("evidence_explanation"):
            description += f"\n\n**Evidence:** {finding.get('evidence_explanation')}"

        return description.strip()

    def _add_references(self, finding: dict, observation: Observation) -> None:
        cve = finding.get("cve")
        if cve:
            observation.unsaved_references.append(f"https://nvd.nist.gov/vuln/detail/{cve}")

        mitre_attack_id = finding.get("mitre_attack_id")
        if mitre_attack_id:
            observation.unsaved_references.append(
                f"https://attack.mitre.org/techniques/{str(mitre_attack_id).replace('.', '/')}/"
            )

    def _add_evidences(self, finding: dict, observation: Observation) -> None:
        commands = finding.get("evidence_commands")
        if commands:
            if isinstance(commands, list):
                commands = "\n".join(str(command) for command in commands)
            observation.unsaved_evidences.append(["Commands", str(commands)])

        if finding.get("evidence_logs"):
            observation.unsaved_evidences.append(["Logs", str(finding.get("evidence_logs"))])

        if finding.get("raw_request"):
            observation.unsaved_evidences.append(["Request", str(finding.get("raw_request"))])

        if finding.get("raw_response"):
            observation.unsaved_evidences.append(["Response", str(finding.get("raw_response"))])

        if not observation.unsaved_evidences:
            observation.unsaved_evidences.append(["Finding", dumps(finding)])
