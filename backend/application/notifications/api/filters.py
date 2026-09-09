from typing import Any

from django.db.models import QuerySet, Subquery
from django_filters import BooleanFilter, CharFilter, FilterSet, OrderingFilter

from application.access_control.services.current_user import get_current_user
from application.notifications.models import (
    Notification,
    Notification_Viewed,
    Product_Notification,
)


class NotificationFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="icontains")
    message = CharFilter(field_name="message", lookup_expr="icontains")
    function = CharFilter(field_name="function", lookup_expr="icontains")
    exclude_already_viewed = BooleanFilter(field_name="exclude_already_viewed", method="get_exclude_already_viewed")

    def get_exclude_already_viewed(
        self,
        queryset: QuerySet,
        name: Any,  # pylint: disable=unused-argument
        value: Any,
    ) -> QuerySet:
        # field_name is used as a positional argument
        user = get_current_user()
        if not user:
            return queryset

        if value:
            return queryset.exclude(
                id__in=Subquery(Notification_Viewed.objects.filter(user=user).values_list("notification_id", flat=True))
            )

        return queryset

    ordering = OrderingFilter(
        fields=(
            ("name", "name"),
            ("created", "created"),
            ("message", "message"),
            ("type", "type"),
            ("function", "function"),
            ("product__name", "product_name"),
            ("observation__title", "observation_title"),
            ("user__full_name", "user_full_name"),
        ),
    )

    class Meta:
        model = Notification
        fields = [
            "name",
            "created",
            "message",
            "type",
            "function",
            "product",
            "observation",
            "user",
        ]


class ProductNotificationFilter(FilterSet):
    ordering = OrderingFilter(
        fields=(
            ("product__name", "product_data.name"),
            ("user__full_name", "user"),
        ),
    )

    class Meta:
        model = Product_Notification
        fields = [
            "product",
            "user",
        ]
