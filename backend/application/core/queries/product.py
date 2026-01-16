from typing import Optional

from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet

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


def get_product_by_id(
    product_id: int, is_product_group: bool = None, with_annotations: bool = False
) -> Optional[Product]:
    try:
        if is_product_group is None:
            return _add_annotations(Product.objects.all(), False, False).get(id=product_id)
        return _add_annotations(Product.objects.all(), is_product_group, with_annotations).get(
            id=product_id, is_product_group=is_product_group
        )
    except Product.DoesNotExist:
        return None


def get_product_by_name(name: str, is_product_group: bool = None) -> Optional[Product]:
    try:
        if is_product_group is None:
            return Product.objects.get(name=name)
        return Product.objects.get(name=name, is_product_group=is_product_group)
    except Product.DoesNotExist:
        return None


def get_products(is_product_group: bool = None, with_annotations: bool = False) -> QuerySet[Product]:
    user = get_current_user()

    if user is None:
        return Product.objects.none()

    products = Product.objects.all()

    if is_product_group is not None:
        products = _add_annotations(products, is_product_group, with_annotations)

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


def _add_annotations(queryset: QuerySet, is_product_group: bool, with_annotations: bool) -> QuerySet:
    if not with_annotations:
        return queryset

    subquery_open_critical = (
        _get_product_group_observation_subquery(Severity.SEVERITY_CRITICAL)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_CRITICAL)
    )
    subquery_open_high = (
        _get_product_group_observation_subquery(Severity.SEVERITY_HIGH)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_HIGH)
    )
    subquery_open_medium = (
        _get_product_group_observation_subquery(Severity.SEVERITY_MEDIUM)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_MEDIUM)
    )
    subquery_open_low = (
        _get_product_group_observation_subquery(Severity.SEVERITY_LOW)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_LOW)
    )
    subquery_open_none = (
        _get_product_group_observation_subquery(Severity.SEVERITY_NONE)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_NONE)
    )
    subquery_open_unknown = (
        _get_product_group_observation_subquery(Severity.SEVERITY_UNKNOWN)
        if is_product_group
        else _get_product_observation_subquery(Severity.SEVERITY_UNKNOWN)
    )

    queryset = queryset.annotate(
        open_critical_observation_count=Coalesce(subquery_open_critical, 0),
        open_high_observation_count=Coalesce(subquery_open_high, 0),
        open_medium_observation_count=Coalesce(subquery_open_medium, 0),
        open_low_observation_count=Coalesce(subquery_open_low, 0),
        open_none_observation_count=Coalesce(subquery_open_none, 0),
        open_unknown_observation_count=Coalesce(subquery_open_unknown, 0),
    )

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


def _get_product_observation_subquery(severity: str) -> Subquery:
    branch_filter = Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )

    return Subquery(
        Observation.objects.filter(
            branch_filter,
            product=OuterRef("pk"),
            current_status=Status.STATUS_OPEN,
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
            current_status=Status.STATUS_OPEN,
            current_severity=severity,
        )
        .order_by()
        .values("product__product_group")
        .annotate(count=Count("pk"))
        .values("count"),
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
