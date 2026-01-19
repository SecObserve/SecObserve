import logging

from django.core.paginator import Paginator
from django.db import migrations

from application.core.services.observation import (
    _normalize_update_impact_score_and_fix_available,
)

logger = logging.getLogger("secobserve.migration")


def initialize_fix_and_upgrade(apps, schema_editor):
    Observation = apps.get_model("core", "Observation")
    observations = Observation.objects.exclude(origin_component_name__exact="").order_by("id")

    paginator = Paginator(observations, 1000)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        updates = []

        for observation in page.object_list:
            _normalize_update_impact_score_and_fix_available(observation)
            updates.append(observation)

        Observation.objects.bulk_update(updates, ["update_impact_score", "fix_available"])


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0074_observation_fix_available_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            initialize_fix_and_upgrade,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
