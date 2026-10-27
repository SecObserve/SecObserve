from typing import Any, Optional

from django.db.models import QuerySet

from application.access_control.models import Authorization_Group, User
from application.access_control.services.current_user import get_current_user
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Audit_Log,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
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
        user=None if _is_deleted(user, deleted) else user,
        user_name=user.full_name if user else "",
        product=product,
        product_name=product.name if product else "",
        authorization_group=None if _is_deleted(authorization_group, deleted) else authorization_group,
        authorization_group_name=authorization_group.name if authorization_group else "",
        action=action,
        target=target,
        old_value=old_value,
        new_value=new_value,
    )


def _is_deleted(row: Any, deleted: Any) -> bool:
    if isinstance(deleted, QuerySet):
        # A bulk deletion can remove any row of its model
        return isinstance(row, deleted.model)
    return row is not None and row == deleted


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


def is_deleted_with_product(origin: Any) -> bool:
    # The members of a deleted product or product group go with it, there is no product left to refer to
    return isinstance(origin, Product) or (isinstance(origin, QuerySet) and origin.model is Product)


def log_product_member(
    member: Product_Member | Product_Authorization_Group_Member, created: bool, old_role: Optional[int]
) -> None:
    if created:
        _write_product_member_log(
            member,
            (Audit_Log_Action.AUDIT_LOG_ACTION_USER_MEMBER_ADDED, Audit_Log_Action.AUDIT_LOG_ACTION_GROUP_MEMBER_ADDED),
            new_value=Roles(member.role).name,
        )
    elif old_role and old_role != member.role:
        _write_product_member_log(
            member,
            (
                Audit_Log_Action.AUDIT_LOG_ACTION_USER_MEMBER_ROLE_CHANGED,
                Audit_Log_Action.AUDIT_LOG_ACTION_GROUP_MEMBER_ROLE_CHANGED,
            ),
            old_value=Roles(old_role).name,
            new_value=Roles(member.role).name,
        )


def log_product_member_removed(member: Product_Member | Product_Authorization_Group_Member, origin: Any) -> None:
    if not is_deleted_with_product(origin):
        _write_product_member_log(
            member,
            (
                Audit_Log_Action.AUDIT_LOG_ACTION_USER_MEMBER_REMOVED,
                Audit_Log_Action.AUDIT_LOG_ACTION_GROUP_MEMBER_REMOVED,
            ),
            old_value=Roles(member.role).name,
            deleted=origin,
        )


def _write_product_member_log(
    member: Product_Member | Product_Authorization_Group_Member, actions: tuple[str, str], **kwargs: Any
) -> None:
    if isinstance(member, Product_Member):
        write_audit_log(actions[0], member.user.full_name, product=member.product, **kwargs)
    else:
        write_audit_log(
            actions[1],
            member.authorization_group.name,
            product=member.product,
            authorization_group=member.authorization_group,
            **kwargs,
        )


def log_authorization_group_user(
    authorization_group: Authorization_Group, user: User, removed: bool, deleted: Any = None
) -> None:
    write_audit_log(
        (
            Audit_Log_Action.AUDIT_LOG_ACTION_GROUP_USER_REMOVED
            if removed
            else Audit_Log_Action.AUDIT_LOG_ACTION_GROUP_USER_ADDED
        ),
        user.full_name,
        authorization_group=authorization_group,
        deleted=deleted,
    )


def log_authorization_group_users_added(instance: Any, reverse: bool, model: Any, pk_set: set) -> None:
    # The relation can be changed from both sides, e.g. user.authorization_groups.add() by the OIDC synchronization
    for related in model.objects.filter(pk__in=pk_set):
        authorization_group, user = (related, instance) if reverse else (instance, related)
        log_authorization_group_user(authorization_group, user, removed=False)


def log_superuser(user: User, created: bool, old_value: Optional[bool]) -> None:
    if created and user.is_superuser:
        write_audit_log(Audit_Log_Action.AUDIT_LOG_ACTION_SUPERUSER, user.full_name, new_value=str(True))
    elif not created and old_value is not None and old_value != user.is_superuser:
        write_audit_log(
            Audit_Log_Action.AUDIT_LOG_ACTION_SUPERUSER,
            user.full_name,
            old_value=str(old_value),
            new_value=str(user.is_superuser),
        )
