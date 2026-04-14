from typing import Optional

from django.db.models import Max
from django.db.models.query import QuerySet

from application.access_control.models import Authorization_Group, User
from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.core.queries.product import get_products


def get_product_member(product: Product, user: User = None) -> Optional[Product_Member]:
    if not user:
        user = get_current_user()

    try:
        return Product_Member.objects.get(product=product, user=user)
    except Product_Member.DoesNotExist:
        return None


def get_product_members() -> QuerySet[Product_Member]:
    user = get_current_user()

    if user is None:
        return Product_Member.objects.none()

    product_members = Product_Member.objects.exclude(user__username__startswith="-product-").order_by("id")

    if user.is_superuser:
        return product_members

    products = get_products()
    return product_members.filter(product__in=products)


def get_product_authorization_group_member(
    product: Product, authorization_group: Authorization_Group
) -> Optional[Product_Authorization_Group_Member]:
    try:
        return Product_Authorization_Group_Member.objects.get(product=product, authorization_group=authorization_group)
    except Product_Authorization_Group_Member.DoesNotExist:
        return None


def get_product_authorization_group_members() -> QuerySet[Product_Authorization_Group_Member]:
    user = get_current_user()

    if user is None:
        return Product_Authorization_Group_Member.objects.none()

    product_authorization_group_members = Product_Authorization_Group_Member.objects.all().order_by("id")

    if user.is_superuser:
        return product_authorization_group_members

    products = get_products()
    return product_authorization_group_members.filter(product__in=products)


def get_highest_role_of_product_authorization_group_members_for_user(product: Product, user: User = None) -> int:
    if not user:
        user = get_current_user()

    highest_product_role = Product_Authorization_Group_Member.objects.filter(
        product=product,
        authorization_group__users=user,
    ).aggregate(Max("role", default=0))["role__max"]

    if product.product_group:
        highest_product_group_role = Product_Authorization_Group_Member.objects.filter(
            product=product.product_group,
            authorization_group__users=user,
        ).aggregate(Max("role", default=0))["role__max"]

        if highest_product_group_role:
            highest_product_role = max(highest_product_role, highest_product_group_role)

    return highest_product_role
