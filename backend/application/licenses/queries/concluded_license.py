from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import Product_Authorization_Group_Member, Product_Member
from application.licenses.models import Concluded_License


def get_concluded_license(concluded_license_id: int) -> Optional[Concluded_License]:
    try:
        return Concluded_License.objects.get(id=concluded_license_id)
    except Concluded_License.DoesNotExist:
        return None


def get_concluded_licenses() -> QuerySet[Concluded_License]:
    user = get_current_user()

    if user is None:
        return Concluded_License.objects.none()

    components = Concluded_License.objects.all()

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
