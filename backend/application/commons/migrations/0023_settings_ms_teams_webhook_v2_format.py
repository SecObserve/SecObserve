from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commons", "0022_settings_feature_cross_scanner_deduplication"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="exception_ms_teams_webhook_v2_format",
            field=models.BooleanField(
                default=False,
                help_text="Use new MS Teams webhook format (Power Automate Workflow)",
            ),
        ),
        migrations.AddField(
            model_name="settings",
            name="observation_title_notification_ms_teams_webhook_v2_format",
            field=models.BooleanField(default=False),
        ),
    ]
