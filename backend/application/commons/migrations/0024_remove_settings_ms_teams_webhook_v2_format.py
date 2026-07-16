from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("commons", "0023_settings_ms_teams_webhook_v2_format"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="settings",
            name="exception_ms_teams_webhook_v2_format",
        ),
        migrations.RemoveField(
            model_name="settings",
            name="observation_title_notification_ms_teams_webhook_v2_format",
        ),
    ]
