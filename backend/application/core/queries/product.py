from collections.abc import Sequence
from typing import Optional

from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.utils import timezone

from application.access_control.services.current_user import get_current_user
from application.commons.models import Settings
from application.core.models import (
    Observation,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.core.types import Severity, Status
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from application.metrics.models import Product_License_Metrics, Product_Metrics

SEVERITY_MAPPING = {
    Severity.SEVERITY_CRITICAL: "active_critical",
    Severity.SEVERITY_HIGH: "active_high",
    Severity.SEVERITY_MEDIUM: "active_medium",
    Severity.SEVERITY_LOW: "active_low",
    Severity.SEVERITY_NONE: "active_none",
    Severity.SEVERITY_UNKNOWN: "active_unknown",
}

EVALUATION_RESULT_MAPPING = {
    License_Policy_Evaluation_Result.RESULT_ALLOWED: "allowed",
    License_Policy_Evaluation_Result.RESULT_FORBIDDEN: "forbidden",
    License_Policy_Evaluation_Result.RESULT_IGNORED: "ignored",
    License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED: "review_required",
    License_Policy_Evaluation_Result.RESULT_UNKNOWN: "unknown",
}


def get_product_by_id(
    product_id: int,
    is_product_group: bool = None,
    with_observation_annotations: bool = False,
    with_metrics_annotations: bool = False,
) -> Optional[Product]:
    try:
        if is_product_group is None:
            return _add_annotations(Product.objects.all(), False, False, False).get(id=product_id)
        product = Product.objects.get(id=product_id, is_product_group=is_product_group)
        if with_observation_annotations or with_metrics_annotations:
            settings = Settings.load()
            populate_product_count_annotations(
                [product],
                is_product_group=is_product_group,
                use_metrics=with_metrics_annotations and not with_observation_annotations,
                include_license_counts=settings.feature_license_management,
            )
        return product
    except Product.DoesNotExist:
        return None


def get_product_by_name(name: str, is_product_group: bool = None) -> Optional[Product]:
    try:
        if is_product_group is None:
            return Product.objects.get(name=name)
        return Product.objects.get(name=name, is_product_group=is_product_group)
    except Product.DoesNotExist:
        return None


def get_products(
    is_product_group: bool = None, with_observation_annotations: bool = False, with_metrics_annotations: bool = False
) -> QuerySet[Product]:
    user = get_current_user()

    if user is None:
        return Product.objects.none()

    products = Product.objects.all().order_by("id")

    if is_product_group is not None:
        products = _add_annotations(products, is_product_group, with_observation_annotations, with_metrics_annotations)

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("pk"), user=user)
        product_group_members = Product_Member.objects.filter(product=OuterRef("product_group"), user=user)

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("pk"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product_group"),
            authorization_group__users=user,
        )

        products = products.annotate(
            member=Exists(product_members),
            product_group_member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )
        products = products.filter(
            Q(member=True)
            | Q(product_group_member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
        )

    if is_product_group is not None:
        products = products.filter(is_product_group=is_product_group)

    return products


def populate_product_count_annotations(
    products: Sequence[Product],
    is_product_group: bool,
    use_metrics: bool = False,
    include_license_counts: bool = False,
) -> None:
    product_ids = [product.pk for product in products if product.pk]
    if not product_ids:
        return

    _initialize_observation_count_annotations(products)
    if include_license_counts:
        _initialize_license_count_annotations(products)
    else:
        _clear_license_count_annotations(products)

    if use_metrics:
        _populate_observation_counts_from_metrics(products, is_product_group, product_ids)
        if include_license_counts:
            _populate_license_counts_from_metrics(products, is_product_group, product_ids)
    else:
        _populate_observation_counts_from_observations(products, is_product_group, product_ids)
        if include_license_counts:
            _populate_license_counts_from_components(products, is_product_group, product_ids)


def populate_product_group_product_counts(product_groups: Sequence[Product]) -> None:
    product_group_ids = [product_group.pk for product_group in product_groups if product_group.pk]
    if not product_group_ids:
        return

    product_groups_by_id = {product_group.pk: product_group for product_group in product_groups}
    for product_group in product_groups:
        product_group.products_count_value = 0

    counts = (
        Product.objects.filter(product_group_id__in=product_group_ids)
        .values("product_group_id")
        .annotate(count=Count("pk"))
    )
    for count in counts:
        product_group = product_groups_by_id.get(count["product_group_id"])
        if product_group:
            product_group.products_count_value = count["count"]


def _initialize_observation_count_annotations(products: Sequence[Product]) -> None:
    for product in products:
        for metric_field in SEVERITY_MAPPING.values():
            setattr(product, f"{metric_field}_observation_count", 0)


def _initialize_license_count_annotations(products: Sequence[Product]) -> None:
    for product in products:
        for metric_field in EVALUATION_RESULT_MAPPING.values():
            setattr(product, f"{metric_field}_licenses_count", 0)


def _clear_license_count_annotations(products: Sequence[Product]) -> None:
    for product in products:
        for metric_field in EVALUATION_RESULT_MAPPING.values():
            setattr(product, f"{metric_field}_licenses_count", None)


def _populate_observation_counts_from_observations(
    products: Sequence[Product],
    is_product_group: bool,
    product_ids: list[int],
) -> None:
    products_by_id = {product.pk: product for product in products}
    grouping_field = "product__product_group_id" if is_product_group else "product_id"
    product_filter = (
        {"product__product_group_id__in": product_ids} if is_product_group else {"product_id__in": product_ids}
    )

    counts = (
        Observation.objects.filter(
            _get_default_branch_filter(),
            current_status__in=Status.STATUS_ACTIVE,
            **product_filter,
        )
        .values(grouping_field, "current_severity")
        .annotate(count=Count("pk"))
    )
    for count in counts:
        product = products_by_id.get(count[grouping_field])
        metric_field = SEVERITY_MAPPING.get(count["current_severity"])
        if product and metric_field:
            setattr(product, f"{metric_field}_observation_count", count["count"])


def _populate_observation_counts_from_metrics(
    products: Sequence[Product],
    is_product_group: bool,
    product_ids: list[int],
) -> None:
    products_by_id = {product.pk: product for product in products}
    grouping_field = "product__product_group_id" if is_product_group else "product_id"
    product_filter = (
        {"product__product_group_id__in": product_ids} if is_product_group else {"product_id__in": product_ids}
    )
    metric_fields = tuple(SEVERITY_MAPPING.values())

    counts = (
        Product_Metrics.objects.filter(date=timezone.localdate(), **product_filter)
        .values(grouping_field)
        .annotate(**{metric_field: Sum(metric_field) for metric_field in metric_fields})
    )
    for count in counts:
        product = products_by_id.get(count[grouping_field])
        if product:
            for metric_field in metric_fields:
                setattr(product, f"{metric_field}_observation_count", count[metric_field] or 0)


def _populate_license_counts_from_components(
    products: Sequence[Product],
    is_product_group: bool,
    product_ids: list[int],
) -> None:
    products_by_id = {product.pk: product for product in products}
    grouping_field = "product__product_group_id" if is_product_group else "product_id"
    product_filter = (
        {"product__product_group_id__in": product_ids} if is_product_group else {"product_id__in": product_ids}
    )

    counts = (
        License_Component.objects.filter(_get_default_branch_filter(), **product_filter)
        .values(grouping_field, "evaluation_result")
        .annotate(count=Count("pk"))
    )
    for count in counts:
        product = products_by_id.get(count[grouping_field])
        metric_field = EVALUATION_RESULT_MAPPING.get(count["evaluation_result"])
        if product and metric_field:
            setattr(product, f"{metric_field}_licenses_count", count["count"])


def _populate_license_counts_from_metrics(
    products: Sequence[Product],
    is_product_group: bool,
    product_ids: list[int],
) -> None:
    products_by_id = {product.pk: product for product in products}
    grouping_field = "product__product_group_id" if is_product_group else "product_id"
    product_filter = (
        {"product__product_group_id__in": product_ids} if is_product_group else {"product_id__in": product_ids}
    )
    metric_fields = tuple(EVALUATION_RESULT_MAPPING.values())

    counts = (
        Product_License_Metrics.objects.filter(date=timezone.localdate(), **product_filter)
        .values(grouping_field)
        .annotate(**{metric_field: Sum(metric_field) for metric_field in metric_fields})
    )
    for count in counts:
        product = products_by_id.get(count[grouping_field])
        if product:
            for metric_field in metric_fields:
                setattr(product, f"{metric_field}_licenses_count", count[metric_field] or 0)


def _get_default_branch_filter() -> Q:
    return Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )


def _add_annotations(
    queryset: QuerySet, is_product_group: bool, with_observation_annotations: bool, with_metrics_annotations: bool
) -> QuerySet:
    if not with_observation_annotations and not with_metrics_annotations:
        return queryset

    if with_observation_annotations:
        queryset = _add_observation_annotations(queryset, is_product_group)
        queryset = _add_license_annotations(queryset, is_product_group)
    elif with_metrics_annotations:
        queryset = _add_observation_metrics_annotations(queryset, is_product_group)
        queryset = _add_license_metrics_annotations(queryset, is_product_group)
    return queryset


def _add_observation_annotations(queryset: QuerySet, is_product_group: bool) -> QuerySet:
    subquery_active_critical = (
        _get_product_group_observation_subquery(Severity.SEVERITY_CRITICAL)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_CRITICAL)
    )
    subquery_active_high = (
        _get_product_group_observation_subquery(Severity.SEVERITY_HIGH)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_HIGH)
    )
    subquery_active_medium = (
        _get_product_group_observation_subquery(Severity.SEVERITY_MEDIUM)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_MEDIUM)
    )
    subquery_active_low = (
        _get_product_group_observation_subquery(Severity.SEVERITY_LOW)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_LOW)
    )
    subquery_active_none = (
        _get_product_group_observation_subquery(Severity.SEVERITY_NONE)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_NONE)
    )
    subquery_active_unknown = (
        _get_product_group_observation_subquery(Severity.SEVERITY_UNKNOWN)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_UNKNOWN)
    )

    queryset = queryset.annotate(
        active_critical_observation_count=Coalesce(subquery_active_critical, 0),
        active_high_observation_count=Coalesce(subquery_active_high, 0),
        active_medium_observation_count=Coalesce(subquery_active_medium, 0),
        active_low_observation_count=Coalesce(subquery_active_low, 0),
        active_none_observation_count=Coalesce(subquery_active_none, 0),
        active_unknown_observation_count=Coalesce(subquery_active_unknown, 0),
    )

    return queryset


def _add_observation_metrics_annotations(queryset: QuerySet, is_product_group: bool) -> QuerySet:
    subquery_active_critical = (
        _get_product_group_metrics_subquery(Severity.SEVERITY_CRITICAL)
        if is_product_group
        else _get_product_metrics_subquery(Severity.SEVERITY_CRITICAL)
    )
    subquery_active_high = (
        _get_product_group_metrics_subquery(Severity.SEVERITY_HIGH)
        if is_product_group
        else _get_product_metrics_subquery(Severity.SEVERITY_HIGH)
    )
    subquery_active_medium = (
        _get_product_group_metrics_subquery(Severity.SEVERITY_MEDIUM)
        if is_product_group
        else _get_product_metrics_subquery(Severity.SEVERITY_MEDIUM)
    )
    subquery_active_low = (
        _get_product_group_metrics_subquery(Severity.SEVERITY_LOW)
        if is_product_group
        else _get_product_metrics_subquery(Severity.SEVERITY_LOW)
    )
    subquery_active_none = (
        _get_product_group_metrics_subquery(Severity.SEVERITY_NONE)
        if is_product_group
        else _get_product_metrics_subquery(Severity.SEVERITY_NONE)
    )
    subquery_active_unknown = (
        _get_product_group_metrics_subquery(Severity.SEVERITY_UNKNOWN)
        if is_product_group
        else _get_product_metrics_subquery(Severity.SEVERITY_UNKNOWN)
    )

    queryset = queryset.annotate(
        active_critical_observation_count=Coalesce(subquery_active_critical, 0),
        active_high_observation_count=Coalesce(subquery_active_high, 0),
        active_medium_observation_count=Coalesce(subquery_active_medium, 0),
        active_low_observation_count=Coalesce(subquery_active_low, 0),
        active_none_observation_count=Coalesce(subquery_active_none, 0),
        active_unknown_observation_count=Coalesce(subquery_active_unknown, 0),
    )

    return queryset


def _add_license_annotations(queryset: QuerySet, is_product_group: bool) -> QuerySet:
    settings = Settings.load()
    if settings.feature_license_management:
        subquery_license_forbidden = (
            _get_product_group_license_subquery(License_Policy_Evaluation_Result.RESULT_FORBIDDEN)
            if is_product_group
            else _get_product_license_subquery(License_Policy_Evaluation_Result.RESULT_FORBIDDEN)
        )
        subquery_license_review_required = (
            _get_product_group_license_subquery(License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED)
            if is_product_group
            else _get_product_license_subquery(License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED)
        )
        subquery_license_unknown = (
            _get_product_group_license_subquery(License_Policy_Evaluation_Result.RESULT_UNKNOWN)
            if is_product_group
            else _get_product_license_subquery(License_Policy_Evaluation_Result.RESULT_UNKNOWN)
        )
        subquery_license_allowed = (
            _get_product_group_license_subquery(License_Policy_Evaluation_Result.RESULT_ALLOWED)
            if is_product_group
            else _get_product_license_subquery(License_Policy_Evaluation_Result.RESULT_ALLOWED)
        )
        subquery_license_ignored = (
            _get_product_group_license_subquery(License_Policy_Evaluation_Result.RESULT_IGNORED)
            if is_product_group
            else _get_product_license_subquery(License_Policy_Evaluation_Result.RESULT_IGNORED)
        )

        queryset = queryset.annotate(
            forbidden_licenses_count=Coalesce(subquery_license_forbidden, 0),
            review_required_licenses_count=Coalesce(subquery_license_review_required, 0),
            unknown_licenses_count=Coalesce(subquery_license_unknown, 0),
            allowed_licenses_count=Coalesce(subquery_license_allowed, 0),
            ignored_licenses_count=Coalesce(subquery_license_ignored, 0),
        )

    return queryset


def _add_license_metrics_annotations(queryset: QuerySet, is_product_group: bool) -> QuerySet:
    settings = Settings.load()
    if settings.feature_license_management:
        subquery_license_forbidden = (
            _get_product_group_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_FORBIDDEN)
            if is_product_group
            else _get_product_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_FORBIDDEN)
        )
        subquery_license_review_required = (
            _get_product_group_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED)
            if is_product_group
            else _get_product_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED)
        )
        subquery_license_unknown = (
            _get_product_group_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_UNKNOWN)
            if is_product_group
            else _get_product_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_UNKNOWN)
        )
        subquery_license_allowed = (
            _get_product_group_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_ALLOWED)
            if is_product_group
            else _get_product_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_ALLOWED)
        )
        subquery_license_ignored = (
            _get_product_group_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_IGNORED)
            if is_product_group
            else _get_product_license_metrics_subquery(License_Policy_Evaluation_Result.RESULT_IGNORED)
        )

        queryset = queryset.annotate(
            forbidden_licenses_count=Coalesce(subquery_license_forbidden, 0),
            review_required_licenses_count=Coalesce(subquery_license_review_required, 0),
            unknown_licenses_count=Coalesce(subquery_license_unknown, 0),
            allowed_licenses_count=Coalesce(subquery_license_allowed, 0),
            ignored_licenses_count=Coalesce(subquery_license_ignored, 0),
        )

    return queryset


def _get_product_observation_subquery(severity: str) -> Subquery:
    branch_filter = Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )

    return Subquery(
        Observation.objects.filter(
            branch_filter,
            product=OuterRef("pk"),
            current_status__in=Status.STATUS_ACTIVE,
            current_severity=severity,
        )
        .order_by()
        .values("product")
        .annotate(count=Count("pk"))
        .values("count"),
        output_field=IntegerField(),
    )


def _get_product_group_observation_subquery(severity: str) -> Subquery:
    branch_filter = Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )

    return Subquery(
        Observation.objects.filter(
            branch_filter,
            product__product_group=OuterRef("pk"),
            current_status__in=Status.STATUS_ACTIVE,
            current_severity=severity,
        )
        .order_by()
        .values("product__product_group")
        .annotate(count=Count("pk"))
        .values("count"),
        output_field=IntegerField(),
    )


def _get_product_metrics_subquery(severity: str) -> Subquery:
    return Subquery(
        Product_Metrics.objects.filter(product=OuterRef("pk"), date=timezone.localdate()).values(
            SEVERITY_MAPPING[severity]
        ),
        output_field=IntegerField(),
    )


def _get_product_group_metrics_subquery(severity: str) -> Subquery:
    return Subquery(
        Product_Metrics.objects.filter(product__product_group=OuterRef("pk"), date=timezone.localdate())
        .values("product__product_group")
        .annotate(total=Sum(SEVERITY_MAPPING[severity]))
        .values("total"),
        output_field=IntegerField(),
    )


def _get_product_license_subquery(evaluation_result: str) -> Subquery:
    branch_filter = Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )

    return Subquery(
        License_Component.objects.filter(
            branch_filter,
            product=OuterRef("pk"),
            evaluation_result=evaluation_result,
        )
        .order_by()
        .values("product")
        .annotate(count=Count("pk"))
        .values("count"),
        output_field=IntegerField(),
    )


def _get_product_group_license_subquery(evaluation_result: str) -> Subquery:
    branch_filter = Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )

    return Subquery(
        License_Component.objects.filter(
            branch_filter,
            product__product_group=OuterRef("pk"),
            evaluation_result=evaluation_result,
        )
        .order_by()
        .values("product__product_group")
        .annotate(count=Count("pk"))
        .values("count"),
        output_field=IntegerField(),
    )


def _get_product_license_metrics_subquery(evaluation_result: str) -> Subquery:
    return Subquery(
        Product_License_Metrics.objects.filter(product=OuterRef("pk"), date=timezone.localdate()).values(
            EVALUATION_RESULT_MAPPING[evaluation_result]
        ),
        output_field=IntegerField(),
    )


def _get_product_group_license_metrics_subquery(evaluation_result: str) -> Subquery:
    return Subquery(
        Product_License_Metrics.objects.filter(product__product_group=OuterRef("pk"), date=timezone.localdate())
        .values("product__product_group")
        .annotate(total=Sum(EVALUATION_RESULT_MAPPING[evaluation_result]))
        .values("total"),
        output_field=IntegerField(),
    )
