from typing import Any

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    CharField,
    IntegerField,
    JSONField,
    Serializer,
)

from application.commons.services.security_gate_conditions import (
    normalize_security_gate_conditions,
)


class SecurityGatePreviewRequestSerializer(Serializer):
    """The draft of a security gate: thresholds not given fall back to the effective ones."""

    security_gate_advanced = BooleanField(required=False, default=False)
    security_gate_conditions = JSONField(required=False, allow_null=True)
    security_gate_threshold_critical = IntegerField(required=False, min_value=0, max_value=999999)
    security_gate_threshold_high = IntegerField(required=False, min_value=0, max_value=999999)
    security_gate_threshold_medium = IntegerField(required=False, min_value=0, max_value=999999)
    security_gate_threshold_low = IntegerField(required=False, min_value=0, max_value=999999)
    security_gate_threshold_none = IntegerField(required=False, min_value=0, max_value=999999)
    security_gate_threshold_unknown = IntegerField(required=False, min_value=0, max_value=999999)

    def validate_security_gate_conditions(self, value: Any) -> dict[str, Any]:
        try:
            return normalize_security_gate_conditions(value)
        except ValueError as error:
            raise ValidationError(str(error)) from error


class SecurityGatePreviewRowSerializer(Serializer):
    severity = CharField()
    threshold = IntegerField()
    active = IntegerField()
    counted = IntegerField()
    passed = BooleanField()
    # Settings preview only: the products using the instance-wide gate that exceed the threshold
    products_failed = IntegerField(required=False)
