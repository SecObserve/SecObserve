from typing import Optional

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.authorization.services.roles_permissions import Roles
from application.core.models import Product, Product_Authorization_Group_Member
from application.core.queries.product_member import (
    get_highest_role_of_product_authorization_group_members_for_user,
    get_product_member,
)


def get_effective_assessment_approvers(product: Product) -> tuple[set[int], set[int]]:
    """Return the effective approver user ids and authorization group ids for a product.

    The effective set is the union of the product's own designated approvers and those of
    its product group (mirroring the inheritance of the "assessments need approval" flag).
    """
    approver_user_ids: set[int] = set(product.assessment_approvers.values_list("id", flat=True))
    approver_group_ids: set[int] = set(product.assessment_approver_authorization_groups.values_list("id", flat=True))
    if product.product_group:
        approver_user_ids |= set(product.product_group.assessment_approvers.values_list("id", flat=True))
        approver_group_ids |= set(
            product.product_group.assessment_approver_authorization_groups.values_list("id", flat=True)
        )
    return approver_user_ids, approver_group_ids


def assessment_approvers_configured(product: Product) -> bool:
    """Whether the product (or its product group) has any designated assessment approvers."""
    if product.pk is None:
        return False
    approver_user_ids, approver_group_ids = get_effective_assessment_approvers(product)
    return bool(approver_user_ids or approver_group_ids)


def is_user_designated_assessment_approver(product: Product, user: Optional[User] = None) -> bool:
    """Check whether a user is explicitly a designated assessment approver for a product.

    Unlike ``user_is_allowed_assessment_approver`` (which permits everyone when no approvers
    are configured), this returns False when the effective approver set is empty. When designated
    approvers are configured, the Observation_Log_Approval permission is restricted to these users
    (who must still hold an approval-capable role).
    """
    if user is None:
        user = get_current_user()
    if user is None:
        return False
    if product.pk is None:
        return False

    approver_user_ids, approver_group_ids = get_effective_assessment_approvers(product)

    if not approver_user_ids and not approver_group_ids:
        return False

    if user.pk in approver_user_ids:
        return True

    if approver_group_ids:
        return _user_is_member_of_approval_capable_approver_group(product, user, approver_group_ids)

    return False


def user_is_allowed_assessment_approver(product: Product, user: Optional[User] = None) -> bool:
    """Check whether a user satisfies the designated-approver restriction for a product.

    Returns True when no approvers are configured (legacy behavior) or when the user is a
    designated approver, either directly or via membership in a designated authorization group.
    This is an additional condition layered on top of the Observation_Log_Approval permission
    and the self-approval restriction; it never grants approval rights on its own.
    """
    if user is None:
        user = get_current_user()
    if user is None:
        return False

    approver_user_ids, approver_group_ids = get_effective_assessment_approvers(product)

    if not approver_user_ids and not approver_group_ids:
        return True

    if _user_is_owner(product, user):
        return True

    if _get_highest_user_role(product, user) < Roles.Writer:
        return False

    if user.pk in approver_user_ids:
        return True

    if approver_group_ids:
        return _user_is_member_of_approval_capable_approver_group(product, user, approver_group_ids)

    return False


def _user_is_member_of_approval_capable_approver_group(
    product: Product, user: User, approver_group_ids: set[int]
) -> bool:
    product_ids = [product.pk]
    if product.product_group_id:
        product_ids.append(product.product_group_id)

    return Product_Authorization_Group_Member.objects.filter(
        product_id__in=product_ids,
        authorization_group_id__in=approver_group_ids,
        authorization_group__users=user,
        role__gte=Roles.Writer,
    ).exists()


def _user_is_owner(product: Product, user: User) -> bool:
    return _get_highest_user_role(product, user) == Roles.Owner


def _get_highest_user_role(product: Product, user: User) -> int:
    if user.is_superuser:
        return Roles.Owner

    user_member = get_product_member(product, user)
    highest_role = user_member.role if user_member else 0

    if product.product_group:
        product_group_member = get_product_member(product.product_group, user)
        if product_group_member:
            highest_role = max(highest_role, product_group_member.role)

    highest_role = max(highest_role, get_highest_role_of_product_authorization_group_members_for_user(product, user))
    return highest_role
