from django.core.paginator import Paginator
from django.db import migrations


def initialize_default_branch(apps, schema_editor):
    Branch = apps.get_model("core", "Branch")

    Product = apps.get_model("core", "Product")
    products = (
        Product.objects.exclude(repository_default_branch__isnull=True)
        .order_by("id")
        .select_related("repository_default_branch")
    )

    paginator = Paginator(products, 1000)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        updates = []

        for product in page.object_list:
            branch = product.repository_default_branch
            branch.is_default_branch = True
            updates.append(branch)

        Branch.objects.bulk_update(updates, ["is_default_branch"])


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0072_branch_is_default_branch",
        ),
    ]

    operations = [
        migrations.RunPython(
            initialize_default_branch,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
