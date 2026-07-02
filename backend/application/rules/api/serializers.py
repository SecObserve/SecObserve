import platform
from typing import Any, Optional

from rest_framework.serializers import (
    CharField,
    ChoiceField,
    DateTimeField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from application.commons.services.functions import validate_vex_remediations
from application.core.api.serializers_observation import ObservationListSerializer
from application.core.api.serializers_product import NestedProductSerializer
from application.core.models import Product
from application.rules.models import Rule
from application.rules.types import Rule_Status, Rule_Type


class GeneralRuleSerializer(ModelSerializer):
    user = CharField(read_only=True)
    approval_status = CharField(read_only=True)
    rejection_remark = CharField(read_only=True)
    approval_date = DateTimeField(read_only=True)
    approval_user = CharField(read_only=True)
    user_full_name = SerializerMethodField()
    approval_user_full_name = SerializerMethodField()

    class Meta:
        model = Rule
        exclude = ["product"]

    def get_user_full_name(self, obj: Rule) -> Optional[str]:
        if obj.user:
            return obj.user.full_name

        return None

    def get_approval_user_full_name(self, obj: Rule) -> Optional[str]:
        if obj.approval_user:
            return obj.approval_user.full_name

        return None

    def validate_description(self, value: str) -> str:
        if not value:
            raise ValidationError("Must be set")

        return value

    def validate_type(self, value: str) -> str:
        if value == Rule_Type.RULE_TYPE_REGO and platform.machine() not in ["x86_64", "AMD64"]:
            raise ValidationError("Rego rules are only supported on 'x86_64' or 'AMD64' architectures")

        return value

    def validate_new_vex_remediations(self, value: Any) -> Optional[list[dict]]:
        return validate_vex_remediations(value)

    def validate(self, attrs: dict) -> dict:
        if attrs.get("type") == Rule_Type.RULE_TYPE_REGO and not attrs.get("rego_module"):
            raise ValidationError("Rego module must be set")

        return super().validate(attrs)

    def update(self, instance: Rule, validated_data: dict) -> Rule:
        instance.approval_status = ""
        return super().update(instance, validated_data)


class ProductRuleSerializer(ModelSerializer):
    product_data = NestedProductSerializer(source="product", read_only=True)
    user = CharField(read_only=True)
    approval_status = CharField(read_only=True)
    rejection_remark = CharField(read_only=True)
    approval_date = DateTimeField(read_only=True)
    approval_user = CharField(read_only=True)
    user_full_name = SerializerMethodField()
    approval_user_full_name = SerializerMethodField()

    class Meta:
        model = Rule
        fields = "__all__"

    def get_user_full_name(self, obj: Rule) -> Optional[str]:
        if obj.user:
            return obj.user.full_name

        return None

    def get_approval_user_full_name(self, obj: Rule) -> Optional[str]:
        if obj.approval_user:
            return obj.approval_user.full_name

        return None

    def validate_description(self, value: str) -> str:
        if not value:
            raise ValidationError("Must be set")

        return value

    def validate_product(self, value: Product) -> Product:
        self.instance: Rule
        if self.instance and self.instance.product != value:
            raise ValidationError("Product cannot be changed")

        return value

    def validate(self, attrs: dict) -> dict:
        if attrs.get("type") == Rule_Type.RULE_TYPE_REGO and not attrs.get("rego_module"):
            raise ValidationError("Rego module must be set")

        return super().validate(attrs)

    def update(self, instance: Rule, validated_data: dict) -> Rule:
        instance.approval_status = ""
        return super().update(instance, validated_data)


class RuleApprovalSerializer(Serializer):
    approval_status = ChoiceField(choices=Rule_Status.RULE_STATUS_CHOICES_APPROVAL, required=True)
    rejection_remark = CharField(max_length=255, required=True, allow_blank=True)


class SimulationResultSerializer(Serializer):
    count = IntegerField()
    results = ListField(child=ObservationListSerializer())
