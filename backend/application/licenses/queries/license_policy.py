from typing import Optional

from django.db.models import Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.queries.product import get_products
from application.licenses.models import License_Policy


def get_license_policy(license_policy_id: int) -> Optional[License_Policy]:
    try:
        return License_Policy.objects.get(id=license_policy_id)
    except License_Policy.DoesNotExist:
        return None


def get_license_policies() -> QuerySet[License_Policy]:
    user = get_current_user()

    if user is None:
        return License_Policy.objects.none()

    license_policies = License_Policy.objects.all().order_by("id")

    if user.is_superuser:
        return license_policies

    products = get_products(is_product_group=False)

    return license_policies.filter(
        Q(users=user) | Q(authorization_groups__users=user) | Q(is_public=True) | Q(product__in=products)
    ).distinct()
