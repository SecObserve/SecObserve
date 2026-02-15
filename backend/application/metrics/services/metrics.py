from datetime import timedelta
from typing import Optional

from django.utils import timezone

from application.core.models import Observation, Product
from application.core.types import Severity, Status
from application.metrics.models import Product_Metrics, Product_Metrics_Status
from application.metrics.queries.product_metrics import (
    get_product_metrics,
    get_todays_product_metrics,
)
from application.metrics.services.age import get_days


def calculate_product_metrics() -> str:

    num_products = 0

    for product in Product.objects.filter(is_product_group=False):
        if calculate_metrics_for_product(product):
            num_products += 1

    product_metrics_status = Product_Metrics_Status.load()
    product_metrics_status.last_calculated = timezone.now()
    product_metrics_status.save()

    if num_products == 1:
        return "Calculated metrics for 1 product."

    return f"Calculated metrics for {num_products} products."


def calculate_metrics_for_product(  # pylint: disable=too-many-branches
    product: Product,
) -> bool:
    # There are quite a lot of branches, but at least they are not nested too much

    metrics_calculated = False
    today = timezone.localdate()

    latest_product_metrics = _get_latest_product_metrics(product)

    if product.last_observation_change.date() < today and latest_product_metrics:
        # No relevant changes of observations today, but we might need to update the metrics
        # if there are no metrics for today or previous days.
        iteration_date = latest_product_metrics.date + timedelta(days=1)
        while iteration_date <= today:
            Product_Metrics.objects.create(
                product=product,
                date=iteration_date,
                open_critical=latest_product_metrics.open_critical,
                open_high=latest_product_metrics.open_high,
                open_medium=latest_product_metrics.open_medium,
                open_low=latest_product_metrics.open_low,
                open_none=latest_product_metrics.open_none,
                open_unknown=latest_product_metrics.open_unknown,
                open=latest_product_metrics.open,
                affected=latest_product_metrics.affected,
                resolved=latest_product_metrics.resolved,
                duplicate=latest_product_metrics.duplicate,
                false_positive=latest_product_metrics.false_positive,
                in_review=latest_product_metrics.in_review,
                not_affected=latest_product_metrics.not_affected,
                not_security=latest_product_metrics.not_security,
                risk_accepted=latest_product_metrics.risk_accepted,
            )
            iteration_date += timedelta(days=1)
            metrics_calculated = True
    else:
        # Either there are relevant changes of observations today or there are no metrics yet at all,
        # so we need to calculate the metrics for today.
        todays_product_metrics = Product_Metrics.objects.update_or_create(
            product=product,
            date=today,
            defaults={
                "open_critical": 0,
                "open_high": 0,
                "open_medium": 0,
                "open_low": 0,
                "open_none": 0,
                "open_unknown": 0,
                "open": 0,
                "affected": 0,
                "resolved": 0,
                "duplicate": 0,
                "false_positive": 0,
                "in_review": 0,
                "not_affected": 0,
                "not_security": 0,
                "risk_accepted": 0,
            },
        )[0]

        observations = Observation.objects.filter(
            product=product,
            branch=product.repository_default_branch,
        ).values("current_severity", "current_status")

        for observation in observations:
            if observation.get("current_status") in Status.STATUS_ACTIVE:
                if observation.get("current_severity") == Severity.SEVERITY_CRITICAL:
                    todays_product_metrics.open_critical += 1
                elif observation.get("current_severity") == Severity.SEVERITY_HIGH:
                    todays_product_metrics.open_high += 1
                elif observation.get("current_severity") == Severity.SEVERITY_MEDIUM:
                    todays_product_metrics.open_medium += 1
                elif observation.get("current_severity") == Severity.SEVERITY_LOW:
                    todays_product_metrics.open_low += 1
                elif observation.get("current_severity") == Severity.SEVERITY_NONE:
                    todays_product_metrics.open_none += 1
                elif observation.get("current_severity") == Severity.SEVERITY_UNKNOWN:
                    todays_product_metrics.open_unknown += 1
            if observation.get("current_status") == Status.STATUS_OPEN:
                todays_product_metrics.open += 1
            elif observation.get("current_status") == Status.STATUS_AFFECTED:
                todays_product_metrics.affected += 1
            elif observation.get("current_status") == Status.STATUS_RESOLVED:
                todays_product_metrics.resolved += 1
            elif observation.get("current_status") == Status.STATUS_DUPLICATE:
                todays_product_metrics.duplicate += 1
            elif observation.get("current_status") == Status.STATUS_FALSE_POSITIVE:
                todays_product_metrics.false_positive += 1
            elif observation.get("current_status") == Status.STATUS_IN_REVIEW:
                todays_product_metrics.in_review += 1
            elif observation.get("current_status") == Status.STATUS_NOT_AFFECTED:
                todays_product_metrics.not_affected += 1
            elif observation.get("current_status") == Status.STATUS_NOT_SECURITY:
                todays_product_metrics.not_security += 1
            elif observation.get("current_status") == Status.STATUS_RISK_ACCEPTED:
                todays_product_metrics.risk_accepted += 1

        todays_product_metrics.save()
        metrics_calculated = True

    return metrics_calculated


def _get_latest_product_metrics(product: Product) -> Optional[Product_Metrics]:
    try:
        return Product_Metrics.objects.filter(product=product).latest("date")
    except Product_Metrics.DoesNotExist:
        return None


def get_product_metrics_timeline(product: Optional[Product], age: str) -> dict:
    product_metrics = get_product_metrics()
    if product:
        if product.is_product_group:
            product_metrics = product_metrics.filter(product__product_group=product)
        else:
            product_metrics = product_metrics.filter(product=product)

    days = get_days(age)
    if days:
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        time_threshold = today - timedelta(days=int(days))
        product_metrics = product_metrics.filter(date__gte=time_threshold)

    response_data: dict = {}

    for product_metric in product_metrics:
        if not product or product.is_product_group:
            response_metric = response_data.get(product_metric.date.isoformat(), {})
            response_metric["open_critical"] = response_metric.get("open_critical", 0) + product_metric.open_critical
            response_metric["open_high"] = response_metric.get("open_high", 0) + product_metric.open_high
            response_metric["open_medium"] = response_metric.get("open_medium", 0) + product_metric.open_medium
            response_metric["open_low"] = response_metric.get("open_low", 0) + product_metric.open_low
            response_metric["open_none"] = response_metric.get("open_none", 0) + product_metric.open_none
            response_metric["open_unknown"] = response_metric.get("open_unknown", 0) + product_metric.open_unknown
            response_metric["open"] = response_metric.get("open", 0) + product_metric.open
            response_metric["affected"] = response_metric.get("affected", 0) + product_metric.affected
            response_metric["resolved"] = response_metric.get("resolved", 0) + product_metric.resolved
            response_metric["duplicate"] = response_metric.get("duplicate", 0) + product_metric.duplicate
            response_metric["false_positive"] = response_metric.get("false_positive", 0) + product_metric.false_positive
            response_metric["in_review"] = response_metric.get("in_review", 0) + product_metric.in_review
            response_metric["not_affected"] = response_metric.get("not_affected", 0) + product_metric.not_affected
            response_metric["not_security"] = response_metric.get("not_security", 0) + product_metric.not_security
            response_metric["risk_accepted"] = response_metric.get("risk_accepted", 0) + product_metric.risk_accepted
            response_data[product_metric.date.isoformat()] = response_metric
        else:
            response_metric = {}
            response_metric["open_critical"] = product_metric.open_critical
            response_metric["open_high"] = product_metric.open_high
            response_metric["open_medium"] = product_metric.open_medium
            response_metric["open_low"] = product_metric.open_low
            response_metric["open_none"] = product_metric.open_none
            response_metric["open_unknown"] = product_metric.open_unknown
            response_metric["open"] = product_metric.open
            response_metric["affected"] = product_metric.affected
            response_metric["resolved"] = product_metric.resolved
            response_metric["duplicate"] = product_metric.duplicate
            response_metric["false_positive"] = product_metric.false_positive
            response_metric["in_review"] = product_metric.in_review
            response_metric["not_affected"] = product_metric.not_affected
            response_metric["not_security"] = product_metric.not_security
            response_metric["risk_accepted"] = product_metric.risk_accepted
            response_data[product_metric.date.isoformat()] = response_metric
    return response_data


def get_product_metrics_current(product: Optional[Product]) -> dict:
    product_metrics = get_todays_product_metrics()
    if product:
        if product.is_product_group:
            product_metrics = product_metrics.filter(product__product_group=product)
        else:
            product_metrics = product_metrics.filter(product=product)

    response_data: dict = _initialize_response_data()
    if len(product_metrics) > 0:
        for product_metric in product_metrics:
            response_data["open_critical"] += product_metric.open_critical
            response_data["open_high"] += product_metric.open_high
            response_data["open_medium"] += product_metric.open_medium
            response_data["open_low"] += product_metric.open_low
            response_data["open_none"] += product_metric.open_none
            response_data["open_unknown"] += product_metric.open_unknown
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
    response_data["open_critical"] = 0
    response_data["open_high"] = 0
    response_data["open_medium"] = 0
    response_data["open_low"] = 0
    response_data["open_none"] = 0
    response_data["open_unknown"] = 0
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
