from application.core.models import Product


def get_effective_assessment_approvers(product: Product) -> tuple[set[int], set[int]]:
    """Return designated approver user and authorization-group ids, including inherited configuration."""
    approver_user_ids: set[int] = set(product.assessment_approvers.values_list("id", flat=True))
    approver_group_ids: set[int] = set(product.assessment_approver_authorization_groups.values_list("id", flat=True))
    if product.product_group:
        approver_user_ids |= set(product.product_group.assessment_approvers.values_list("id", flat=True))
        approver_group_ids |= set(
            product.product_group.assessment_approver_authorization_groups.values_list("id", flat=True)
        )
    return approver_user_ids, approver_group_ids


def assessment_approvers_configured(product: Product) -> bool:
    """Whether a saved product or its product group has designated assessment approvers."""
    if product.pk is None:
        return False
    approver_user_ids, approver_group_ids = get_effective_assessment_approvers(product)
    return bool(approver_user_ids or approver_group_ids)
