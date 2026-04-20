from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import Product_Authorization_Group_Member, Product_Member
from application.vex.models import CycloneDX, CycloneDX_Branch, CycloneDX_Vulnerability


def get_cyclonedx_s() -> QuerySet[CycloneDX]:
    user = get_current_user()

    if user is None:
        return CycloneDX.objects.none()

    cyclonedx_s = CycloneDX.objects.all().order_by("id")

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

        cyclonedx_s = cyclonedx_s.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        cyclonedx_s = cyclonedx_s.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
            | (Q(product__isnull=True) & Q(user=user))
        )

    return cyclonedx_s


def get_cyclonedx_by_document_id(document_id_prefix: str, document_base_id: str) -> Optional[CycloneDX]:
    user = get_current_user()

    if user is None:
        return None

    try:
        cyclonedx = CycloneDX.objects.get(
            document_id_prefix=document_id_prefix,
            document_base_id=document_base_id,
        )
        if not user.is_superuser and cyclonedx not in get_cyclonedx_s():
            return None
        return cyclonedx
    except CycloneDX.DoesNotExist:
        return None


def get_cyclonedx_vulnerabilities() -> QuerySet[CycloneDX_Vulnerability]:
    user = get_current_user()

    if user is None:
        return CycloneDX_Vulnerability.objects.none()

    if user.is_superuser:
        return CycloneDX_Vulnerability.objects.all().order_by("name")

    return CycloneDX_Vulnerability.objects.filter(cyclonedx__in=get_cyclonedx_s()).order_by("name")


def get_cyclonedx_branches() -> QuerySet[CycloneDX_Branch]:
    user = get_current_user()

    if user is None:
        return CycloneDX_Branch.objects.none()

    if user.is_superuser:
        return CycloneDX_Branch.objects.all().order_by("branch__name")

    return CycloneDX_Branch.objects.filter(cyclonedx__in=get_cyclonedx_s()).order_by("branch__name")
