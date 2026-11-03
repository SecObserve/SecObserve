from typing import Any, Optional

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from application.commons.api.permissions import UserHasSuperuserPermission
from application.commons.models import Settings
from application.commons.services.security_gate_conditions import (
    conditions_have_a_rule,
)
from application.core.api.serializers_security_gate import (
    SecurityGatePreviewRequestSerializer,
    SecurityGatePreviewRowSerializer,
)
from application.core.models import Product
from application.core.services.security_gate import (
    SEVERITIES,
    get_security_gate_rules,
    get_security_gate_thresholds,
    preview_security_gate,
    resolve_security_gate_rules,
)


def preview_security_gate_from_request(product: Optional[Product], data: Any) -> list[dict[str, Any]]:
    """Validates a gate draft and previews it for one product, or for all products when none is given."""
    serializer = SecurityGatePreviewRequestSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    draft = serializer.validated_data

    thresholds = get_security_gate_thresholds(product) if product else None
    if thresholds is None:
        settings = Settings.load()
        thresholds = {severity: getattr(settings, f"security_gate_threshold_{severity}") for severity in SEVERITIES}
    for severity in SEVERITIES:
        if draft.get(f"security_gate_threshold_{severity}") is not None:
            thresholds[severity] = draft[f"security_gate_threshold_{severity}"]

    rules = None
    conditions = draft.get("security_gate_conditions")
    if draft.get("security_gate_advanced") and conditions and conditions_have_a_rule(conditions):
        rules = resolve_security_gate_rules(conditions)

    return preview_security_gate(product, thresholds, rules)


def preview_configured_security_gate(product: Product) -> list[dict[str, Any]]:
    """The counts of the gate as it is configured for the product, empty when it has no gate."""
    thresholds = get_security_gate_thresholds(product)
    if thresholds is None:
        return []

    return preview_security_gate(product, thresholds, get_security_gate_rules(product))


class SettingsSecurityGatePreviewView(APIView):
    serializer_class = SecurityGatePreviewRequestSerializer
    permission_classes = (IsAuthenticated, UserHasSuperuserPermission)

    @extend_schema(
        methods=["POST"],
        request=SecurityGatePreviewRequestSerializer,
        responses={HTTP_200_OK: SecurityGatePreviewRowSerializer(many=True)},
    )
    def post(self, request: Request, pk: int = None) -> Response:  # pylint: disable=unused-argument
        # pk is part of the settings path, the settings are a singleton
        rows = preview_security_gate_from_request(None, request.data)
        return Response(SecurityGatePreviewRowSerializer(rows, many=True).data, status=HTTP_200_OK)
