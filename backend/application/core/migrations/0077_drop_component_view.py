from django.db import migrations

# The component view has to be created after all other migrations. Otherwise some alterations of
# observation lead to errors, due to https://www.sqlite.org/lang_altertable.html#caution.
# It will be created before the first query runs.

DROP_SQL = "DROP VIEW IF EXISTS core_component;"


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0076_alter_product_notification_ms_teams_webhook_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=DROP_SQL,
            reverse_sql=DROP_SQL,
        ),
    ]
