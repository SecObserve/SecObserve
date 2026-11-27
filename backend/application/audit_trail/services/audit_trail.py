from typing import Any, Optional

from django.db.models import Field

from application.access_control.services.current_user import get_current_user
from application.audit_trail.models import Product_Audit_Event
from application.core.models import Product

MASKED_VALUE = "***"
MAX_VALUE_LENGTH = 255


def create_audit_event(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    product: Product,
    object_type: str,
    object_id: int,
    object_name: str,
    action: str,
    changes: Optional[dict] = None,
) -> None:
    if changes:
        changes = {field: {key: _cut(value) for key, value in values.items()} for field, values in changes.items()}
    user = get_current_user()
    Product_Audit_Event.objects.create(
        product_id=product.pk,
        product_name=product.name,
        is_product_group=product.is_product_group,
        user=user,
        user_full_name=user.full_name if user else "",
        object_type=object_type,
        object_id=object_id,
        object_name=object_name[:513],
        action=action,
        changes=changes,
    )


def _cut(value: Any) -> Any:
    if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
        return value[:MAX_VALUE_LENGTH] + " ..."
    return value


def get_changes(
    instance: Any, ignored_fields: set[str], masked_fields: set[str], update_fields: Optional[frozenset[str]] = None
) -> dict:
    changes = {}
    for field_name, values in instance.get_dirty_fields(check_relationship=True, verbose=True).items():
        # Dirty fields not in update_fields have not been saved
        if field_name in ignored_fields or (update_fields is not None and field_name not in update_fields):
            continue
        if field_name in masked_fields:
            changes[field_name] = {"old": MASKED_VALUE, "new": MASKED_VALUE}
            continue
        field = instance._meta.get_field(field_name)
        changes[field_name] = {
            "old": _display_value(field, values["saved"]),
            "new": _display_value(field, values["current"]),
        }
    return changes


def get_created_values(instance: Any, ignored_fields: set[str], masked_fields: set[str]) -> dict:
    values = {}
    for field in instance._meta.concrete_fields:
        # The product is the event's product anyway
        if (
            field.primary_key
            or field.name in ignored_fields
            or field.name == "product"
            or getattr(field, "auto_now", False)
            or getattr(field, "auto_now_add", False)
        ):
            continue
        value = getattr(instance, field.attname)
        # Only the values that have been actively set
        if value == field.get_default():
            continue
        values[field.name] = {"new": MASKED_VALUE if field.name in masked_fields else _display_value(field, value)}
    return values


def _display_value(field: Field, value: Any) -> Any:
    if value is None or not field.remote_field:
        return value
    related_object = field.related_model.objects.filter(pk=value).first()  # type: ignore[union-attr]
    return str(related_object) if related_object else value


def create_approval_audit_event(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    product: Product,
    object_type: str,
    object_id: int,
    object_name: str,
    approval_status: str,
    rejection_remark: Optional[str],
    edits: Optional[dict] = None,
) -> None:
    changes = dict(edits or {})
    if rejection_remark:
        changes["rejection_remark"] = {"old": "", "new": rejection_remark}
    create_audit_event(product, object_type, object_id, object_name, approval_status, changes or None)
