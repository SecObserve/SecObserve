from itertools import batched
from typing import Any, Iterable, Optional

from django.db import migrations

BATCH_SIZE = 1000


def backfill_approvals(apps: Any, schema_editor: Any) -> None:  # pylint: disable=unused-argument
    # Approval decisions are the only history that is kept with time and user, for rules only the latest decision
    Product_Audit_Event = apps.get_model("audit_trail", "Product_Audit_Event")
    Observation_Log = apps.get_model("core", "Observation_Log")
    Rule = apps.get_model("rules", "Rule")

    observation_logs = (
        Observation_Log.objects.filter(
            approval_date__isnull=False, assessment_status__in=["Approved", "Approved with edits", "Rejected"]
        )
        .select_related("observation__product", "approval_user")
        .order_by("approval_date", "id")
    )
    _bulk_create(
        Product_Audit_Event,
        (
            _event(
                Product_Audit_Event,
                product=log.observation.product,
                user=log.approval_user,
                created=log.approval_date,
                object_type="Assessment",
                object_id=log.observation.pk,
                object_name=log.observation.title,
                action=log.assessment_status,
                rejection_remark=log.rejection_remark,
            )
            for log in observation_logs.iterator(chunk_size=BATCH_SIZE)
        ),
    )

    rules = (
        Rule.objects.filter(
            product__isnull=False, approval_date__isnull=False, approval_status__in=["Approved", "Rejected"]
        )
        .select_related("product", "approval_user")
        .order_by("approval_date", "id")
    )
    _bulk_create(
        Product_Audit_Event,
        (
            _event(
                Product_Audit_Event,
                product=rule.product,
                user=rule.approval_user,
                created=rule.approval_date,
                object_type="Product rule",
                object_id=rule.pk,
                object_name=rule.name,
                action=rule.approval_status,
                rejection_remark=rule.rejection_remark,
            )
            for rule in rules.iterator(chunk_size=BATCH_SIZE)
        ),
    )


def _event(  # pylint: disable=too-many-arguments
    Product_Audit_Event: Any,
    *,
    product: Any,
    user: Any,
    created: Any,
    object_type: str,
    object_id: int,
    object_name: str,
    action: str,
    rejection_remark: Optional[str],
) -> Any:
    # Same values as create_audit_event() and create_approval_audit_event() at runtime
    return Product_Audit_Event(
        product_id=product.pk,
        product_name=product.name,
        is_product_group=product.is_product_group,
        created=created,
        user=user,
        user_full_name=user.full_name if user else "",
        object_type=object_type,
        object_id=object_id,
        object_name=object_name[:513],
        action=action,
        changes={"rejection_remark": {"old": "", "new": rejection_remark}} if rejection_remark else None,
    )


def _bulk_create(Product_Audit_Event: Any, events: Iterable[Any]) -> None:
    for batch in batched(events, BATCH_SIZE):
        Product_Audit_Event.objects.bulk_create(batch)


class Migration(migrations.Migration):
    dependencies = [
        ("audit_trail", "0001_initial"),
        ("core", "0106_alter_observation_log_rejection_remark"),
        ("rules", "0022_alter_rule_rejection_remark"),
    ]

    operations = [
        migrations.RunPython(backfill_approvals, migrations.RunPython.noop),
    ]
