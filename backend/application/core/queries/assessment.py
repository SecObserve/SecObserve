from typing import Optional

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.core.models import Product


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


def is_user_designated_assessment_approver(product: Product, user: Optional[User] = None) -> bool:
    """Check whether a user is explicitly a designated assessment approver for a product.

    Unlike ``user_is_allowed_assessment_approver`` (which permits everyone when no approvers
    are configured), this returns False when the effective approver set is empty. It is used to
    additionally grant the Observation_Assessment permission to designated approvers whose role
    would not otherwise include it (e.g. the Writer role).
    """
    if user is None:
        user = get_current_user()
    if user is None:
        return False

    approver_user_ids, approver_group_ids = get_effective_assessment_approvers(product)

    if not approver_user_ids and not approver_group_ids:
        return False

    if user.pk in approver_user_ids:
        return True

    if approver_group_ids:
        return user.authorization_groups.filter(id__in=approver_group_ids).exists()

    return False
