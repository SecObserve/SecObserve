from django.core.paginator import Paginator
from django.db import migrations
from django.db.models import Q

from application.core.services.components import get_or_create_component

BATCH_SIZE = 1000


def initialize_observation_components(apps, schema_editor):
    Component = apps.get_model("core", "Component")
    Observation = apps.get_model("core", "Observation")

    # Observations having either a component name or a component purl. The filter only uses columns
    # that are not written by this migration, so that the pagination below stays stable.
    observations = Observation.objects.exclude(Q(origin_component_name="") & Q(origin_component_purl="")).order_by("id")

    component_ids: dict[tuple, int] = {}

    paginator = Paginator(observations, BATCH_SIZE)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        updates = []

        for observation in page.object_list:
            key = (
                observation.origin_component_name,
                observation.origin_component_version,
                observation.origin_component_name_version,
                observation.origin_component_type,
                observation.origin_component_purl,
                observation.origin_component_cpe,
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
                        cpe=key[5],
                    )
                ).pk
                component_ids[key] = component_id

            observation.origin_component_id = component_id
            updates.append(observation)

        Observation.objects.bulk_update(updates, ["origin_component"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0098_component"),
    ]

    operations = [
        migrations.RunPython(
            initialize_observation_components,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
