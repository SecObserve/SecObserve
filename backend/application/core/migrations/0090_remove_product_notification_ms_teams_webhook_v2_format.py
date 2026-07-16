from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0089_product_notification_ms_teams_webhook_v2_format"),
        ("core", "0089_rename_approval_remark_observation_log_rejection_remark_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="notification_ms_teams_webhook_v2_format",
        ),
    ]
