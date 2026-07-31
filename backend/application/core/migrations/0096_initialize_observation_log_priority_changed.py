from django.db import migrations


def initialize_priority_changed(apps, schema_editor):
    Observation_Log = apps.get_model("core", "Observation_Log")

    # Observation logs created before the priority_changed flag existed only can have a priority
    # if that priority has been changed by the assessment or rule the log belongs to.
    Observation_Log.objects.filter(priority__isnull=False).update(priority_changed=True)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0095_observation_log_priority_changed"),
    ]

    operations = [
        migrations.RunPython(
            initialize_priority_changed,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
