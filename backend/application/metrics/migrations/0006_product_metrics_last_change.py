from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metrics", "0005_product_license_metrics"),
    ]

    operations = [
        migrations.AddField(
            model_name="product_license_metrics",
            name="last_license_change",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name="product_metrics",
            name="last_observation_change",
            field=models.DateTimeField(null=True),
        ),
    ]
