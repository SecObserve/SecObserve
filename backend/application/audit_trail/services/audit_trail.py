from typing import Any, Optional

from django.db.models import Field

from application.access_control.services.current_user import get_current_user
from application.audit_trail.models import Product_Audit_Event
from application.core.models import Product

MASKED_VALUE = "***"


def create_audit_event(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    product: Product,
    object_type: str,
    object_id: int,
    object_name: str,
    action: str,
    changes: Optional[dict] = None,
) -> None:
    user = get_current_user()
    Product_Audit_Event.objects.create(
        product_id=product.pk,
        product_name=product.name,
        user=user,
        user_full_name=user.full_name if user else "",
        object_type=object_type,
        object_id=object_id,
        object_name=object_name[:513],
        action=action,
        changes=changes,
    )


def get_changes(instance: Any, ignored_fields: set[str], masked_fields: set[str]) -> dict:
    changes = {}
    for field_name, values in instance.get_dirty_fields(check_relationship=True, verbose=True).items():
        if field_name in ignored_fields:
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
) -> None:
    changes = {"rejection_remark": {"old": "", "new": rejection_remark}} if rejection_remark else None
    create_audit_event(product, object_type, object_id, object_name, approval_status, changes)
