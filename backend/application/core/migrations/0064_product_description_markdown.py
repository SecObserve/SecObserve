import logging

from django.core.paginator import Paginator
from django.db import migrations
from html_to_markdown import convert

logger = logging.getLogger("secobserve.migration")


def convert_product_description_to_markdown(apps, schema_editor):
    Product = apps.get_model("core", "Product")
    products = Product.objects.exclude(description__exact="").order_by("id")

    paginator = Paginator(products, 1000)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        updates = []

        for product in page.object_list:
            product.description = convert(product.description).get("content")
            updates.append(product)

        Product.objects.bulk_update(updates, ["description"])


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0063_observation_origin_source_file_link",
        ),
    ]

    operations = [
        migrations.RunPython(
            convert_product_description_to_markdown,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
