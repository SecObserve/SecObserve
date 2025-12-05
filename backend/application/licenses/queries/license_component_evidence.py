from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import Product_Authorization_Group_Member, Product_Member
from application.licenses.models import License_Component_Evidence


def get_license_component_evidences() -> QuerySet[License_Component_Evidence]:
    user = get_current_user()

    if user is None:
        return License_Component_Evidence.objects.none()

    components = License_Component_Evidence.objects.all()

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("license_component__product_id"), user=user)
        product_group_members = Product_Member.objects.filter(
            product=OuterRef("license_component__product__product_group"), user=user
        )

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("license_component__product_id"), authorization_group__users=user
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("license_component__product__product_group"), authorization_group__users=user
        )

        components = components.annotate(
            license_component__product__member=Exists(product_members),
            license_component__product__product_group__member=Exists(product_group_members),
            license_component__product__authorization_group_member=Exists(product_authorization_group_members),
            license_component__product__product_group_authorization_group_member=Exists(
                product_group_authorization_group_members
            ),
        )

        components = components.filter(
            Q(license_component__product__member=True)
            | Q(license_component__product__product_group__member=True)
            | Q(license_component__product__authorization_group_member=True)
            | Q(license_component__product__product_group_authorization_group_member=True)
        )

    return components
