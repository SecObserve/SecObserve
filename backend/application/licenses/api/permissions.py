from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.access_control.queries.authorization_group import (
    get_authorization_groups,
)
from application.authorization.api.permissions_base import (
    check_object_permission,
    check_post_permission,
)
from application.authorization.services.roles_permissions import Permissions
from application.licenses.models import (
    Concluded_License,
    License_Group,
    License_Group_Authorization_Group_Member,
    License_Group_Member,
    License_Policy,
    License_Policy_Authorization_Group_Member,
    License_Policy_Member,
)


class UserHasConcludedLicensePermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return check_post_permission(request, Concluded_License, "product", Permissions.Concluded_License_Create)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Concluded_License_View,
            put_permission=Permissions.Concluded_License_Edit,
            delete_permission=Permissions.Concluded_License_Delete,
        )


class UserHasLicenseGroupPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            user = request.user
            if not user:
                return False

            if isinstance(user, AnonymousUser):
                return False

            return not user.is_external

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: License_Group) -> bool:
        if request.method != "GET":
            return _has_license_group_manage_permission(request, obj)

        return True


class UserHasLicenseGroupMemberPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            license_group = get_object_or_404(License_Group, pk=request.data.get("license_group"))
            return _has_license_group_manage_permission(request, license_group)

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: License_Group_Member) -> bool:
        if request.method != "GET":
            return _has_license_group_manage_permission(request, obj.license_group)

        return True


class UserHasLicenseGroupAuthenticationGroupMemberPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            license_group = get_object_or_404(License_Group, pk=request.data.get("license_group"))

            authorization_group = request.data.get("authorization_group")
            if not authorization_group:
                raise ValueError("No Authorization_Group provided")

            if not isinstance(authorization_group, int):
                raise ValueError("Authorization_Group must be an integer")

            authorization_groups = get_authorization_groups().values_list("id", flat=True)
            if authorization_group not in authorization_groups:
                raise NotFound("Authorization_Group not found.")

            return _has_license_group_manage_permission(request, license_group)

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: License_Group_Member) -> bool:
        if request.method != "GET":
            return _has_license_group_manage_permission(request, obj.license_group)

        return True


class UserHasLicensePolicyPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            user = request.user
            if not user:
                return False

            if isinstance(user, AnonymousUser):
                return False

            return not user.is_external

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: License_Policy) -> bool:
        if request.method != "GET":
            return _has_license_policy_manage_permission(request, obj)

        return True


class UserHasLicensePolicyItemMemberPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            license_policy = get_object_or_404(License_Policy, pk=request.data.get("license_policy"))
            return _has_license_policy_manage_permission(request, license_policy)

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: License_Policy_Member) -> bool:
        if request.method != "GET":
            return _has_license_policy_manage_permission(request, obj.license_policy)

        return True


class UserHasLicensePolicyAuthorizationGroupMemberPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            license_policy = get_object_or_404(License_Policy, pk=request.data.get("license_policy"))

            authorization_group = request.data.get("authorization_group")
            if not authorization_group:
                raise ValueError("No Authorization_Group provided")

            if not isinstance(authorization_group, int):
                raise ValueError("Authorization_Group must be an integer")

            authorization_groups = get_authorization_groups().values_list("id", flat=True)
            if authorization_group not in authorization_groups:
                raise NotFound("Authorization_Group not found.")

            return _has_license_policy_manage_permission(request, license_policy)

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: License_Policy_Member) -> bool:
        if request.method != "GET":
            return _has_license_policy_manage_permission(request, obj.license_policy)

        return True


def _has_license_group_manage_permission(request: Request, license_group: License_Group) -> bool:
    user = request.user

    if not user:
        return False

    if isinstance(user, AnonymousUser):
        return False

    if user.is_superuser:
        return True

    if License_Group_Member.objects.filter(license_group=license_group, user=user, is_manager=True).exists():
        return True

    if License_Group_Authorization_Group_Member.objects.filter(
        license_group=license_group, authorization_group__users=user, is_manager=True
    ).exists():
        return True

    return False


def _has_license_policy_manage_permission(request: Request, license_policy: License_Policy) -> bool:
    user = request.user

    if not user:
        return False

    if isinstance(user, AnonymousUser):
        return False

    if user.is_superuser:
        return True

    if License_Policy_Member.objects.filter(license_policy=license_policy, user=user, is_manager=True).exists():
        return True

    if License_Policy_Authorization_Group_Member.objects.filter(
        license_policy=license_policy, authorization_group__users=user, is_manager=True
    ).exists():
        return True

    return False
