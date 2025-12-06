from typing import Optional

from django.db.models import Count, Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Branch,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.licenses.models import License_Component


def get_license_component(license_component_id: int) -> Optional[License_Component]:
    try:
        return License_Component.objects.get(id=license_component_id)
    except License_Component.DoesNotExist:
        return None


def get_license_components() -> QuerySet[License_Component]:
    user = get_current_user()

    if user is None:
        return License_Component.objects.none()

    components = License_Component.objects.all()

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("product_id"), user=user)
        product_group_members = Product_Member.objects.filter(product=OuterRef("product__product_group"), user=user)

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product_id"), authorization_group__users=user
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product__product_group"), authorization_group__users=user
        )

        components = components.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            product__authorization_group_member=Exists(product_authorization_group_members),
            product__product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        components = components.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(product__authorization_group_member=True)
            | Q(product__product_group_authorization_group_member=True)
        )

    return components


def get_license_component_licenses(
    product: Product, branch: Optional[Branch], order_by_1: str, order_by2: str, order_by_3: str
) -> QuerySet:
    license_components = get_license_components().filter(product=product)
    if branch:
        license_components = license_components.filter(branch=branch)

    license_components_overview = license_components.values(
        "branch__name",
        "effective_spdx_license__spdx_id",
        "effective_spdx_license__name",
        "effective_license_expression",
        "effective_non_spdx_license",
        "effective_multiple_licenses",
        "evaluation_result",
    ).annotate(Count("id"))

    if order_by_1:
        return license_components_overview.order_by(order_by_1, order_by2, order_by_3)

    return license_components_overview.order_by("numerical_evaluation_result", "effective_license_name", "branch__name")
