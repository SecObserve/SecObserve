from typing import Optional

from rest_framework.serializers import (
    BooleanField,
    CharField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
    SerializerMethodField,
    ValidationError,
)

from application.core.api.serializers_helpers import validate_cpe23, validate_purl
from application.core.models import Branch, Component, Product, Service
from application.core.services.security_gate import (
    evaluate_security_gate,
    get_security_gate_priority_thresholds,
    get_security_gate_thresholds,
)


class ComponentSerializer(ModelSerializer):
    # has_active_observations, has_inactive_observations and has_licenses are annotated in get_components()
    has_active_observations = BooleanField(read_only=True)
    has_inactive_observations = BooleanField(read_only=True)
    has_licenses = BooleanField(read_only=True)

    class Meta:
        model = Component
        fields = "__all__"


class ComponentNameSerializer(ModelSerializer):
    class Meta:
        model = Component
        fields = ["id", "name_version"]


class PURLTypeElementSerializer(Serializer):
    id = CharField()
    name = CharField()


class PURLTypeSerializer(Serializer):
    count = IntegerField()
    results = ListField(child=PURLTypeElementSerializer())


class BranchSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()
    active_critical_observation_count = IntegerField(read_only=True)
    active_high_observation_count = IntegerField(read_only=True)
    active_medium_observation_count = IntegerField(read_only=True)
    active_low_observation_count = IntegerField(read_only=True)
    active_none_observation_count = IntegerField(read_only=True)
    active_unknown_observation_count = IntegerField(read_only=True)
    forbidden_licenses_count = IntegerField(read_only=True)
    review_required_licenses_count = IntegerField(read_only=True)
    unknown_licenses_count = IntegerField(read_only=True)
    allowed_licenses_count = IntegerField(read_only=True)
    ignored_licenses_count = IntegerField(read_only=True)
    security_gate_passed = SerializerMethodField()

    def validate_purl(self, purl: str) -> str:
        return validate_purl(purl)

    def validate_cpe23(self, cpe23: str) -> str:
        return validate_cpe23(cpe23)

    def get_name_with_product(self, obj: Service) -> str:
        return f"{obj.name} ({obj.product.name})"

    def get_security_gate_passed(self, obj: Branch) -> Optional[bool]:
        # Responses of create and update are not annotated with the observation counts
        if getattr(obj, "active_critical_observation_count", None) is None:
            return None

        thresholds = get_security_gate_thresholds(obj.product)
        if thresholds is None:
            return None

        return evaluate_security_gate(obj, thresholds, get_security_gate_priority_thresholds(obj.product))

    class Meta:
        model = Branch
        fields = "__all__"

    def validate(self, attrs: dict) -> dict:  # pylint: disable=too-many-branches
        if attrs.get("osv_linux_release") and not attrs.get("osv_linux_distribution"):
            raise ValidationError("osv_linux_release cannot be set without osv_linux_distribution")

        return super().validate(attrs)

    def validate_product(self, value: Product) -> Product:
        if self.instance and self.instance.product != value:
            raise ValidationError("Product cannot be changed")

        return value


class BranchNameSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()

    class Meta:
        model = Branch
        fields = ["id", "name", "name_with_product"]

    def get_name_with_product(self, obj: Branch) -> str:
        return f"{obj.name} ({obj.product.name})"


class ServiceSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()
    active_critical_observation_count = IntegerField(read_only=True)
    active_high_observation_count = IntegerField(read_only=True)
    active_medium_observation_count = IntegerField(read_only=True)
    active_low_observation_count = IntegerField(read_only=True)
    active_none_observation_count = IntegerField(read_only=True)
    active_unknown_observation_count = IntegerField(read_only=True)
    forbidden_licenses_count = IntegerField(read_only=True)
    review_required_licenses_count = IntegerField(read_only=True)
    unknown_licenses_count = IntegerField(read_only=True)
    allowed_licenses_count = IntegerField(read_only=True)
    ignored_licenses_count = IntegerField(read_only=True)

    class Meta:
        model = Service
        fields = "__all__"

    def get_name_with_product(self, obj: Service) -> str:
        return f"{obj.name} ({obj.product.name})"

    def validate_product(self, value: Product) -> Product:
        if self.instance and self.instance.product != value:
            raise ValidationError("Product cannot be changed")

        return value


class ServiceNameSerializer(ModelSerializer):
    name_with_product = SerializerMethodField()

    class Meta:
        model = Branch
        fields = ["id", "name", "name_with_product"]

    def get_name_with_product(self, obj: Service) -> str:
        return f"{obj.name} ({obj.product.name})"
