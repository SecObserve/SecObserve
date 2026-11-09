from typing import Optional

from django.db.models import QuerySet
from django.http import HttpResponse
from openpyxl import Workbook

from application.commons.services.export import export_csv, export_excel
from application.core.models import Product
from application.metrics.models import Product_Metrics
from application.metrics.queries.product_metrics import get_product_metrics


def export_product_metrics_excel(product: Optional[Product]) -> Workbook:
    product_metrics = _get_product_metrics(product)
    return export_excel(product_metrics, "Product Metrics", _get_excludes(), _get_foreign_keys())


def export_product_metrics_csv(response: HttpResponse, product: Optional[Product]) -> None:
    product_metrics = _get_product_metrics(product)
    return export_csv(
        response,
        product_metrics,
        _get_excludes(),
        _get_foreign_keys(),
    )


def _get_product_metrics(product: Optional[Product]) -> QuerySet[Product_Metrics]:
    product_metrics = get_product_metrics()
    if product:
        if product.is_product_group:
            product_metrics = product_metrics.filter(product__product_group=product)
        else:
            product_metrics = product_metrics.filter(product=product)
    product_metrics = product_metrics.order_by("product__name", "date")
    return product_metrics


def _get_excludes() -> list[str]:
    return [
        "id",
        "pk",
        "objects",
        "last_observation_change",
    ]


def _get_foreign_keys() -> list[str]:
    return ["product"]
