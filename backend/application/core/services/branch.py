from typing import Optional

from django.utils import timezone

from application.core.models import Branch, Product


def set_default_branch(branch: Branch, created: bool) -> None:

    if created or (branch.get_dirty_fields().get("is_default_branch") is not None):
        if branch.is_default_branch:
            for other_branch in Branch.objects.filter(product=branch.product, is_default_branch=True).exclude(
                pk=branch.pk
            ):
                other_branch.is_default_branch = False
                other_branch.save()

            _set_repository_default_branch(branch.product, branch)
        else:
            if branch.product.repository_default_branch == branch:
                _set_repository_default_branch(branch.product, None)


def _set_repository_default_branch(product: Product, branch: Optional[Branch]) -> None:
    if product.repository_default_branch_id != (branch.pk if branch else None):
        # The metrics count the observations and licenses of the default branch
        product.last_observation_change = timezone.now()
        product.last_license_change = product.last_observation_change
    product.repository_default_branch = branch
    product.save()
