from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations

# The fields must be the same as the ones in application.core.queries.observation,
# otherwise not all searched fields are indexed. They are defined here again to freeze the migration.

OBSERVATION_FULL_TEXT_SEARCH_FIELDS = {
    "title": "core_obs_title_trgm_idx",
    "description": "core_obs_description_trgm_idx",
    "recommendation": "core_obs_recommend_trgm_idx",
    "vulnerability_id": "core_obs_vuln_id_trgm_idx",
    "vulnerability_id_aliases": "core_obs_vuln_alias_trgm_idx",
    "origin_component_name_version": "core_obs_component_trgm_idx",
    "origin_docker_image_name_tag": "core_obs_docker_image_trgm_idx",
    "origin_endpoint_url": "core_obs_endpoint_url_trgm_idx",
    "origin_source_file": "core_obs_source_file_trgm_idx",
    "origin_cloud_qualified_resource": "core_obs_cloud_res_trgm_idx",
    "origin_kubernetes_qualified_resource": "core_obs_k8s_res_trgm_idx",
}

OBSERVATION_LOG_FULL_TEXT_SEARCH_FIELDS = {
    "comment": "core_obs_log_comment_trgm_idx",
}


def _get_indexes(apps):
    indexes = []
    for model_name, fields in (
        ("Observation", OBSERVATION_FULL_TEXT_SEARCH_FIELDS),
        ("Observation_Log", OBSERVATION_LOG_FULL_TEXT_SEARCH_FIELDS),
    ):
        table = apps.get_model("core", model_name)._meta.db_table
        for field, index_name in fields.items():
            indexes.append((table, field, index_name))
    return indexes


def create_indexes(apps, schema_editor):
    # Full text search is only available with PostgreSQL
    if schema_editor.connection.vendor != "postgresql":
        return

    # The indexes are built on UPPER(field), because Django filters with UPPER(field) LIKE UPPER(value) for icontains.
    # Raw SQL, because Django can only create an index with an operator class on an expression,
    # if django.contrib.postgres is installed.
    quote_name = schema_editor.quote_name
    for table, field, index_name in _get_indexes(apps):
        schema_editor.execute(
            f"CREATE INDEX {quote_name(index_name)} ON {quote_name(table)} "
            f"USING gin (UPPER({quote_name(field)}) gin_trgm_ops)"
        )


def remove_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    for _, _, index_name in _get_indexes(apps):
        schema_editor.execute(f"DROP INDEX IF EXISTS {schema_editor.quote_name(index_name)}")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0100_observation_log_assessment_status_index"),
    ]

    operations = [
        # Only executed with PostgreSQL
        TrigramExtension(),
        migrations.RunPython(create_indexes, remove_indexes),
    ]
