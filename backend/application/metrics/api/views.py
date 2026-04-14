import csv
from tempfile import NamedTemporaryFile
from typing import Optional

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.core.models import Product
from application.core.queries.product import get_product_by_id
from application.core.types import Severity
from application.metrics.api.serializers import (
    ProductMetricsSerializer,
    ProductMetricsStatusSerializer,
)
from application.metrics.models import Product_Metrics_Status
from application.metrics.services.export_metrics import (
    export_product_metrics_csv,
    export_product_metrics_excel,
)
from application.metrics.services.metrics import (
    get_codecharta_metrics,
    get_product_metrics_current,
    get_product_metrics_timeline,
)


class ProductMetricsTimelineView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: dict},
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> Response:
        product = _get_and_check_product(request)
        age = request.query_params.get("age", "")
        return Response(get_product_metrics_timeline(product, age))


class ProductMetricsCurrentView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: ProductMetricsSerializer},
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> Response:
        product = _get_and_check_product(request)
        return Response(get_product_metrics_current(product))


class ProductMetricsExportExcelView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={
            (HTTP_200_OK, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"): OpenApiTypes.BINARY
        },
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> HttpResponse:
        product = _get_and_check_product(request)

        workbook = export_product_metrics_excel(product)

        with NamedTemporaryFile() as tmp:
            workbook.save(tmp.name)  # nosemgrep: python.lang.correctness.tempfile.flush.tempfile-without-flush
            # export works fine without .flush()
            tmp.seek(0)
            stream = tmp.read()

        response = HttpResponse(
            content=stream,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = "attachment; filename=product_metrics.xlsx"

        return response


class ProductMetricsExportCsvView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={(HTTP_200_OK, "text/csv"): OpenApiTypes.BINARY},
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> HttpResponse:
        product = _get_and_check_product(request)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=product_metrics.csv"

        export_product_metrics_csv(response, product)

        return response


class ProductMetricsExportCodeChartaView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={(HTTP_200_OK, "text/csv"): OpenApiTypes.BINARY},
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> HttpResponse:
        product = _get_and_check_product(request)
        if not product:
            raise ValidationError("Product not found")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="secobserve_codecharta_metrics.csv"'

        writer = csv.DictWriter(
            response,
            fieldnames=[
                "source_file",
                "Vulnerabilities_Total".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_CRITICAL}".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_HIGH}".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_MEDIUM}".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_LOW}".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_NONE}".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_UNKNOWN}".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_HIGH}_and_above".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_MEDIUM}_and_above".lower(),
                f"Vulnerabilities_{Severity.SEVERITY_LOW}_and_above".lower(),
            ],
        )
        writer.writeheader()
        for row in get_codecharta_metrics(product):
            writer.writerow(row)

        return response


class ProductMetricsStatusView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: ProductMetricsStatusSerializer},
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> Response:
        settings = Settings.load()

        status = Product_Metrics_Status.load()
        return Response(
            {
                "last_calculated": status.last_calculated,
                "calculation_interval": settings.background_product_metrics_interval_minutes,
            }
        )


def _get_and_check_product(request: Request) -> Optional[Product]:
    product_id = request.query_params.get("product_id")
    if product_id and not product_id.isdigit():
        raise ValidationError("product_id must be a number")
    if product_id:
        product = get_product_by_id(int(product_id))
    else:
        product = None
    if product:
        user_has_permission_or_403(product, Permissions.Product_View)
    return product
