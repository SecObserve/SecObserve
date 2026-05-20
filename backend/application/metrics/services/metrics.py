from datetime import timedelta
from typing import Optional

from django.db.models import Count, Q
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
    get_product_metrics,
    get_todays_product_metrics,
)
from application.metrics.services.age import get_days


def calculate_product_metrics() -> str:
    settings = Settings.load()

    num_products = 0
    license_metrics_calculated = False
    for product in Product.objects.filter(is_product_group=False):
        observation_metrics_calculated = bool(calculate_observation_metrics_for_product(product))
        if settings.feature_license_management:
            license_metrics_calculated = bool(calculate_license_metrics_for_product(product))
        num_products += observation_metrics_calculated or license_metrics_calculated

    product_metrics_status = Product_Metrics_Status.load()
    product_metrics_status.last_calculated = timezone.now()
    product_metrics_status.save()

    if num_products == 1:
        return "Calculated metrics for 1 product."

    return f"Calculated metrics for {num_products} products."


def calculate_observation_metrics_for_product(  # pylint: disable=too-many-branches
    product: Product,
) -> bool:
    # There are quite a lot of branches, but at least they are not nested too much

    metrics_calculated = False
    today = timezone.localdate()

    latest_product_metrics = _get_latest_product_observation_metrics(product)

    if timezone.localdate(product.last_observation_change) < today and latest_product_metrics:
        # No relevant changes of observations today, but we might need to update the metrics
        # if there are no metrics for today or previous days.
        iteration_date = latest_product_metrics.date + timedelta(days=1)
        while iteration_date <= today:
            Product_Metrics.objects.create(
                product=product,
                date=iteration_date,
                active_critical=latest_product_metrics.active_critical,
                active_high=latest_product_metrics.active_high,
                active_medium=latest_product_metrics.active_medium,
                active_low=latest_product_metrics.active_low,
                active_none=latest_product_metrics.active_none,
                active_unknown=latest_product_metrics.active_unknown,
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
        observation_metrics = Observation.objects.filter(
            product=product,
            branch=product.repository_default_branch,
        ).aggregate(
            active_critical=Count(
                "pk",
                filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_CRITICAL),
            ),
            active_high=Count(
                "pk",
                filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_HIGH),
            ),
            active_medium=Count(
                "pk",
                filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_MEDIUM),
            ),
            active_low=Count(
                "pk",
                filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_LOW),
            ),
            active_none=Count(
                "pk",
                filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_NONE),
            ),
            active_unknown=Count(
                "pk",
                filter=Q(current_status__in=Status.STATUS_ACTIVE, current_severity=Severity.SEVERITY_UNKNOWN),
            ),
            open=Count("pk", filter=Q(current_status=Status.STATUS_OPEN)),
            affected=Count("pk", filter=Q(current_status=Status.STATUS_AFFECTED)),
            resolved=Count("pk", filter=Q(current_status=Status.STATUS_RESOLVED)),
            duplicate=Count("pk", filter=Q(current_status=Status.STATUS_DUPLICATE)),
            false_positive=Count("pk", filter=Q(current_status=Status.STATUS_FALSE_POSITIVE)),
            in_review=Count("pk", filter=Q(current_status=Status.STATUS_IN_REVIEW)),
            not_affected=Count("pk", filter=Q(current_status=Status.STATUS_NOT_AFFECTED)),
            not_security=Count("pk", filter=Q(current_status=Status.STATUS_NOT_SECURITY)),
            risk_accepted=Count("pk", filter=Q(current_status=Status.STATUS_RISK_ACCEPTED)),
        )

        Product_Metrics.objects.update_or_create(
            product=product,
            date=today,
            defaults=observation_metrics,
        )
        metrics_calculated = True

    return metrics_calculated


def calculate_license_metrics_for_product(  # pylint: disable=too-many-branches
    product: Product,
) -> bool:
    # There are quite a lot of branches, but at least they are not nested too much

    metrics_calculated = False
    today = timezone.localdate()

    latest_product_license_metrics = _get_latest_product_license_metrics(product)

    if timezone.localdate(product.last_license_change) < today and latest_product_license_metrics:
        # No relevant changes of observations today, but we might need to update the metrics
        # if there are no metrics for today or previous days.
        iteration_date = latest_product_license_metrics.date + timedelta(days=1)
        while iteration_date <= today:
            Product_License_Metrics.objects.create(
                product=product,
                date=iteration_date,
                allowed=latest_product_license_metrics.allowed,
                forbidden=latest_product_license_metrics.forbidden,
                ignored=latest_product_license_metrics.ignored,
                review_required=latest_product_license_metrics.review_required,
                unknown=latest_product_license_metrics.unknown,
            )
            iteration_date += timedelta(days=1)
            metrics_calculated = True
    else:
        # Either there are relevant changes of licenses today or there are no metrics yet at all,
        # so we need to calculate the metrics for today.
        license_metrics = License_Component.objects.filter(
            product=product,
            branch=product.repository_default_branch,
        ).aggregate(
            allowed=Count(
                "pk",
                filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED),
            ),
            forbidden=Count(
                "pk",
                filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_FORBIDDEN),
            ),
            ignored=Count(
                "pk",
                filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_IGNORED),
            ),
            review_required=Count(
                "pk",
                filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED),
            ),
            unknown=Count(
                "pk",
                filter=Q(evaluation_result=License_Policy_Evaluation_Result.RESULT_UNKNOWN),
            ),
        )

        Product_License_Metrics.objects.update_or_create(
            product=product,
            date=today,
            defaults=license_metrics,
        )
        metrics_calculated = True

    return metrics_calculated


def _get_latest_product_observation_metrics(product: Product) -> Optional[Product_Metrics]:
    try:
        return Product_Metrics.objects.filter(product=product).latest("date")
    except Product_Metrics.DoesNotExist:
        return None


def _get_latest_product_license_metrics(product: Product) -> Optional[Product_License_Metrics]:
    try:
        return Product_License_Metrics.objects.filter(product=product).latest("date")
    except Product_License_Metrics.DoesNotExist:
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
            response_metric["active_critical"] = (
                response_metric.get("active_critical", 0) + product_metric.active_critical
            )
            response_metric["active_high"] = response_metric.get("active_high", 0) + product_metric.active_high
            response_metric["active_medium"] = response_metric.get("active_medium", 0) + product_metric.active_medium
            response_metric["active_low"] = response_metric.get("active_low", 0) + product_metric.active_low
            response_metric["active_none"] = response_metric.get("active_none", 0) + product_metric.active_none
            response_metric["active_unknown"] = response_metric.get("active_unknown", 0) + product_metric.active_unknown
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
            response_metric["active_critical"] = product_metric.active_critical
            response_metric["active_high"] = product_metric.active_high
            response_metric["active_medium"] = product_metric.active_medium
            response_metric["active_low"] = product_metric.active_low
            response_metric["active_none"] = product_metric.active_none
            response_metric["active_unknown"] = product_metric.active_unknown
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
