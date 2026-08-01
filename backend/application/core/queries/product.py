from collections.abc import Sequence
from typing import Optional

from django.db.models import Count, Exists, OuterRef, Q, Sum
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
            return Product.objects.get(id=product_id)
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


def get_products(is_product_group: Optional[bool] = None) -> QuerySet[Product]:
    user = get_current_user()

    if user is None:
        return Product.objects.none()

    products = Product.objects.all().order_by("id")

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

    product_group: Optional[Product]

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
