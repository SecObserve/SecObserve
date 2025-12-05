from typing import Optional

from django.db.models.query import QuerySet

from application.access_control.models import Authorization_Group
from application.access_control.queries.authorization_group import (
    get_authorization_groups,
)
from application.access_control.services.current_user import get_current_user
from application.licenses.models import (
    License_Group,
    License_Group_Authorization_Group_Member,
)
from application.licenses.queries.license_group import get_license_groups


def get_license_group_authorization_group_member(
    license_group: License_Group, authorization_group: Authorization_Group
) -> Optional[License_Group_Authorization_Group_Member]:
    try:
        return License_Group_Authorization_Group_Member.objects.get(
            license_group=license_group, authorization_group=authorization_group
        )
    except License_Group_Authorization_Group_Member.DoesNotExist:
        return None


def get_license_group_authorization_group_members() -> QuerySet[License_Group_Authorization_Group_Member]:
    user = get_current_user()

    if user is None:
        return License_Group_Authorization_Group_Member.objects.none()

    license_group_authorization_group_members = License_Group_Authorization_Group_Member.objects.all().order_by("id")

    if user.is_superuser:
        return license_group_authorization_group_members

    authorization_groups = get_authorization_groups()
    license_groups = get_license_groups()
    return license_group_authorization_group_members.filter(
        authorization_group__in=authorization_groups, license_group__in=license_groups
    )
