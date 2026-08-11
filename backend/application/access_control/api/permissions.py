from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
)


class UserHasSuperuserPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if (
            request.method != "GET"
            and request.path != "/api/users/my_settings/"
            and not request.path.endswith("/change_password/")
        ):
            return request.user.is_superuser

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method != "GET" and request.path != f"/api/users/{obj.pk}/change_password/":
            return request.user.is_superuser

        return True


class UserHasAuthorizationGroupPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            if isinstance(request.user, AnonymousUser):
                return False
            return not request.user.is_external

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Authorization_Group) -> bool:
        if request.method != "GET":
            return _has_manage_permission(request, obj)

        return True


class UserHasAuthorizationGroupMemberPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            pk = request.data.get("authorization_group") if isinstance(request.data, dict) else None
            authorization_group = get_object_or_404(Authorization_Group, pk)
            return _has_manage_permission(request, authorization_group)

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Authorization_Group_Member) -> bool:
        if request.method != "GET":
            return _has_manage_permission(request, obj.authorization_group)

        return True


def _has_manage_permission(request: Request, authorization_group: Authorization_Group) -> bool:
    user = request.user

    if isinstance(user, AnonymousUser):
        return False

    if user and user.is_superuser:
        return True

    try:
        authorization_group_member = Authorization_Group_Member.objects.get(
            authorization_group=authorization_group, user=user
        )
        return authorization_group_member.is_manager
    except Authorization_Group_Member.DoesNotExist:
        return False
