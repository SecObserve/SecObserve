from django.db.models.query import QuerySet

from application.access_control.models import Authorization_Group
from application.access_control.services.current_user import get_current_user


def get_authorization_groups() -> QuerySet[Authorization_Group]:
    user = get_current_user()

    if user is None:
        return Authorization_Group.objects.none()

    authorization_groups = Authorization_Group.objects.all().order_by("id")

    if user.is_superuser:
        return authorization_groups

    return authorization_groups.filter(users=user)
