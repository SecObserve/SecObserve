from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from django.db.models import QuerySet
from django.db.models.signals import m2m_changed, post_delete, post_save

from application.audit_trail.services.audit_trail import (
    create_audit_event,
    get_changes,
)
from application.audit_trail.types import Audit_Action, Audit_Object_Type
from application.core.models import Product


@dataclass(frozen=True)
class Tracked_Model:
    object_type: str
    get_product: Callable[[Any], Optional[Product]] = lambda instance: instance.product
    get_name: Callable[[Any], str] = str
    ignored_fields: set[str] = field(default_factory=set)
    masked_fields: set[str] = field(default_factory=set)


# Lazy model references, so that the app doesn't need to import apps from higher layers
TRACKED_MODELS = {
    "core.Product": Tracked_Model(
        object_type=Audit_Object_Type.PRODUCT,
        get_product=lambda instance: instance,
        ignored_fields={
            "last_observation_change",
            "last_license_change",
            "security_gate_passed",
            "has_cloud_resource",
            "has_component",
            "has_docker_image",
            "has_endpoint",
            "has_kubernetes_resource",
            "has_source",
            "has_potential_duplicates",
        },
        masked_fields={"issue_tracker_api_key", "notification_ms_teams_webhook", "notification_slack_webhook"},
    ),
    "core.Branch": Tracked_Model(
        object_type=Audit_Object_Type.BRANCH,
        # The default branch is shown as a change of the product
        ignored_fields={"last_import", "is_default_branch"},
    ),
    "core.Service": Tracked_Model(object_type=Audit_Object_Type.SERVICE),
    "core.Product_Member": Tracked_Model(
        object_type=Audit_Object_Type.PRODUCT_MEMBER,
        get_name=lambda instance: str(instance.user),
    ),
    "core.Product_Authorization_Group_Member": Tracked_Model(
        object_type=Audit_Object_Type.PRODUCT_AUTHORIZATION_GROUP_MEMBER,
        get_name=lambda instance: str(instance.authorization_group),
    ),
    "rules.Rule": Tracked_Model(
        object_type=Audit_Object_Type.PRODUCT_RULE,
        # Approvals are recorded with their own events
        ignored_fields={"user", "approval_status", "rejection_remark", "approval_date", "approval_user"},
    ),
    "import_observations.Api_Configuration": Tracked_Model(
        object_type=Audit_Object_Type.API_CONFIGURATION,
        get_name=lambda instance: instance.name,
        masked_fields={"api_key", "basic_auth_password"},
    ),
    "scancodeio.ScanCodeIO_Project": Tracked_Model(object_type=Audit_Object_Type.SCANCODEIO_PROJECT),
    "notifications.Webhook": Tracked_Model(
        object_type=Audit_Object_Type.WEBHOOK,
        get_name=lambda instance: instance.name,
        ignored_fields={"consecutive_failures", "next_attempt_at", "created", "user"},
        masked_fields={"secret", "url"},
    ),
}

APPROVER_FIELDS = ("assessment_approvers", "assessment_approver_authorization_groups")


def connect_signals() -> None:
    for model in TRACKED_MODELS:
        post_save.connect(audit_post_save, sender=model)
        post_delete.connect(audit_post_delete, sender=model)
    for approver_field in APPROVER_FIELDS:
        m2m_changed.connect(audit_approvers_changed, sender=f"core.Product_{approver_field}")


def audit_post_save(sender: Any, instance: Any, created: bool, raw: bool = False, **kwargs: Any) -> None:
    # Fixtures are loaded raw
    if raw:
        return

    tracked_model = _get_tracked_model(sender)
    product = tracked_model.get_product(instance)
    if not product:
        return

    if created:
        _create_audit_event(tracked_model, product, instance, Audit_Action.CREATED)
        return

    # ScanCode.io projects are only created and deleted
    if not hasattr(instance, "get_dirty_fields"):
        return

    changes = get_changes(instance, tracked_model.ignored_fields, tracked_model.masked_fields)
    if changes:
        _create_audit_event(tracked_model, product, instance, Audit_Action.CHANGED, changes)


def audit_post_delete(sender: Any, instance: Any, origin: Any = None, **kwargs: Any) -> None:
    # The deletion of a product cascades to its objects, only the deletion of the product itself is recorded
    if not isinstance(instance, Product) and _is_product_deletion(origin):
        return

    tracked_model = _get_tracked_model(sender)
    product = tracked_model.get_product(instance)
    if product:
        _create_audit_event(tracked_model, product, instance, Audit_Action.DELETED)


def audit_approvers_changed(  # pylint: disable=too-many-arguments
    sender: Any, instance: Any, *, action: str, reverse: bool, model: Any, pk_set: Optional[set[int]], **kwargs: Any
) -> None:
    if reverse or action not in ("post_add", "post_remove") or not pk_set:
        return

    approver_field = next(name for name in APPROVER_FIELDS if getattr(Product, name).through == sender)
    names = sorted(str(approver) for approver in model.objects.filter(pk__in=pk_set))
    change_type = "added" if action == "post_add" else "removed"
    _create_audit_event(
        TRACKED_MODELS["core.Product"],
        instance,
        instance,
        Audit_Action.CHANGED,
        {approver_field: {change_type: names}},
    )


def _get_tracked_model(sender: Any) -> Tracked_Model:
    return TRACKED_MODELS[sender._meta.label]


def _is_product_deletion(origin: Any) -> bool:
    return isinstance(origin, Product) or (isinstance(origin, QuerySet) and origin.model is Product)


def _create_audit_event(
    tracked_model: Tracked_Model, product: Product, instance: Any, action: str, changes: Optional[dict] = None
) -> None:
    create_audit_event(
        product=product,
        object_type=tracked_model.object_type,
        object_id=instance.pk,
        object_name=tracked_model.get_name(instance),
        action=action,
        changes=changes,
    )
