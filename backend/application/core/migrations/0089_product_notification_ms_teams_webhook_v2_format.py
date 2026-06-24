from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0088_resave_encrypt_issue_tracker_api_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="notification_ms_teams_webhook_v2_format",
            field=models.BooleanField(default=False),
        ),
    ]
