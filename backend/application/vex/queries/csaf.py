from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import Product_Authorization_Group_Member, Product_Member
from application.vex.models import CSAF, CSAF_Branch, CSAF_Vulnerability


def get_csafs() -> QuerySet[CSAF]:
    user = get_current_user()

    if user is None:
        return CSAF.objects.none()

    csafs = CSAF.objects.all().order_by("id")

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

        csafs = csafs.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        csafs = csafs.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
            | (Q(product__isnull=True) & Q(user=user))
        )

    return csafs


def get_csaf_by_document_id(document_id_prefix: str, document_base_id: str) -> Optional[CSAF]:
    user = get_current_user()

    if user is None:
        return None

    try:
        csaf = CSAF.objects.get(document_id_prefix=document_id_prefix, document_base_id=document_base_id)
        if not user.is_superuser and csaf not in get_csafs():
            return None
        return csaf
    except CSAF.DoesNotExist:
        return None


def get_csaf_vulnerabilities() -> QuerySet[CSAF_Vulnerability]:
    user = get_current_user()

    if user is None:
        return CSAF_Vulnerability.objects.none()

    if user.is_superuser:
        return CSAF_Vulnerability.objects.all().order_by("name")

    return CSAF_Vulnerability.objects.filter(csaf__in=get_csafs()).order_by("name")


def get_csaf_branches() -> QuerySet[CSAF_Branch]:
    user = get_current_user()

    if user is None:
        return CSAF_Branch.objects.none()

    if user.is_superuser:
        return CSAF_Branch.objects.all().order_by("branch__name")

    return CSAF_Branch.objects.filter(csaf__in=get_csafs()).order_by("branch__name")
