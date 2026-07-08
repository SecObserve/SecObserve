from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import application.core.types


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0091_product_propagate_branches"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Product_Delete_Request",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=application.core.types.Product_Delete_Request_Status.STATUS_CHOICES,
                        default=application.core.types.Product_Delete_Request_Status.STATUS_PENDING,
                        max_length=16,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delete_requests",
                        to="core.product",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="product_delete_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="product_delete_request",
            index=models.Index(fields=["product", "status"], name="core_produc_product_6b09c7_idx"),
        ),
    ]
