from django.db import migrations
from django.db.models import Q

from application.core.services.components import get_or_create_component

BATCH_SIZE = 1000


def initialize_license_component_components(apps, schema_editor):
    Component = apps.get_model("core", "Component")
    License_Component = apps.get_model("licenses", "License_Component")

    # License components having either a component name or a component purl and no component yet.
    # Skipping the ones that are done lets a restarted migration continue where it stopped.
    license_components = (
        License_Component.objects.exclude(Q(component_name="") & Q(component_purl=""))
        .filter(component__isnull=True)
        .order_by("id")
    )

    component_ids: dict[tuple, int] = {}
    last_id = 0

    while True:
        batch = list(license_components.filter(id__gt=last_id)[:BATCH_SIZE])
        if not batch:
            break

        for license_component in batch:
            key = (
                license_component.component_name,
                license_component.component_version,
                license_component.component_name_version,
                license_component.component_type,
                license_component.component_purl,
            )

            component_id = component_ids.get(key)
            if component_id is None:
                component_id = get_or_create_component(
                    Component(
                        name=key[0],
                        version=key[1],
                        name_version=key[2],
                        type=key[3],
                        purl=key[4],
                    )
                ).pk
                component_ids[key] = component_id

            license_component.component_id = component_id

        License_Component.objects.bulk_update(batch, ["component"])
        last_id = batch[-1].id


class Migration(migrations.Migration):
    # One transaction per batch instead of one for the whole migration: the row locks are released
    # in between, so that writes of an installation that is still running cannot deadlock with it.
    atomic = False

    dependencies = [
        ("core", "0099_initialize_observation_components"),
        ("licenses", "0023_license_component_component"),
    ]

    operations = [
        migrations.RunPython(
            initialize_license_component_components,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
