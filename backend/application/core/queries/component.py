from typing import Optional

from django.conf import settings
from django.db import connection
from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Component,
    Observation,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.core.types import Status
from application.licenses.models import License_Component


def get_component_by_id(component_id: str) -> Optional[Component]:
    # _create_component_view()

    # try:
    #     return Component.objects.get(id=component_id)
    # except Component.DoesNotExist:
    return None


def get_components() -> QuerySet[Component]:
    # _create_component_view()

    # user = get_current_user()

    # if user is None:
    #     return Component.objects.none()

    components = Component.objects.all().order_by("id")

    active_observations = Observation.objects.filter(
        origin_component=OuterRef("pk"),
        current_status__in=Status.STATUS_ACTIVE,
    )
    license_components = License_Component.objects.filter(component=OuterRef("pk"))

    components = components.annotate(
        has_observations=Exists(active_observations),
        has_licenses=Exists(license_components),
    )

    # if not user.is_superuser:
    #     product_members = Product_Member.objects.filter(product=OuterRef("product_id"), user=user)
    #     product_group_members = Product_Member.objects.filter(product=OuterRef("product__product_group"), user=user)

    #     product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
    #         product=OuterRef("product_id"),
    #         authorization_group__users=user,
    #     )

    #     product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
    #         product=OuterRef("product__product_group"),
    #         authorization_group__users=user,
    #     )

    #     components = components.annotate(
    #         product__member=Exists(product_members),
    #         product__product_group__member=Exists(product_group_members),
    #         authorization_group_member=Exists(product_authorization_group_members),
    #         product_group_authorization_group_member=Exists(product_group_authorization_group_members),
    #     )

    #     components = components.filter(
    #         Q(product__member=True)
    #         | Q(product__product_group__member=True)
    #         | Q(authorization_group_member=True)
    #         | Q(product_group_authorization_group_member=True)
    #     )

    return components
