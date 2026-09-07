from typing import Optional

from django.db.models import Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import Product
from application.core.queries.product import get_member_product_ids
from application.notifications.models import Product_Notification


def get_product_notification_by_id(product_notification_id: int) -> Optional[Product_Notification]:
    try:
        return Product_Notification.objects.get(id=product_notification_id)
    except Product_Notification.DoesNotExist:
        return None


def get_product_notifications() -> QuerySet[Product_Notification]:
    user = get_current_user()

    if user is None:
        return Product_Notification.objects.none()

    product_notifications = Product_Notification.objects.all().order_by("product__name", "id")

    if user.is_superuser:
        return product_notifications

    # The settings of a product group are inherited by its products, so they are visible for
    # everybody who is a member of one of them, not only for the members of the product group
    product_ids = get_member_product_ids(user)
    product_group_ids = set(
        Product.objects.filter(pk__in=product_ids, product_group__isnull=False).values_list(
            "product_group_id", flat=True
        )
    )

    # Rows for products the user cannot access anymore are hidden instead of being deleted
    return product_notifications.filter(user=user).filter(
        Q(product__isnull=True) | Q(product_id__in=product_ids | product_group_ids)
    )
