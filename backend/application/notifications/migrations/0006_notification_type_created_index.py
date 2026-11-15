from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0005_product_notification_product_rule_approval_receipt"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["type", "created"], name="commons_not_type_1d9959_idx"),
        ),
    ]
