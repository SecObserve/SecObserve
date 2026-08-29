from django.core.paginator import Paginator
from django.db import migrations
from django.db.models import Q

from application.core.services.components import get_or_create_component

BATCH_SIZE = 1000


def initialize_license_component_components(apps, schema_editor):
    Component = apps.get_model("core", "Component")
    License_Component = apps.get_model("licenses", "License_Component")

    # License components having either a component name or a component purl. The filter only uses
    # columns that are not written by this migration, so that the pagination below stays stable.
    license_components = License_Component.objects.exclude(Q(component_name="") & Q(component_purl="")).order_by("id")

    component_ids: dict[tuple, int] = {}

    paginator = Paginator(license_components, BATCH_SIZE)
    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        updates = []

        for license_component in page.object_list:
            key = (
                license_component.component_name,
                license_component.component_version,
                license_component.component_name_version,
                license_component.component_type,
                license_component.component_purl,
                license_component.component_cpe,
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

            license_component.component_id = component_id
            updates.append(license_component)

        License_Component.objects.bulk_update(updates, ["component"])


class Migration(migrations.Migration):
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
