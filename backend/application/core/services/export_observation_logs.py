from typing import Iterator

from django.db.models.query import QuerySet
from django.http import HttpResponse
from openpyxl import Workbook

from application.commons.services.export import (
    ExportColumn,
    export_csv_columns,
    export_excel_columns,
    frontend_url,
)
from application.commons.services.functions import get_base_url_frontend

COLUMNS = [
    ExportColumn("ID", "id", 10),
    ExportColumn("Assessment URL", "observation_log_url", 20),
    ExportColumn("Product group", "observation__product__product_group__name", 25),
    ExportColumn("Product", "observation__product__name", 25),
    ExportColumn("Branch / Version", "observation__branch__name", 20),
    ExportColumn("Service", "observation__origin_service__name", 20),
    ExportColumn("Observation", "observation__title", 50),
    ExportColumn("Observation URL", "observation_url", 20),
    ExportColumn("Component", "observation__origin_component_name_version", 30),
    ExportColumn("User", "user__full_name", 20),
    ExportColumn("Severity", "severity", 12),
    ExportColumn("Status", "status", 14),
    ExportColumn("Priority", "priority", 10),
    ExportColumn("VEX justification", "vex_justification", 20),
    ExportColumn("VEX remediations", "vex_remediations", 20),
    ExportColumn("Risk acceptance expiry date", "risk_acceptance_expiry_date", 14),
    ExportColumn("Comment", "comment", 60),
    ExportColumn("Created", "created", 20),
    ExportColumn("Assessment status", "assessment_status", 14),
    ExportColumn("Approver", "approval_user__full_name", 20),
    ExportColumn("Approval date", "approval_date", 20),
    ExportColumn("Rejection remark", "rejection_remark", 40),
    ExportColumn("Values of the assessor", "assessor_values", 40),
]
# Alphabetical, like the export of the observations
COLUMNS.sort(key=lambda column: column.header.casefold())


def export_observation_logs_excel(observation_logs: QuerySet) -> Workbook:
    return export_excel_columns(_get_rows(observation_logs), "Assessments", COLUMNS)


def export_observation_logs_csv(response: HttpResponse, observation_logs: QuerySet) -> None:
    export_csv_columns(response, _get_rows(observation_logs), COLUMNS)


def _get_rows(observation_logs: QuerySet) -> Iterator[tuple]:
    base_url_frontend = get_base_url_frontend()
    observation_logs = observation_logs.annotate(
        observation_log_url=frontend_url(base_url_frontend, "observation_logs", "pk"),
        observation_url=frontend_url(base_url_frontend, "observations", "observation_id"),
    )
    return observation_logs.values_list(*[column.field for column in COLUMNS]).iterator(chunk_size=2000)
