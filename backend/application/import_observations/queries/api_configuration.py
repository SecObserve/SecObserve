from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.import_observations.models import Api_Configuration


def get_api_configuration_by_id(
    api_configuration_id: int,
) -> Optional[Api_Configuration]:
    try:
        return Api_Configuration.objects.get(id=api_configuration_id)
    except Api_Configuration.DoesNotExist:
        return None


def get_api_configuration_by_name(product: Product, name: str) -> Optional[Api_Configuration]:
    try:
        return Api_Configuration.objects.get(product=product, name=name)
    except Api_Configuration.DoesNotExist:
        return None


def get_api_configurations() -> QuerySet[Api_Configuration]:
    user = get_current_user()

    if user is None:
        return Api_Configuration.objects.none()

    api_configurations = Api_Configuration.objects.all().order_by("id")

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

        api_configurations = api_configurations.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        api_configurations = api_configurations.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
        )

    return api_configurations
