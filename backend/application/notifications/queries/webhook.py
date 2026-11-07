from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.queries.product import get_products
from application.notifications.models import Webhook, Webhook_Delivery


def get_webhooks() -> QuerySet[Webhook]:
    user = get_current_user()

    if user is None:
        return Webhook.objects.none()

    webhooks = Webhook.objects.all().order_by("id")

    if user.is_superuser:
        return webhooks

    # Products and product groups the user is a member of, global webhooks have no product
    return webhooks.filter(product__in=get_products())


def get_webhook_deliveries() -> QuerySet[Webhook_Delivery]:
    return Webhook_Delivery.objects.filter(webhook__in=get_webhooks()).order_by("-id")
