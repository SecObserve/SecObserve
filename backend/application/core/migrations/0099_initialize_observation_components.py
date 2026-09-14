from django.db import migrations
from django.db.models import Q

from application.core.services.components import get_or_create_component

BATCH_SIZE = 1000


def initialize_observation_components(apps, schema_editor):
    Component = apps.get_model("core", "Component")
    Observation = apps.get_model("core", "Observation")

    # Observations having either a component name or a component purl and no component yet.
    # Skipping the ones that are done lets a restarted migration continue where it stopped.
    observations = (
        Observation.objects.exclude(Q(origin_component_name="") & Q(origin_component_purl=""))
        .filter(origin_component__isnull=True)
        .order_by("id")
    )

    component_ids: dict[tuple, int] = {}
    last_id = 0

    while True:
        batch = list(observations.filter(id__gt=last_id)[:BATCH_SIZE])
        if not batch:
            break

        for observation in batch:
            key = (
                observation.origin_component_name,
                observation.origin_component_version,
                observation.origin_component_name_version,
                observation.origin_component_type,
                observation.origin_component_purl,
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

            observation.origin_component_id = component_id

        Observation.objects.bulk_update(batch, ["origin_component"])
        last_id = batch[-1].id


class Migration(migrations.Migration):
    # One transaction per batch instead of one for the whole migration: the row locks are released
    # in between, so that writes of an installation that is still running cannot deadlock with it.
    atomic = False

    dependencies = [
        ("core", "0098_component"),
    ]

    operations = [
        migrations.RunPython(
            initialize_observation_components,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
