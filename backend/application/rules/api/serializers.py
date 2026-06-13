import platform
import re
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


class RuleSerializerBase(ModelSerializer):
    user = CharField(read_only=True)
    approval_status = CharField(read_only=True)
    approval_remark = CharField(read_only=True)
    approval_date = DateTimeField(read_only=True)
    approval_user = CharField(read_only=True)
    user_full_name = SerializerMethodField()
    approval_user_full_name = SerializerMethodField()

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

    def validate_title(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_description_observation(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_component_name_version(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_component_purl(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_docker_image_name_tag(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_endpoint_url(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_service_name(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_source_file(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_cloud_qualified_resource(self, value: str) -> str:
        _validate_regex(value)
        return value

    def validate_origin_kubernetes_qualified_resource(self, value: str) -> str:
        _validate_regex(value)
        return value

    def update(self, instance: Rule, validated_data: dict) -> Rule:
        instance.approval_status = ""
        return super().update(instance, validated_data)


def _validate_regex(value: str) -> None:
    try:
        re.compile(value, re.IGNORECASE)
    except re.error as e:
        raise ValidationError(f"Cannot compile regular expression: '{str(e)}'") from e


class GeneralRuleSerializer(RuleSerializerBase):
    class Meta:
        model = Rule
        exclude = ["product"]


class ProductRuleSerializer(RuleSerializerBase):
    product_data = NestedProductSerializer(source="product", read_only=True)

    class Meta:
        model = Rule
        fields = "__all__"

    def validate_product(self, value: Product) -> Product:
        self.instance: Rule
        if self.instance and self.instance.product != value:
            raise ValidationError("Product cannot be changed")

        return value


class RuleApprovalSerializer(Serializer):
    approval_status = ChoiceField(choices=Rule_Status.RULE_STATUS_CHOICES_APPROVAL, required=True)
    approval_remark = CharField(max_length=255, required=True)


class SimulationResultSerializer(Serializer):
    count = IntegerField()
    results = ListField(child=ObservationListSerializer())
