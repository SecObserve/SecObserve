import logging

from django.core.paginator import Paginator
from django.db import migrations

from application.core.services.observation import _normalize_origin_component

logger = logging.getLogger("secobserve.migration")


def populate_purl_type(apps, schema_editor):
    Observation = apps.get_model("core", "Observation")
    observations = (
        Observation.objects.exclude(origin_component_purl="").filter(origin_component_purl_type="").order_by("id")
    )

    paginator = Paginator(observations, 1000)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        updates = []

        for observation in page.object_list:
            _normalize_origin_component(observation)
            updates.append(observation)

        Observation.objects.bulk_update(updates, ["origin_component_purl_type"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0044_observation_purl_type"),
    ]

    operations = [
        migrations.RunPython(populate_purl_type),
    ]
