from typing import Optional

from rest_framework.serializers import (
    CharField,
    ChoiceField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
)

from application.access_control.services.current_user import get_current_user
from application.notifications.models import (
    Notification,
    Notification_Viewed,
    Product_Notification,
)


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


class ProductNotificationSerializer(ModelSerializer):
    product_name = SerializerMethodField()
    user_full_name = SerializerMethodField()

    class Meta:
        model = Product_Notification
        fields = "__all__"
        read_only_fields = ["product", "user"]

    def get_product_name(self, obj: Product_Notification) -> Optional[str]:
        if obj.product:
            return obj.product.name

        return None

    def get_user_full_name(self, obj: Product_Notification) -> Optional[str]:
        if obj.user:
            return obj.user.full_name

        return None


class ProductNotificationPairSerializer(Serializer):
    """
    The settings of a product together with the settings it inherits from. The settings of a product
    are None while the user does not override them, the parent is None for a product group.
    """

    product_notification = ProductNotificationSerializer(allow_null=True)
    parent_notification = ProductNotificationSerializer(allow_null=True)


class NotificationBulkSerializer(Serializer):
    notifications = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)


class WebhookTestSerializer(Serializer):
    webhook_url = CharField(max_length=2048)
    webhook_type = ChoiceField(choices=["msteams", "slack"])
