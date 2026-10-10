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

# has_active_observations, has_inactive_observations and has_licenses are annotated in get_components()
COLUMNS = [
    ExportColumn("Active observations", "has_active_observations", 12),
    ExportColumn("Component URL", "component_url", 20),
    ExportColumn("Ecosystem", "purl_type", 12),
    ExportColumn("Inactive observations", "has_inactive_observations", 12),
    ExportColumn("Licenses", "has_licenses", 12),
    ExportColumn("Name", "name", 30),
    ExportColumn("Namespace", "purl_namespace", 20),
    ExportColumn("PURL", "purl", 40),
    ExportColumn("Type", "type", 12),
    ExportColumn("Version", "version", 20),
]


def export_components_excel(components: QuerySet) -> Workbook:
    return export_excel_columns(_get_rows(components), "Components", COLUMNS)


def export_components_csv(response: HttpResponse, components: QuerySet) -> None:
    export_csv_columns(response, _get_rows(components), COLUMNS)


def _get_rows(components: QuerySet) -> Iterator[tuple]:
    components = components.annotate(component_url=frontend_url(get_base_url_frontend(), "components", "pk"))
    return components.values_list(*[column.field for column in COLUMNS]).iterator(chunk_size=2000)
