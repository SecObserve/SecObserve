from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.scancodeio.models import ScanCodeIO_Project


def get_scancodeio_project_by_product(product: Product) -> Optional[ScanCodeIO_Project]:
    try:
        return ScanCodeIO_Project.objects.get(product=product)
    except ScanCodeIO_Project.DoesNotExist:
        return None


def get_scancodeio_project_by_webhook_token_hash(webhook_token_hash: str) -> Optional[ScanCodeIO_Project]:
    try:
        return ScanCodeIO_Project.objects.get(webhook_token_hash=webhook_token_hash)
    except ScanCodeIO_Project.DoesNotExist:
        return None


def get_scancodeio_projects() -> QuerySet[ScanCodeIO_Project]:
    user = get_current_user()

    if user is None:
        return ScanCodeIO_Project.objects.none()

    scancodeio_projects = ScanCodeIO_Project.objects.all().order_by("id")

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

        scancodeio_projects = scancodeio_projects.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        scancodeio_projects = scancodeio_projects.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
        )

    return scancodeio_projects


def get_scancodeio_project_by_id(scancodeio_project_id: int) -> Optional[ScanCodeIO_Project]:
    try:
        return ScanCodeIO_Project.objects.select_related("product").get(pk=scancodeio_project_id)
    except ScanCodeIO_Project.DoesNotExist:
        return None
