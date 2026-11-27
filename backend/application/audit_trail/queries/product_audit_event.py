from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.audit_trail.models import Product_Audit_Event
from application.core.queries.product import get_products


def get_product_audit_events() -> QuerySet[Product_Audit_Event]:
    user = get_current_user()

    if user is None:
        return Product_Audit_Event.objects.none()

    product_audit_events = Product_Audit_Event.objects.all().order_by("-created", "-id")

    # Only superusers can see the events of deleted products
    if user.is_superuser:
        return product_audit_events

    return product_audit_events.filter(product__in=get_products())
