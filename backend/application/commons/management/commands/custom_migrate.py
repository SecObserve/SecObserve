# project/myapp/management/commands/custom_migrate.py
from django.core.management.commands.migrate import Command as MigrateCommand
from django.db import connection

# The component view has to be created after all other migrations. Otherwise some alterations of
# observation lead to errors, due to https://www.sqlite.org/lang_altertable.html#caution.
# Thanks to https://stackoverflow.com/a/40239171 for providing the idea how to solve this.


class Command(MigrateCommand):

    DROP_COMPONENT_VIEW = "DROP VIEW IF EXISTS core_component;"

    CREATE_COMPONENT_VIEW = """
CREATE VIEW core_component AS
WITH CombinedData AS (
    SELECT
        product_id as product_id,
        branch_id as branch_id,
        origin_service_id as origin_service_id,
        origin_component_name AS component_name,
        origin_component_version AS component_version,
        origin_component_name_version AS component_name_version,
        origin_component_purl AS component_purl,
        origin_component_purl_type AS component_purl_type,
        origin_component_cpe AS component_cpe,
        origin_component_dependencies AS component_dependencies,
        origin_component_cyclonedx_bom_link AS component_cyclonedx_bom_link
    FROM core_observation
    WHERE origin_component_name_version != ''

    UNION
    
    SELECT 
        product_id as product_id,
        branch_id as branch_id,
        origin_service_id as origin_service_id,
        component_name AS component_name,
        component_version AS component_version,
        component_name_version AS component_name_version,
        component_purl AS component_purl,
        component_purl_type AS component_purl_type,
        component_cpe AS component_cpe,
        component_dependencies AS component_dependencies,
        component_cyclonedx_bom_link AS component_cyclonedx_bom_link
    FROM licenses_license_component
),
ObservationFlag AS (
    SELECT DISTINCT
        product_id,
        branch_id,
        origin_service_id,
        origin_component_name_version AS component_name_version,
        origin_component_purl AS component_purl,
        origin_component_cpe AS component_cpe,
        origin_component_dependencies AS component_dependencies,
        origin_component_cyclonedx_bom_link AS component_cyclonedx_bom_link,
        TRUE AS has_observation
    FROM core_observation
    WHERE current_status = 'Open'
)
SELECT
    MD5(
		CONCAT(
			CAST(COALESCE(cd.product_id, 111) as CHAR(255)),
			CAST(COALESCE(cd.branch_id, 222) as CHAR(255)),
			CAST(COALESCE(cd.origin_service_id, 333) as CHAR(255)),
			COALESCE(cd.component_name_version, 'no_name_version'),
			COALESCE(cd.component_purl, 'no_purl'),
			COALESCE(cd.component_cpe, 'no_cpe'),
			COALESCE(cd.component_dependencies, 'no_dependencies'),
			COALESCE(cd.component_cyclonedx_bom_link, 'component_cyclonedx_bom_link')
			)		
		) AS id,
    cd.product_id as product_id,
    cd.branch_id as branch_id,
    cd.origin_service_id as origin_service_id,
    cd.component_name AS component_name,
    cd.component_version AS component_version,
    cd.component_name_version AS component_name_version,
    cd.component_purl AS component_purl,
    cd.component_purl_type AS component_purl_type,
    cd.component_cpe AS component_cpe,
    cd.component_dependencies AS component_dependencies,
    cd.component_cyclonedx_bom_link AS component_cyclonedx_bom_link,
    COALESCE(ObservationFlag.has_observation, FALSE) AS has_observations
FROM CombinedData cd
LEFT JOIN ObservationFlag ON 
    cd.product_id = ObservationFlag.product_id
	AND (
        (cd.branch_id = ObservationFlag.branch_id) IS TRUE OR 
        (cd.branch_id IS NULL AND ObservationFlag.branch_id IS NULL)
        )
	AND (
        (cd.origin_service_id = ObservationFlag.origin_service_id) IS TRUE OR 
        (cd.origin_service_id IS NULL AND ObservationFlag.origin_service_id IS NULL)
        )
    AND cd.component_name_version = ObservationFlag.component_name_version 
    AND cd.component_purl = ObservationFlag.component_purl 
    AND cd.component_cpe = ObservationFlag.component_cpe 
    AND cd.component_dependencies = ObservationFlag.component_dependencies 
    AND cd.component_cyclonedx_bom_link = ObservationFlag.component_cyclonedx_bom_link 
;
"""

    def handle(self, *args, **options) -> None:
        super().handle(*args, **options)

        with connection.cursor() as cursor:
            cursor.execute(self.DROP_COMPONENT_VIEW)
            cursor.execute(self.CREATE_COMPONENT_VIEW)
