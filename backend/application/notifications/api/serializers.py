from typing import Any, Optional
from urllib.parse import urlsplit

from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from application.access_control.services.current_user import get_current_user
from application.commons.services.functions import get_comma_separated_as_list
from application.core.api.serializers_product import (
    NestedProductSerializer,
    NestedProductSerializerSmall,
)
from application.notifications.models import (
    Notification,
    Notification_Viewed,
    Product_Notification,
    Webhook,
    Webhook_Delivery,
)
from application.notifications.types import Webhook_Event_Type


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
    product_data = NestedProductSerializerSmall(source="product", read_only=True)

    class Meta:
        model = Product_Notification
        fields = "__all__"
        read_only_fields = ["product", "user"]


class ProductNotificationPairSerializer(Serializer):
    product_notification = ProductNotificationSerializer(allow_null=True)
    template_notification = ProductNotificationSerializer(allow_null=True)


class NotificationBulkSerializer(Serializer):
    notifications = ListField(child=IntegerField(min_value=1), min_length=0, max_length=250, required=True)


class WebhookTestSerializer(Serializer):
    webhook_url = CharField(max_length=2048)
    webhook_type = ChoiceField(choices=["msteams", "slack"])


class WebhookEventTypesField(ListField):
    """A list in the API, a comma separated string in the model."""

    child = ChoiceField(choices=Webhook_Event_Type.SUBSCRIBABLE)

    def to_representation(self, data: str) -> list[str]:  # type: ignore[override]
        return get_comma_separated_as_list(data)

    def to_internal_value(self, data: Any) -> str:  # type: ignore[override]
        return ",".join(dict.fromkeys(super().to_internal_value(data)))


class WebhookSerializer(ModelSerializer):
    product_data = NestedProductSerializer(source="product", read_only=True)
    event_types = WebhookEventTypesField(allow_empty=False)

    class Meta:
        model = Webhook
        exclude = ["secret"]
        read_only_fields = ["consecutive_failures", "next_attempt_at"]

    def validate_url(self, url: str) -> str:
        # The network policy needs DNS and is enforced when sending
        try:
            parts = urlsplit(url)
            valid = parts.scheme in ("http", "https") and bool(parts.hostname)
        except ValueError:
            valid = False
        if not valid:
            raise ValidationError("URL must start with http:// or https:// and contain a host")
        return url

    def validate(self, attrs: dict) -> dict:
        if self.instance and "product" in attrs and attrs["product"] != self.instance.product:
            raise ValidationError("Product cannot be changed")
        return attrs

    def update(self, instance: Webhook, validated_data: dict) -> Webhook:
        for field, value in validated_data.items():
            setattr(instance, field, value)
        # Breaks a running drain's lease and clears a backoff, without overwriting the columns the drain writes
        instance.next_attempt_at = None
        instance.save(update_fields=[*validated_data, "next_attempt_at"])
        return instance


class WebhookCreateSerializer(WebhookSerializer):
    secret = CharField(read_only=True)

    class Meta:
        model = Webhook
        fields = "__all__"
        read_only_fields = WebhookSerializer.Meta.read_only_fields


class WebhookSecretSerializer(Serializer):
    secret = CharField()


class WebhookSendTestResultSerializer(Serializer):
    succeeded = BooleanField()
    status_code = IntegerField(allow_null=True)
    error = CharField(allow_blank=True)


class WebhookDeliverySerializer(ModelSerializer):
    class Meta:
        model = Webhook_Delivery
        fields = "__all__"
