from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commons", "0024_settings_feature_show_product_header_chips"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="oidc_strict_audience",
            field=models.BooleanField(
                default=True,
                help_text="Require the audience claim of OIDC tokens to be a single string matching the client id",
            ),
        ),
    ]
