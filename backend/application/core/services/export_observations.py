from typing import Iterator, Optional

from django.db.models import CharField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Cast, Concat
from django.db.models.query import QuerySet
from django.http import HttpResponse
from openpyxl import Workbook

from application.commons.services.export import (
    ExportColumn,
    export_csv_columns,
    export_excel_columns,
)
from application.commons.services.functions import get_base_url_frontend
from application.core.models import Observation, Observation_Log, Product
from application.core.types import Observation_Log_Comment

# The first columns identify an observation and show its current assessment, the columns that
# explain how the current values came about and the details of the origins follow at the end.
COLUMNS = [
    ExportColumn("ID", "id", 10),
    ExportColumn("Observation URL", "observation_url", 20),
    ExportColumn("Product group", "product__product_group__name", 25),
    ExportColumn("Product", "product__name", 25),
    ExportColumn("Product URL", "product_url", 20),
    ExportColumn("Branch / Version", "branch__name", 20),
    ExportColumn("Service", "origin_service__name", 20),
    ExportColumn("Title", "title", 50),
    ExportColumn("Vulnerability ID", "vulnerability_id", 20),
    ExportColumn("Vulnerability ID aliases", "vulnerability_id_aliases", 20),
    ExportColumn("Severity", "current_severity", 12),
    ExportColumn("Status", "current_status", 14),
    ExportColumn("Priority", "current_priority", 10),
    ExportColumn("VEX justification", "current_vex_justification", 20),
    ExportColumn("VEX remediations", "current_vex_remediations", 20),
    ExportColumn("Risk acceptance expiry date", "risk_acceptance_expiry_date", 14),
    ExportColumn("Assessment comment", "observation_log_comment", 40),
    ExportColumn("CVSS 4 score", "cvss4_score", 10),
    ExportColumn("CVSS 3 score", "cvss3_score", 10),
    ExportColumn("EPSS score (%)", "epss_score", 10),
    ExportColumn("EPSS percentile (%)", "epss_percentile", 10),
    ExportColumn("CWE", "cwe", 10),
    ExportColumn("Fix available", "fix_available", 10),
    ExportColumn("Update impact score", "update_impact_score", 10),
    ExportColumn("Has potential duplicates", "has_potential_duplicates", 10),
    ExportColumn("Component", "origin_component_name_version", 30),
    ExportColumn("Component PURL", "origin_component_purl", 30),
    ExportColumn("Component type", "origin_component_type", 14),
    ExportColumn("Container", "origin_docker_image_name_tag", 30),
    ExportColumn("Docker image digest", "origin_docker_image_digest", 20),
    ExportColumn("Endpoint URL", "origin_endpoint_url", 30),
    ExportColumn("Source file", "origin_source_file", 30),
    ExportColumn("Source line start", "origin_source_line_start", 10),
    ExportColumn("Source line end", "origin_source_line_end", 10),
    ExportColumn("Source file link", "origin_source_file_link", 30),
    ExportColumn("Cloud resource", "origin_cloud_qualified_resource", 30),
    ExportColumn("Kubernetes resource", "origin_kubernetes_qualified_resource", 30),
    ExportColumn("Scanner", "scanner", 20),
    ExportColumn("Parser", "parser__name", 20),
    ExportColumn("Scanner observation ID", "scanner_observation_id", 20),
    ExportColumn("Upload filename", "upload_filename", 20),
    ExportColumn("API configuration", "api_configuration_name", 20),
    ExportColumn("Found", "found", 12),
    ExportColumn("Created", "created", 20),
    ExportColumn("Last seen", "import_last_seen", 20),
    ExportColumn("Last change", "last_observation_log", 20),
    ExportColumn("Modified", "modified", 20),
    ExportColumn("Description", "description", 60),
    ExportColumn("Recommendation", "recommendation", 60),
    ExportColumn("CVSS 4 vector", "cvss4_vector", 30),
    ExportColumn("CVSS 3 vector", "cvss3_vector", 30),
    ExportColumn("CVE found in", "cve_found_in", 20),
    ExportColumn("Parser severity", "parser_severity", 12),
    ExportColumn("Fields rule severity", "rule_severity", 12),
    ExportColumn("Rego rule severity", "rule_rego_severity", 12),
    ExportColumn("Assessment severity", "assessment_severity", 12),
    ExportColumn("Parser status", "parser_status", 14),
    ExportColumn("VEX status", "vex_status", 14),
    ExportColumn("Fields rule status", "rule_status", 14),
    ExportColumn("Rego rule status", "rule_rego_status", 14),
    ExportColumn("Assessment status", "assessment_status", 14),
    ExportColumn("Fields rule priority", "rule_priority", 10),
    ExportColumn("Rego rule priority", "rule_rego_priority", 10),
    ExportColumn("Assessment priority", "assessment_priority", 10),
    ExportColumn("Parser VEX justification", "parser_vex_justification", 20),
    ExportColumn("VEX statement VEX justification", "vex_vex_justification", 20),
    ExportColumn("Fields rule VEX justification", "rule_vex_justification", 20),
    ExportColumn("Rego rule VEX justification", "rule_rego_vex_justification", 20),
    ExportColumn("Assessment VEX justification", "assessment_vex_justification", 20),
    ExportColumn("VEX statement VEX remediations", "vex_vex_remediations", 20),
    ExportColumn("Fields rule VEX remediations", "rule_vex_remediations", 20),
    ExportColumn("Rego rule VEX remediations", "rule_rego_vex_remediations", 20),
    ExportColumn("Assessment VEX remediations", "assessment_vex_remediations", 20),
    ExportColumn("General fields rule", "general_rule__name", 20),
    ExportColumn("General Rego rule", "general_rule_rego__name", 20),
    ExportColumn("Product fields rule", "product_rule__name", 20),
    ExportColumn("Product Rego rule", "product_rule_rego__name", 20),
    ExportColumn("VEX document", "vex_statement__document__document_id", 20),
    ExportColumn("Component name", "origin_component_name", 20),
    ExportColumn("Component version", "origin_component_version", 14),
    ExportColumn("Component ecosystem", "origin_component_purl_type", 12),
    ExportColumn("Component CPE", "origin_component_cpe", 20),
    ExportColumn("Component dependencies", "origin_component_dependencies", 30),
    ExportColumn("Component CycloneDX BOM link", "origin_component_cyclonedx_bom_link", 30),
    ExportColumn("Docker image name", "origin_docker_image_name", 20),
    ExportColumn("Docker image tag", "origin_docker_image_tag", 14),
    ExportColumn("Container (short)", "origin_docker_image_name_tag_short", 20),
    ExportColumn("Endpoint scheme", "origin_endpoint_scheme", 10),
    ExportColumn("Endpoint host", "origin_endpoint_hostname", 20),
    ExportColumn("Endpoint port", "origin_endpoint_port", 10),
    ExportColumn("Endpoint path", "origin_endpoint_path", 20),
    ExportColumn("Endpoint params", "origin_endpoint_params", 20),
    ExportColumn("Endpoint query", "origin_endpoint_query", 20),
    ExportColumn("Endpoint fragment", "origin_endpoint_fragment", 20),
    ExportColumn("Cloud provider", "origin_cloud_provider", 14),
    ExportColumn("Cloud account / subscription / project", "origin_cloud_account_subscription_project", 20),
    ExportColumn("Cloud resource name", "origin_cloud_resource", 20),
    ExportColumn("Cloud resource type", "origin_cloud_resource_type", 20),
    ExportColumn("Kubernetes cluster", "origin_kubernetes_cluster", 20),
    ExportColumn("Kubernetes namespace", "origin_kubernetes_namespace", 20),
    ExportColumn("Kubernetes resource type", "origin_kubernetes_resource_type", 20),
    ExportColumn("Kubernetes resource name", "origin_kubernetes_resource_name", 20),
    ExportColumn("Issue tracker issue ID", "issue_tracker_issue_id", 20),
    ExportColumn("Issue tracker issue closed", "issue_tracker_issue_closed", 10),
    ExportColumn("Jira initial status", "issue_tracker_jira_initial_status", 20),
]

# Model fields that are deliberately not exported
EXCLUDED_FIELDS = ["identity_hash", "numerical_severity", "origin_component"]


def export_observations_excel(observations: QuerySet) -> Workbook:
    return export_excel_columns(_get_rows(observations), "Observations", COLUMNS)


def export_observations_excel_for_product(product: Product, status: Optional[list[str]]) -> Workbook:
    return export_observations_excel(_get_observations(product, status))


def export_observations_csv(response: HttpResponse, observations: QuerySet) -> None:
    export_csv_columns(response, _get_rows(observations), COLUMNS)


def export_observations_csv_for_product(response: HttpResponse, product: Product, status: Optional[list[str]]) -> None:
    export_observations_csv(response, _get_observations(product, status))


def _get_rows(observations: QuerySet) -> Iterator[tuple]:
    base_url_frontend = get_base_url_frontend()
    observations = observations.annotate(
        observation_log_comment=_newest_comment(),
        observation_url=_frontend_url(base_url_frontend, "observations", "pk"),
        product_url=_frontend_url(base_url_frontend, "products", "product_id"),
    )
    # One query with joins instead of loading the related objects row by row
    return observations.values_list(*[column.field for column in COLUMNS]).iterator(chunk_size=2000)


def _newest_comment() -> Subquery:
    return Subquery(
        Observation_Log.objects.filter(observation=OuterRef("pk"))
        .filter(~Q(severity="") | ~Q(status=""))
        .filter(Q(severity="") | Q(severity=OuterRef("current_severity")))
        .filter(Q(status="") | Q(status=OuterRef("current_status")))
        .exclude(comment__in=Observation_Log_Comment.AUTOMATED_COMMENTS)
        .order_by("-created", "-id")
        .values("comment")[:1]
    )


def _frontend_url(base_url_frontend: str, route: str, id_field: str) -> Concat:
    return Concat(
        Value(f"{base_url_frontend}#/{route}/"),
        Cast(id_field, output_field=CharField()),
        Value("/show"),
        output_field=CharField(),
    )


def _get_observations(product: Product, status: Optional[list[str]]) -> QuerySet:
    if product.is_product_group:
        observations = Observation.objects.filter(product__product_group=product)
    else:
        observations = Observation.objects.filter(product=product)

    if status:
        observations = observations.filter(current_status__in=status)

    return observations.order_by("product__name", "branch__name", "numerical_severity", "title", "id")
