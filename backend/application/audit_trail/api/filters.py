from django_filters import (
    CharFilter,
    DateTimeFilter,
    FilterSet,
    NumberFilter,
    OrderingFilter,
)

from application.audit_trail.models import Product_Audit_Event


class ProductAuditEventFilter(FilterSet):
    # Not a model choice, the product may have been deleted
    product = NumberFilter(field_name="product_id")
    product_name = CharFilter(field_name="product_name", lookup_expr="icontains")
    created_after = DateTimeFilter(field_name="created", lookup_expr="gte")
    created_before = DateTimeFilter(field_name="created", lookup_expr="lt")

    ordering = OrderingFilter(
        fields=(
            ("created", "created"),
            ("product_name", "product_name"),
            ("user_full_name", "user_full_name"),
            ("object_type", "object_type"),
            ("object_name", "object_name"),
            ("action", "action"),
        ),
    )

    class Meta:
        model = Product_Audit_Event
        fields = ["is_product_group", "user", "object_type", "object_id", "action"]
