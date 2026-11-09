from datetime import date, datetime, timedelta
from itertools import batched
from typing import Optional, TypeVar

from django.db.models import Count, F, OuterRef, Q, Subquery, Sum
from django.utils import timezone

from application.commons.models import Settings
from application.core.models import Observation, Product
from application.core.types import Severity, Status
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from application.metrics.models import (
    Product_License_Metrics,
    Product_Metrics,
    Product_Metrics_Status,
)
from application.metrics.queries.product_metrics import (
    get_latest_product_metrics,
    get_product_metrics,
)
from application.metrics.services.age import get_days

OBSERVATION_COUNTS = {
    "active_critical": Count(
        "pk", filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_CRITICAL)
    ),
    "active_high": Count(
        "pk", filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_HIGH)
    ),
    "active_medium": Count(
        "pk", filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_MEDIUM)
    ),
    "active_low": Count(
        "pk", filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_LOW)
    ),
    "active_none": Count(
        "pk", filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_NONE)
    ),
    "active_unknown": Count(
        "pk", filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_UNKNOWN)
    ),
    "open": Count("pk", filter=Q(current_status=Status.STATUS_OPEN)),
    "affected": Count("pk", filter=Q(current_status=Status.STATUS_AFFECTED)),
    "resolved": Count("pk", filter=Q(current_status=Status.STATUS_RESOLVED)),
    "duplicate": Count("pk", filter=Q(current_status=Status.STATUS_DUPLICATE)),
    "false_positive": Count("pk", filter=Q(current_status=Status.STATUS_FALSE_POSITIVE)),
    "in_review": Count("pk", filter=Q(current_status=Status.STATUS_IN_REVIEW)),
    "not_affected": Count("pk", filter=Q(current_status=Status.STATUS_NOT_AFFECTED)),
    "not_security": Count("pk", filter=Q(current_status=Status.STATUS_NOT_SECURITY)),
    "risk_accepted": Count("pk", filter=Q(current_status=Status.STATUS_RISK_ACCEPTED)),
}

LICENSE_COUNTS = {
    "allowed": Count("pk", filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED)),
    "forbidden": Count("pk", filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN)),
    "ignored": Count("pk", filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_IGNORED)),
    "review_required": Count("pk", filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED)),
    "unknown": Count("pk", filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_UNKNOWN)),
}

# Stays below the parameter limits of the databases
BATCH_SIZE = 1000

Metrics = TypeVar("Metrics", Product_Metrics, Product_License_Metrics)


def calculate_product_metrics() -> str:
    settings = Settings.load()

    products = Product.objects.filter(is_product_group=False).values_list(
        "pk", "last_observation_change", "last_license_change"
    )
    observation_changes = {}
    license_changes = {}
    for product_id, last_observation_change, last_license_change in products:
        observation_changes[product_id] = last_observation_change
        license_changes[product_id] = last_license_change

    products_calculated = _calculate_metrics(
        Product_Metrics, Observation, OBSERVATION_COUNTS, "last_observation_change", observation_changes
    )
    if settings.feature_license_management:
        products_calculated |= _calculate_metrics(
            Product_License_Metrics, License_Component, LICENSE_COUNTS, "last_license_change", license_changes
        )

    product_metrics_status = Product_Metrics_Status.load()
    product_metrics_status.last_calculated = timezone.now()
    product_metrics_status.save()

    if len(products_calculated) == 1:
        return "Calculated metrics for 1 product."

    return f"Calculated metrics for {len(products_calculated)} products."


def _calculate_metrics(
    metrics_model: type[Metrics],
    counted_model: type[Observation] | type[License_Component],
    counts: dict[str, Count],
    change_field: str,
    product_changes: dict[int, datetime],
) -> set[int]:
    # Metrics are up to date if they have been calculated for the current change of the product
    today = timezone.localdate()
    todays_pks, todays_changes = _get_todays_metrics(metrics_model, change_field, today)
    changed_product_ids = [
        product_id for product_id, change in product_changes.items() if todays_changes.get(product_id) != change
    ]

    products_calculated: set[int] = set()
    for product_ids in batched(changed_product_ids, BATCH_SIZE):
        new_metrics: list[Metrics] = []
        updated_metrics: list[Metrics] = []
        latest_metrics = _get_latest_metrics(metrics_model, product_ids)
        recalculated_product_ids = []
        for product_id in product_ids:
            latest = latest_metrics.get(product_id)
            if latest and getattr(latest, change_field) == product_changes[product_id]:
                # No relevant changes since the latest metrics, which are copied up to today
                iteration_date = latest.date + timedelta(days=1)
                while iteration_date <= today:
                    new_metrics.append(
                        metrics_model(
                            product_id=product_id,
                            date=iteration_date,
                            **{field: getattr(latest, field) for field in [*counts, change_field]},
                        )
                    )
                    iteration_date += timedelta(days=1)
            else:
                recalculated_product_ids.append(product_id)

        calculated_counts = _count(counted_model, counts, recalculated_product_ids)
        for product_id in recalculated_product_ids:
            metrics = metrics_model(
                product_id=product_id,
                date=today,
                **calculated_counts.get(product_id, dict.fromkeys(counts, 0)),
                **{change_field: product_changes[product_id]},
            )
            if product_id in todays_pks:
                metrics.pk = todays_pks[product_id]
                updated_metrics.append(metrics)
            else:
                new_metrics.append(metrics)

        # Written per batch, so that the memory doesn't grow with the number of products
        metrics_model.objects.bulk_create(new_metrics, BATCH_SIZE)
        metrics_model.objects.bulk_update(updated_metrics, [*counts, change_field], BATCH_SIZE)
        products_calculated.update(metrics.product_id for metrics in new_metrics + updated_metrics)

    return products_calculated


def _get_todays_metrics(
    metrics_model: type[Metrics], change_field: str, today: date
) -> tuple[dict[int, int], dict[int, Optional[datetime]]]:
    todays_pks = {}
    todays_changes = {}
    for pk, product_id, change in metrics_model.objects.filter(date=today).values_list(
        "pk", "product_id", change_field
    ):
        todays_pks[product_id] = pk
        todays_changes[product_id] = change
    return todays_pks, todays_changes


def _get_latest_metrics(metrics_model: type[Metrics], product_ids: tuple[int, ...]) -> dict[int, Metrics]:
    # Starts from the products, so that the latest metrics are looked up once per product, not once per metrics row
    latest_pk = metrics_model.objects.filter(product_id=OuterRef("pk")).order_by("-date").values("pk")[:1]
    latest_pks = Product.objects.filter(pk__in=product_ids).annotate(latest_pk=Subquery(latest_pk)).values("latest_pk")
    return {metrics.product_id: metrics for metrics in metrics_model.objects.filter(pk__in=latest_pks)}


def _count(
    counted_model: type[Observation] | type[License_Component], counts: dict[str, Count], product_ids: list[int]
) -> dict[int, dict[str, int]]:
    # Only the observations and licenses of the default branch are counted, or those without a branch
    # if the product has no default branch
    rows = (
        counted_model.objects.filter(product_id__in=product_ids)
        .filter(
            Q(branch=F("product__repository_default_branch"))
            | Q(branch__isnull=True, product__repository_default_branch__isnull=True)
        )
        .values("product_id")
        .annotate(**counts)
        .values_list("product_id", *counts)
    )
    return {product_id: dict(zip(counts, values)) for product_id, *values in rows}


def get_product_metrics_timeline(product: Optional[Product], age: str) -> dict:
    product_metrics = get_product_metrics()
    if product:
        if product.is_product_group:
            product_metrics = product_metrics.filter(product__product_group=product)
        else:
            product_metrics = product_metrics.filter(product=product)

    days = get_days(age)
    if days:
        product_metrics = product_metrics.filter(date__gte=timezone.localdate() - timedelta(days=int(days)))

    fields = list(_initialize_response_data())
    if not product or product.is_product_group:
        # One row per product and day, summed up by the database; annotations can't reuse the names of the fields.
        # order_by() removes the ordering by id of get_product_metrics(), which would otherwise be grouped by as well.
        sums = product_metrics.order_by().values("date").annotate(**{f"{field}_sum": Sum(field) for field in fields})
        return {
            row["date"].isoformat(): {field: row[f"{field}_sum"] for field in fields} for row in sums.order_by("date")
        }

    return {row.pop("date").isoformat(): row for row in product_metrics.values("date", *fields).order_by("date")}


def get_product_metrics_current(product: Optional[Product]) -> dict:
    product_metrics = get_latest_product_metrics(product)

    response_data: dict = _initialize_response_data()
    if len(product_metrics) > 0:
        for product_metric in product_metrics:
            response_data["active_critical"] += product_metric.active_critical
            response_data["active_high"] += product_metric.active_high
            response_data["active_medium"] += product_metric.active_medium
            response_data["active_low"] += product_metric.active_low
            response_data["active_none"] += product_metric.active_none
            response_data["active_unknown"] += product_metric.active_unknown
            response_data["open"] += product_metric.open
            response_data["affected"] += product_metric.affected
            response_data["resolved"] += product_metric.resolved
            response_data["duplicate"] += product_metric.duplicate
            response_data["false_positive"] += product_metric.false_positive
            response_data["in_review"] += product_metric.in_review
            response_data["not_affected"] += product_metric.not_affected
            response_data["not_security"] += product_metric.not_security
            response_data["risk_accepted"] += product_metric.risk_accepted

    return response_data


def _initialize_response_data() -> dict:
    response_data: dict = {}
    response_data["active_critical"] = 0
    response_data["active_high"] = 0
    response_data["active_medium"] = 0
    response_data["active_low"] = 0
    response_data["active_none"] = 0
    response_data["active_unknown"] = 0
    response_data["open"] = 0
    response_data["affected"] = 0
    response_data["resolved"] = 0
    response_data["duplicate"] = 0
    response_data["false_positive"] = 0
    response_data["in_review"] = 0
    response_data["not_affected"] = 0
    response_data["not_security"] = 0
    response_data["risk_accepted"] = 0
    return response_data


def get_codecharta_metrics(product: Product) -> list[dict]:
    file_severities_dict: dict[str, dict] = {}
    observations = Observation.objects.filter(
        product=product,
        branch=product.repository_default_branch,
        current_status__in=Status.STATUS_ACTIVE,
    )
    for observation in observations:
        if observation.origin_source_file:
            file_severities_value = file_severities_dict.get(observation.origin_source_file)
            if not file_severities_value:
                file_severities_value = {}
                file_severities_value["source_file"] = observation.origin_source_file
                file_severities_value["Vulnerabilities_Total".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_CRITICAL}".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_HIGH}".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_MEDIUM}".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_LOW}".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_NONE}".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_UNKNOWN}".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_HIGH}_and_above".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_MEDIUM}_and_above".lower()] = 0
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_LOW}_and_above".lower()] = 0
                file_severities_dict[observation.origin_source_file] = file_severities_value

            file_severities_value["Vulnerabilities_Total".lower()] += 1
            file_severities_value[f"Vulnerabilities_{observation.current_severity}".lower()] += 1

            if observation.current_severity in (
                Severity.SEVERITY_CRITICAL,
                Severity.SEVERITY_HIGH,
            ):
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_HIGH}_and_above".lower()] += 1
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_MEDIUM}_and_above".lower()] += 1
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_LOW}_and_above".lower()] += 1

            if observation.current_severity == Severity.SEVERITY_MEDIUM:
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_MEDIUM}_and_above".lower()] += 1
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_LOW}_and_above".lower()] += 1

            if observation.current_severity == Severity.SEVERITY_LOW:
                file_severities_value[f"Vulnerabilities_{Severity.SEVERITY_LOW}_and_above".lower()] += 1

    return list(file_severities_dict.values())
