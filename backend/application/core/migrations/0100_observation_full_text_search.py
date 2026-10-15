from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db import migrations

# The search vectors must be the same as the ones in application.core.queries.observation,
# otherwise the indexes are not used. They are defined here again to freeze the migration.


def get_observation_search_vector():
    return SearchVector(
        "title",
        "description",
        "recommendation",
        "vulnerability_id",
        "vulnerability_id_aliases",
        config="simple",
    )


def get_observation_log_search_vector():
    return SearchVector("comment", config="simple")


def _get_indexes(apps):
    return [
        (
            apps.get_model("core", "Observation"),
            GinIndex(get_observation_search_vector(), name="core_observation_fts_idx"),
        ),
        (
            apps.get_model("core", "Observation_Log"),
            GinIndex(get_observation_log_search_vector(), name="core_observation_log_fts_idx"),
        ),
    ]


def create_indexes(apps, schema_editor):
    # Full text search is only available with PostgreSQL
    if schema_editor.connection.vendor != "postgresql":
        return

    for model, index in _get_indexes(apps):
        schema_editor.add_index(model, index)


def remove_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    for model, index in _get_indexes(apps):
        schema_editor.remove_index(model, index)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0099_initialize_observation_components"),
    ]

    operations = [
        migrations.RunPython(create_indexes, remove_indexes),
    ]
