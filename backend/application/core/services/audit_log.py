from typing import Any, Optional

from application.access_control.models import Authorization_Group, User
from application.access_control.services.current_user import get_current_user
from application.core.models import Audit_Log, Product
from application.core.types import Audit_Log_Action


def write_audit_log(  # pylint: disable=too-many-arguments
    action: str,
    target: str,
    *,
    product: Optional[Product] = None,
    authorization_group: Optional[Authorization_Group] = None,
    old_value: str = "",
    new_value: str = "",
    deleted: Any = None,
) -> None:
    user = get_current_user()
    Audit_Log.objects.create(
        # A row that is being deleted can't be referenced, its name is kept
        user=None if user == deleted else user,
        user_name=user.full_name if user else "",
        product=product,
        product_name=product.name if product else "",
        authorization_group=None if authorization_group == deleted else authorization_group,
        authorization_group_name=authorization_group.name if authorization_group else "",
        action=action,
        target=target,
        old_value=old_value,
        new_value=new_value,
    )


def log_assessments_need_approval(product: Product, old_value: bool) -> None:
    if product.assessments_need_approval != old_value:
        write_audit_log(
            Audit_Log_Action.AUDIT_LOG_ACTION_ASSESSMENTS_NEED_APPROVAL,
            product.name,
            product=product,
            old_value=str(old_value),
            new_value=str(product.assessments_need_approval),
        )


def log_assessment_approver(
    product: Product, approver: User | Authorization_Group, removed: bool, deleted: Any = None
) -> None:
    if isinstance(approver, Authorization_Group):
        write_audit_log(
            (
                Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_GROUP_REMOVED
                if removed
                else Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_GROUP_ADDED
            ),
            approver.name,
            product=product,
            authorization_group=approver,
            deleted=deleted,
        )
    else:
        write_audit_log(
            (
                Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_REMOVED
                if removed
                else Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_ADDED
            ),
            approver.full_name,
            product=product,
            deleted=deleted,
        )


def log_assessment_approvers_changed(instance: Any, removed: bool, reverse: bool, model: Any, pk_set: set) -> None:
    # The relation can be changed from both sides, e.g. user.assessment_approver_for_products
    for related in model.objects.filter(pk__in=pk_set):
        product, approver = (related, instance) if reverse else (instance, related)
        log_assessment_approver(product, approver, removed)
