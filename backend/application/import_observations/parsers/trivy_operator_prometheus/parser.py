import json
from dataclasses import dataclass
from typing import Any, Optional

import requests

from application.commons.services.connection_error import get_connection_error_message
from application.core.models import Branch, Observation, Product
from application.core.types import Severity
from application.import_observations.models import Api_Configuration
from application.import_observations.parsers.base_parser import (
    BaseAPIParser,
    BaseParser,
)
from application.import_observations.types import Parser_Type


@dataclass
class KubernetesResource:
    namespace: str
    resource_kind: str
    resource_name: str


class TrivyOperatorPrometheus(BaseParser, BaseAPIParser):
    def __init__(self) -> None:
        self.api_configuration: Optional[Api_Configuration] = None

    @classmethod
    def get_name(cls) -> str:
        return "Trivy Operator Prometheus"

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_OTHER

    def check_connection(self, api_configuration: Api_Configuration) -> tuple[bool, list[str], dict]:
        self.api_configuration = api_configuration

        trivy_operator_prometheus_base_url = api_configuration.base_url
        trivy_operator_prometheus_query = api_configuration.query
        trivy_operator_prometheus_verify_ssl = api_configuration.verify_ssl
        trivy_operator_prometheus_basic_auth = api_configuration.basic_auth_enabled
        trivy_operator_prometheus_basic_auth_username = api_configuration.basic_auth_username
        trivy_operator_prometheus_basic_auth_password = api_configuration.basic_auth_password

        if not trivy_operator_prometheus_base_url.endswith("/"):
            trivy_operator_prometheus_base_url += "/"

        trivy_operator_prometheus_url = (
            trivy_operator_prometheus_base_url + "api/v1/query?query=" + trivy_operator_prometheus_query
        )

        trivy_basic_auth_param = None
        if trivy_operator_prometheus_basic_auth:
            trivy_basic_auth_param = (
                trivy_operator_prometheus_basic_auth_username,
                trivy_operator_prometheus_basic_auth_password,
            )

        try:
            response = requests.get(
                trivy_operator_prometheus_url,
                timeout=60,
                verify=trivy_operator_prometheus_verify_ssl,
                auth=trivy_basic_auth_param,
                allow_redirects=False,
            )
            response.raise_for_status()
        except Exception as e:
            return False, [get_connection_error_message("Cannot access Prometheus", e)], {}

        return True, [], response.json()

    def check_format(self, import_data: Any) -> tuple[bool, list[str], dict]:
        try:
            data = json.load(import_data)
        except Exception:
            return False, ["Data is not valid JSON"], {}

        if not data.get("status") == "success":
            return False, ["Data is not a Prometheus API-Endpoint"], {}

        if not isinstance(data.get("data"), dict) or not isinstance(data.get("data").get("result"), list):
            return False, ["Data not in valid Prometheus-Metric Format"], {}

        return True, [], data

    def get_observations(self, data: dict, product: Product, branch: Optional[Branch]) -> tuple[list[Observation], str]:
        observations = []
        for finding in data.get("data", {}).get("result"):
            if (
                finding.get("metric", {}).get("__name__", "") == "trivy_compliance_info"
                and finding.get("metric", {}).get("status", "") == "Fail"
            ):
                observation = self._create_compliance_observation(finding)
            elif (
                finding.get("metric", {}).get("__name__", "") == "trivy_configaudits_info"
                and finding.get("metric", {}).get("config_audit_success", "") == "false"
            ):
                observation = self._create_config_audit_observation(finding)
            elif finding.get("metric", {}).get("__name__", "") == "trivy_exposedsecrets_info":
                observation = self._create_exposedsecrets_observation(finding)
            elif (
                finding.get("metric", {}).get("__name__", "") == "trivy_rbacassessments_info"
                and finding.get("metric", {}).get("rbac_assessment_success", "") == "false"
            ):
                observation = self._create_rbac_assessment_observation(finding)
            elif finding.get("metric", {}).get("__name__", "") == "trivy_vulnerability_id":
                observation = self._create_vulnerability_observation(finding)
            else:
                continue

            kubernetes_resource = self._get_kubernetes_resource(finding)
            observation.origin_kubernetes_namespace = kubernetes_resource.namespace
            observation.origin_kubernetes_resource_type = kubernetes_resource.resource_kind

            if (
                finding.get("metric", {}).get("__name__", "") == "trivy_rbacassessments_info"
                and not kubernetes_resource.resource_name
            ):
                kubernetes_resource.resource_name = finding.get("metric", {}).get("name", "")

            observation.origin_kubernetes_resource_name = kubernetes_resource.resource_name

            observation.scanner = "Trivy Operator"

            evidence = []
            evidence.append("Vulnerability")
            evidence.append(json.dumps(finding))
            observation.unsaved_evidences.append(evidence)

            observations.append(observation)

        return observations, self.get_name()

    def _create_compliance_observation(self, finding: dict) -> Observation:
        title = finding.get("metric", {}).get("title", "")
        compliance_name = finding.get("metric", {}).get("compliance_name", "")
        compliance_id = finding.get("metric", {}).get("compliance_id", "")
        description = finding.get("metric", {}).get("description", "")
        severity = finding.get("metric", {}).get("severity", Severity.SEVERITY_UNKNOWN)

        return Observation(
            title=f"{title} / {compliance_name}",
            parser_severity=self._get_severity(severity),
            description=self._get_description(description=description, audit_id=compliance_id),
        )

    def _create_config_audit_observation(self, finding: dict) -> Observation:
        config_audit_title = finding.get("metric", {}).get("config_audit_title", "")
        config_audit_description = finding.get("metric", {}).get("config_audit_description", "")
        config_audit_id = finding.get("metric", {}).get("config_audit_id", "")
        severity = finding.get("metric", {}).get("severity", Severity.SEVERITY_UNKNOWN)

        return Observation(
            title=config_audit_title,
            parser_severity=self._get_severity(severity),
            description=self._get_description(description=config_audit_description, audit_id=config_audit_id),
        )

    def _create_exposedsecrets_observation(self, finding: dict) -> Observation:
        image_registry = finding.get("metric", {}).get("image_registry", "")
        image_repository = finding.get("metric", {}).get("image_repository", "")
        image_tag = finding.get("metric", {}).get("image_tag", "")
        secret_target = finding.get("metric", {}).get("secret_target", "")
        secret_title = finding.get("metric", {}).get("secret_title", "")
        severity = finding.get("metric", {}).get("severity", Severity.SEVERITY_UNKNOWN)

        return Observation(
            title=secret_title,
            parser_severity=self._get_severity(severity),
            origin_docker_image_name=f"{image_registry}/{image_repository}",
            origin_docker_image_tag=image_tag,
            origin_source_file=secret_target,
        )

    def _create_rbac_assessment_observation(self, finding: dict) -> Observation:
        rbac_assessment_title = finding.get("metric", {}).get("rbac_assessment_title", "")
        rbac_assessment_description = finding.get("metric", {}).get("rbac_assessment_description", "")
        rbac_assessment_id = finding.get("metric", {}).get("rbac_assessment_id", "")
        severity = finding.get("metric", {}).get("severity", Severity.SEVERITY_UNKNOWN)

        return Observation(
            title=rbac_assessment_title,
            parser_severity=self._get_severity(severity),
            description=self._get_description(description=rbac_assessment_description, audit_id=rbac_assessment_id),
        )

    def _create_vulnerability_observation(self, finding: dict) -> Observation:
        origin_component_name = finding.get("metric", {}).get("resource", "")
        vuln_title = finding.get("metric", {}).get("vuln_title", "")
        vulnerability_id = finding.get("metric", {}).get("vuln_id", "")
        cvss3_score = finding.get("metric", {}).get("vuln_score")
        severity = finding.get("metric", {}).get("severity", Severity.SEVERITY_UNKNOWN)
        origin_docker_image_registry = finding.get("metric", {}).get("image_registry", "")
        origin_docker_image_repository = finding.get("metric", {}).get("image_repository", "")
        origin_docker_image_name = origin_docker_image_registry + "/" + origin_docker_image_repository
        origin_docker_image_tag = finding.get("metric", {}).get("image_tag", "")
        fixed_version = finding.get("metric", {}).get("fixed_version", "")
        origin_component_version = finding.get("metric", {}).get("installed_version", "")

        return Observation(
            title=vulnerability_id,
            parser_severity=self._get_severity(severity),
            numerical_severity=cvss3_score,
            vulnerability_id=vulnerability_id,
            origin_docker_image_name=origin_docker_image_name,
            origin_docker_image_tag=origin_docker_image_tag,
            cvss3_score=cvss3_score,
            origin_component_name=origin_component_name,
            origin_component_version=origin_component_version,
            recommendation=self._get_vulnerability_recommendation(fixed_version, origin_component_version),
            description=self._get_description(description=vuln_title),
        )

    def _get_vulnerability_recommendation(
        self,
        fixed_version: str,
        origin_component_version: str,
    ) -> str:
        recommendation = ""
        if fixed_version:
            recommendation += f"Upgrade from **{origin_component_version}** to **{fixed_version}**"

        return recommendation

    def _get_description(
        self,
        description: str,
        audit_id: Optional[str] = None,
    ) -> str:
        if audit_id:
            if audit_id.upper().startswith("KSV"):
                description += (
                    f"\n\n**Assessment ID:** [{audit_id}]"
                    + f"(https://avd.aquasec.com/misconfig/kubernetes/{audit_id.lower()})"
                )
            else:
                description += f"\n\n**Assessment ID:** {audit_id}"

        prometheus_endpoint_url = (
            self.api_configuration.base_url if isinstance(self.api_configuration, Api_Configuration) else ""
        )
        if prometheus_endpoint_url:
            description += f"\n\n**Prometheus host:** {prometheus_endpoint_url}"

        return description

    def _get_severity(self, severity: str) -> str:
        if (
            severity.capitalize(),
            severity.capitalize(),
        ) in Severity.SEVERITY_CHOICES:
            return severity.capitalize()

        return Severity.SEVERITY_UNKNOWN

    def _get_kubernetes_resource(self, finding: dict) -> KubernetesResource:
        return KubernetesResource(
            namespace=finding.get("metric", {}).get("namespace", ""),
            resource_kind=finding.get("metric", {}).get("resource_kind", ""),
            resource_name=finding.get("metric", {}).get("resource_name", ""),
        )
