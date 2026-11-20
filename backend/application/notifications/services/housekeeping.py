import logging
from datetime import timedelta
from itertools import batched

from django.conf import settings as django_settings
from django.db.models import Exists, OuterRef
from django.utils import timezone

from application.core.models import Product_Authorization_Group_Member, Product_Member
from application.notifications.models import Product_Notification, Webhook_Delivery

logger = logging.getLogger("secobserve.notifications")

BULK_BATCH_SIZE = 1000


def delete_orphaned_product_notifications() -> int:
    """
    Deletes the notification settings of products the user is not a member of anymore, directly
    or through a product group or an authorization group. Rows without a product are the users'
    templates, they are never orphaned.

    The settings of a product group are inherited by its products, so they survive as long as the
    user is a member of one of them. The two clauses for this match nothing for the settings of an
    ordinary product, no product has an ordinary product as its product group.
    """
    orphaned_product_notifications = Product_Notification.objects.filter(
        ~Exists(Product_Member.objects.filter(product=OuterRef("product"), user=OuterRef("user"))),
        ~Exists(Product_Member.objects.filter(product=OuterRef("product__product_group"), user=OuterRef("user"))),
        ~Exists(Product_Member.objects.filter(product__product_group=OuterRef("product"), user=OuterRef("user"))),
        ~Exists(
            Product_Authorization_Group_Member.objects.filter(
                product=OuterRef("product"),
                authorization_group__users=OuterRef("user"),
            )
        ),
        ~Exists(
            Product_Authorization_Group_Member.objects.filter(
                product=OuterRef("product__product_group"),
                authorization_group__users=OuterRef("user"),
            )
        ),
        ~Exists(
            Product_Authorization_Group_Member.objects.filter(
                product__product_group=OuterRef("product"),
                authorization_group__users=OuterRef("user"),
            )
        ),
        product__isnull=False,
    )
    orphaned_product_notification_ids = list(orphaned_product_notifications.values_list("pk", flat=True))

    num_deleted_product_notifications = 0
    for product_notification_ids_batch in batched(orphaned_product_notification_ids, BULK_BATCH_SIZE):
        deleted_objects = Product_Notification.objects.filter(pk__in=product_notification_ids_batch).delete()
        num_deleted_product_notifications += deleted_objects[1].get("notifications.Product_Notification", 0)

    if num_deleted_product_notifications:
        logger.info(  # pylint: disable=logging-fstring-interpolation
            f"Deleted {num_deleted_product_notifications} orphaned product notifications"
        )

    return num_deleted_product_notifications


def delete_old_webhook_deliveries() -> int:
    cutoff = timezone.now() - timedelta(days=django_settings.WEBHOOK_DELIVERY_RETENTION_DAYS)
    old_deliveries = Webhook_Delivery.objects.filter(created__lt=cutoff)

    num_deleted_deliveries = 0
    # Batches keep each delete short, the nightly volume of an OSV run can be large
    while delivery_ids := list(old_deliveries.values_list("pk", flat=True)[:BULK_BATCH_SIZE]):
        num_deleted_deliveries += Webhook_Delivery.objects.filter(pk__in=delivery_ids).delete()[0]

    if num_deleted_deliveries:
        logger.info(  # pylint: disable=logging-fstring-interpolation
            f"Deleted {num_deleted_deliveries} old webhook deliveries"
        )

    return num_deleted_deliveries
