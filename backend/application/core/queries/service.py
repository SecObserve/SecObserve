from typing import Optional

from django.db.models import Count, Exists, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Observation,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
    Service,
)
from application.core.types import Severity, Status
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result


def get_service_by_id(product: Product, service_id: int) -> Optional[Service]:
    try:
        return Service.objects.get(id=service_id, product=product)
    except Service.DoesNotExist:
        return None


def get_service_by_name(product: Product, name: str) -> Optional[Service]:
    try:
        return Service.objects.get(name=name, product=product)
    except Service.DoesNotExist:
        return None


def get_services(with_annotations: bool = False) -> QuerySet[Service]:
    user = get_current_user()

    if user is None:
        return Service.objects.none()

    services = Service.objects.all()
    services = _add_annotations(services, with_annotations)

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("product_id"), user=user)
        product_group_members = Product_Member.objects.filter(product=OuterRef("product__product_group"), user=user)

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product_id"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product__product_group"),
            authorization_group__users=user,
        )

        services = services.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        services = services.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
        )

    return services


def _add_annotations(queryset: QuerySet, with_annotations: bool) -> QuerySet:
    if not with_annotations:
        return queryset

    subquery_open_critical = _get_observation_subquery(Severity.SEVERITY_CRITICAL)
    subquery_open_high = _get_observation_subquery(Severity.SEVERITY_HIGH)
    subquery_open_medium = _get_observation_subquery(Severity.SEVERITY_MEDIUM)
    subquery_open_low = _get_observation_subquery(Severity.SEVERITY_LOW)
    subquery_open_none = _get_observation_subquery(Severity.SEVERITY_NONE)
    subquery_open_unknown = _get_observation_subquery(Severity.SEVERITY_UNKNOWN)

    subquery_license_forbidden = _get_license_subquery(License_Policy_Evaluation_Result.RESULT_FORBIDDEN)
    subquery_license_review_required = _get_license_subquery(License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED)
    subquery_license_unknown = _get_license_subquery(License_Policy_Evaluation_Result.RESULT_UNKNOWN)
    subquery_license_allowed = _get_license_subquery(License_Policy_Evaluation_Result.RESULT_ALLOWED)
    subquery_license_ignored = _get_license_subquery(License_Policy_Evaluation_Result.RESULT_IGNORED)

    queryset = queryset.annotate(
        open_critical_observation_count=Coalesce(subquery_open_critical, 0),
        open_high_observation_count=Coalesce(subquery_open_high, 0),
        open_medium_observation_count=Coalesce(subquery_open_medium, 0),
        open_low_observation_count=Coalesce(subquery_open_low, 0),
        open_none_observation_count=Coalesce(subquery_open_none, 0),
        open_unknown_observation_count=Coalesce(subquery_open_unknown, 0),
        forbidden_licenses_count=Coalesce(subquery_license_forbidden, 0),
        review_required_licenses_count=Coalesce(subquery_license_review_required, 0),
        unknown_licenses_count=Coalesce(subquery_license_unknown, 0),
        allowed_licenses_count=Coalesce(subquery_license_allowed, 0),
        ignored_licenses_count=Coalesce(subquery_license_ignored, 0),
    )

    return queryset


def _get_observation_subquery(severity: str) -> Subquery:
    branch_filter = Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )

    return Subquery(
        Observation.objects.filter(
            branch_filter,
            origin_service=OuterRef("pk"),
            current_status=Status.STATUS_OPEN,
            current_severity=severity,
        )
        .order_by()
        .values("origin_service")
        .annotate(count=Count("pk"))
        .values("count"),
        output_field=IntegerField(),
    )


def _get_license_subquery(evaluation_result: str) -> Subquery:
    branch_filter = Q(branch__is_default_branch=True) | (
        Q(branch__isnull=True) & Q(product__repository_default_branch__isnull=True)
    )

    return Subquery(
        License_Component.objects.filter(
            branch_filter,
            origin_service=OuterRef("pk"),
            evaluation_result=evaluation_result,
        )
        .order_by()
        .values("origin_service")
        .annotate(count=Count("pk"))
        .values("count"),
        output_field=IntegerField(),
    )
