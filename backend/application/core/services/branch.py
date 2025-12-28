from application.core.models import Branch


def set_default_branch(branch: Branch) -> None:
    if branch.is_default_branch:
        for other_branch in Branch.objects.filter(product=branch.product, is_default_branch=True).exclude(pk=branch.pk):
            other_branch.is_default_branch = False
            other_branch.save()

        branch.product.repository_default_branch = branch
        branch.product.save()
    else:
        if branch.product.repository_default_branch == branch:
            branch.product.repository_default_branch = None
            branch.product.save()
