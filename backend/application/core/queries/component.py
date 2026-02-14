from typing import Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet
from django.db import connection

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Component,
    Product_Authorization_Group_Member,
    Product_Member,
)


def get_component_by_id(component_id: str) -> Optional[Component]:
    _create_component_view()

    try:
        return Component.objects.get(id=component_id)
    except Component.DoesNotExist:
        return None


def get_components() -> QuerySet[Component]:
    _create_component_view()

    user = get_current_user()

    if user is None:
        return Component.objects.none()

    components = Component.objects.all()

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("product_id"), user=user)
        product_group_members = Product_Member.objects.filter(product=OuterRef("product__product_group"), user=user)

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product_id"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product__product_group"),
            authorization_group__users=user,
        )

        components = components.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        components = components.filter(
            Q(product__member=True)
            | Q(product__product_group__member=True)
            | Q(authorization_group_member=True)
            | Q(product_group_authorization_group_member=True)
        )

    return components

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


def _create_component_view() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='core_component'")
        row = cursor.fetchone()
        if not row:
            cursor.execute(DROP_COMPONENT_VIEW)
            cursor.execute(CREATE_COMPONENT_VIEW)
