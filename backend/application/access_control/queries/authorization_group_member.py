from typing import Optional

from django.db.models.query import QuerySet

from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
    User,
)
from application.access_control.queries.authorization_group import (
    get_authorization_groups,
)
from application.access_control.services.current_user import get_current_user


def get_authorization_group_member(
    authorization_group: Authorization_Group, user: User
) -> Optional[Authorization_Group_Member]:
    try:
        return Authorization_Group_Member.objects.get(authorization_group=authorization_group, user=user)
    except Authorization_Group_Member.DoesNotExist:
        return None


def get_authorization_group_members() -> QuerySet[Authorization_Group_Member]:
    user = get_current_user()

    if user is None:
        return Authorization_Group_Member.objects.none()

    authorization_group_members = Authorization_Group_Member.objects.all().order_by("id")

    if user.is_superuser:
        return authorization_group_members

    authorization_groups = get_authorization_groups()
    return authorization_group_members.filter(authorization_group__in=authorization_groups)
