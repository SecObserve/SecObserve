from typing import Optional

from django.db.models import Q, QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import Audit_Log, Product


def get_audit_logs(product: Optional[Product] = None) -> QuerySet[Audit_Log]:
    audit_logs = Audit_Log.objects.all().order_by("-created", "-id")

    if product:
        # The product group decides about the approvers of its products as well
        if product.product_group:
            return audit_logs.filter(Q(product=product) | Q(product=product.product_group))
        return audit_logs.filter(product=product)

    user = get_current_user()
    if user and user.is_superuser:
        return audit_logs

    return Audit_Log.objects.none()
