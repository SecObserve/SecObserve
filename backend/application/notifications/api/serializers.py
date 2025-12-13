from typing import Optional

from rest_framework.serializers import (
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from application.access_control.services.current_user import get_current_user
from application.notifications.models import Notification, Notification_Viewed


class NotificationSerializer(ModelSerializer):
    message = SerializerMethodField()
    product_name = SerializerMethodField()
    observation_title = SerializerMethodField()
    user_full_name = SerializerMethodField()
    new_viewed = SerializerMethodField()

    class Meta:
        model = Notification
        fields = "__all__"

    def get_message(self, obj: Notification) -> Optional[str]:
        if not obj.message:
            return obj.message

        user = get_current_user()
        if user and user.is_superuser:
            return obj.message

        return "..."

    def get_product_name(self, obj: Notification) -> Optional[str]:
        if obj.product:
            return obj.product.name

        if obj.observation:
            return obj.observation.product.name

        return None

    def get_observation_title(self, obj: Notification) -> Optional[str]:
        if obj.observation:
            return obj.observation.title

        return None

    def get_user_full_name(self, obj: Notification) -> Optional[str]:
        if obj.user:
            return obj.user.full_name

        return None

    def get_new_viewed(self, obj: Notification) -> str:
        user = get_current_user()
        if user:
            if Notification_Viewed.objects.filter(notification=obj, user=user).exists():
                return "Viewed"
        return "New"


class NotificationBulkSerializer(Serializer):
    notifications = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)
