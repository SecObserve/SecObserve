import json
import uuid
from functools import partial
from typing import Any, Callable, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone

from application.commons.services.functions import (
    get_base_url_frontend,
    get_comma_separated_as_list,
)
from application.core.models import (
    Branch,
    Observation,
    Observation_Log,
    Product,
    Service,
)
from application.core.types import Severity
from application.notifications.models import Webhook, Webhook_Delivery
from application.notifications.services.webhook_delivery import kick_webhooks
from application.notifications.types import Webhook_Event_Type
from application.rules.models import Rule


def build_webhook_payload(event_type: str, data: dict[str, Any]) -> str:
    return json.dumps(
        {"type": event_type, "timestamp": timezone.now().isoformat(), "data": data}, cls=DjangoJSONEncoder
    )


def emit_observation_event(event_type: str, observation: Observation) -> None:
    _emit(
        event_type,
        observation.product,
        lambda: {"product": _product(observation.product), "observation": _observation(observation)},
        observation,
    )


def emit_assessment_event(event_type: str, observation_log: Observation_Log) -> None:
    observation = observation_log.observation
    _emit(
        event_type,
        observation.product,
        lambda: {
            "product": _product(observation.product),
            "observation": _observation(observation),
            "assessment": _assessment(observation_log),
        },
        observation,
    )


def emit_rule_event(event_type: str, rule: Rule) -> None:
    _emit(event_type, rule.product, lambda: {"product": _product(rule.product), "rule": _rule(rule)})


def emit_import_event(  # pylint: disable=too-many-arguments
    *,
    product: Product,
    branch: Optional[Branch],
    service: Optional[Service],
    parser_name: str,
    filename: str,
    api_configuration_name: str,
    numbers: tuple[int, int, int],
) -> None:
    _emit(
        Webhook_Event_Type.IMPORT_COMPLETED,
        product,
        lambda: {
            "product": _product(product),
            "import": {
                "parser": parser_name,
                "branch": branch.name if branch else None,
                "service": service.name if service else None,
                "filename": filename,
                "api_configuration": api_configuration_name,
                "observations_new": numbers[0],
                "observations_updated": numbers[1],
                "observations_resolved": numbers[2],
            },
        },
    )


def emit_security_gate_event(product: Product) -> None:
    _emit(Webhook_Event_Type.SECURITY_GATE_CHANGED, product, lambda: {"product": _product(product)})


def _emit(
    event_type: str,
    product: Optional[Product],
    build_data: Callable[[], dict[str, Any]],
    observation: Optional[Observation] = None,
) -> None:
    """Rows join the producer's transaction; the kick runs after commit and cannot fail the request."""
    webhooks = [
        webhook
        for webhook in Webhook.objects.filter(active=True).only("pk", "product_id", "event_types", "min_severity")
        if event_type in get_comma_separated_as_list(webhook.event_types)
        and _matches_scope(webhook, product)
        and _matches_severity(webhook, observation)
    ]
    if not webhooks:
        return

    payload = build_webhook_payload(event_type, build_data())
    event_id = uuid.uuid4()
    Webhook_Delivery.objects.bulk_create(
        Webhook_Delivery(webhook=webhook, event_id=event_id, event_type=event_type, payload=payload)
        for webhook in webhooks
    )
    transaction.on_commit(partial(kick_webhooks, [webhook.pk for webhook in webhooks]), robust=True)


def _matches_scope(webhook: Webhook, product: Optional[Product]) -> bool:
    if webhook.product_id is None:
        return True
    return product is not None and webhook.product_id in (product.pk, product.product_group_id)


def _matches_severity(webhook: Webhook, observation: Optional[Observation]) -> bool:
    if not webhook.min_severity or observation is None:
        return True
    return observation.numerical_severity <= Severity.NUMERICAL_SEVERITIES[webhook.min_severity]


def _url(path: str) -> str:
    return f"{get_base_url_frontend()}#/{path}/show"


def _product(product: Optional[Product]) -> Optional[dict[str, Any]]:
    if product is None:
        return None
    return {
        "id": product.pk,
        "name": product.name,
        "product_group": (
            {"id": product.product_group.pk, "name": product.product_group.name} if product.product_group else None
        ),
        "security_gate_passed": product.security_gate_passed,
        "url": _url(f"products/{product.pk}"),
    }


def _observation(observation: Observation) -> dict[str, Any]:
    return {
        "id": observation.pk,
        "title": observation.title,
        "severity": observation.current_severity,
        "status": observation.current_status,
        "priority": observation.current_priority,
        "vulnerability_id": observation.vulnerability_id,
        "component": observation.origin_component_name_version,
        "branch": observation.branch.name if observation.branch else None,
        "service": observation.origin_service.name if observation.origin_service else None,
        "scanner": observation.scanner,
        "url": _url(f"observations/{observation.pk}"),
    }


def _assessment(observation_log: Observation_Log) -> dict[str, Any]:
    approval_user = observation_log.approval_user
    return {
        "id": observation_log.pk,
        "user": observation_log.user.username,
        "severity": observation_log.severity,
        "status": observation_log.status,
        "priority": observation_log.priority,
        "comment": observation_log.comment,
        "assessment_status": observation_log.assessment_status,
        "approval_user": approval_user.username if approval_user else None,
        "rejection_remark": observation_log.rejection_remark,
        "url": _url(f"observation_logs/{observation_log.pk}"),
    }


def _rule(rule: Rule) -> dict[str, Any]:
    scope, path = ("product", "product_rules") if rule.product else ("general", "general_rules")
    return {
        "id": rule.pk,
        "name": rule.name,
        "scope": scope,
        "user": rule.user.username if rule.user else None,
        "approval_status": rule.approval_status,
        "approval_user": rule.approval_user.username if rule.approval_user else None,
        "rejection_remark": rule.rejection_remark,
        "url": _url(f"{path}/{rule.pk}"),
    }
