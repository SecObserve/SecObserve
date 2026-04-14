from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import Product_Authorization_Group_Member, Product_Member
from application.vex.models import OpenVEX, OpenVEX_Branch, OpenVEX_Vulnerability


def get_openvex_s() -> QuerySet[OpenVEX]:
    user = get_current_user()

    if user is None:
        return OpenVEX.objects.none()

    openvex_s = OpenVEX.objects.all().order_by("id")

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

        openvex_s = openvex_s.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        openvex_s = openvex_s.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
            | (Q(product__isnull=True) & Q(user=user))
        )

    return openvex_s


def get_openvex_by_document_id(document_id_prefix: str, document_base_id: str) -> Optional[OpenVEX]:
    user = get_current_user()

    if user is None:
        return None

    try:
        openvex = OpenVEX.objects.get(
            document_id_prefix=document_id_prefix,
            document_base_id=document_base_id,
        )
        if not user.is_superuser and openvex not in get_openvex_s():
            return None
        return openvex
    except OpenVEX.DoesNotExist:
        return None


def get_openvex_vulnerabilities() -> QuerySet[OpenVEX_Vulnerability]:
    user = get_current_user()

    if user is None:
        return OpenVEX_Vulnerability.objects.none()

    if user.is_superuser:
        return OpenVEX_Vulnerability.objects.all().order_by("name")

    return OpenVEX_Vulnerability.objects.filter(openvex__in=get_openvex_s()).order_by("name")


def get_openvex_branches() -> QuerySet[OpenVEX_Branch]:
    user = get_current_user()

    if user is None:
        return OpenVEX_Branch.objects.none()

    if user.is_superuser:
        return OpenVEX_Branch.objects.all().order_by("branch__name")

    return OpenVEX_Branch.objects.filter(openvex__in=get_openvex_s()).order_by("branch__name")
