from typing import Any

from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.authorization.api.permissions_base import (
    check_object_permission,
    check_post_permission,
)
from application.authorization.services.authorization import get_highest_user_role
from application.authorization.services.roles_permissions import Permissions, Roles
from application.core.models import Product


class UserHasProductPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            if isinstance(request.user, AnonymousUser):
                raise PermissionDenied("You must be authenticated to create a Product")

            return not request.user.is_external

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Product_View,
            put_permission=Permissions.Product_Edit,
            delete_permission=Permissions.Product_Delete,
            post_permission=_get_product_post_permission(view),
        )


class UserHasProductGroupPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "POST":
            if isinstance(request.user, AnonymousUser):
                raise PermissionDenied("You must be authenticated to create a Product Group")

            return not request.user.is_external

        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Product_Group_View,
            put_permission=Permissions.Product_Group_Edit,
            delete_permission=Permissions.Product_Group_Delete,
            post_permission=_get_product_group_post_permission(view),
        )


class UserHasProductMemberPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return check_post_permission(request, Product, "product", Permissions.Product_Member_Create)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method == "DELETE" and obj.role == Roles.Owner and not request.user.is_superuser:
            _check_delete_owner(request, obj)

        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Product_Member_View,
            put_permission=Permissions.Product_Member_Edit,
            delete_permission=Permissions.Product_Member_Delete,
        )


class UserHasProductAuthorizationGroupMemberPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return check_post_permission(
            request,
            Product,
            "product",
            Permissions.Product_Authorization_Group_Member_Create,
        )

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method == "DELETE" and obj.role == Roles.Owner and not request.user.is_superuser:
            _check_delete_owner(request, obj)

        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Product_Authorization_Group_Member_View,
            put_permission=Permissions.Product_Authorization_Group_Member_Edit,
            delete_permission=Permissions.Product_Authorization_Group_Member_Delete,
        )


def _check_delete_owner(request: Request, obj: Any) -> bool:
    if isinstance(request.user, AnonymousUser):
        raise PermissionDenied("You must be authenticated to delete an Owner")

    if get_highest_user_role(obj.product, request.user) == Roles.Owner:
        return True

    raise ValidationError("You are not permitted to delete an Owner")


def _get_product_post_permission(view: APIView) -> Permissions | None:
    match getattr(view, "action", None):
        case "force_delete" | "approve_delete_request" | "reject_delete_request":
            return Permissions.Product_Delete
        case "request_delete" | "undo_delete_request":
            return Permissions.Product_Edit
        case _:
            return None


def _get_product_group_post_permission(view: APIView) -> Permissions | None:
    match getattr(view, "action", None):
        case "force_delete" | "approve_delete_request" | "reject_delete_request":
            return Permissions.Product_Group_Delete
        case "request_delete" | "undo_delete_request":
            return Permissions.Product_Group_Edit
        case _:
            return None


class UserHasBranchPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return check_post_permission(request, Product, "product", Permissions.Branch_Create)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Branch_View,
            put_permission=Permissions.Branch_Edit,
            delete_permission=Permissions.Branch_Delete,
        )


class UserHasServicePermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return check_post_permission(request, Product, "product", Permissions.Service_Create)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Service_View,
            put_permission=Permissions.Serice_Edit,
            delete_permission=Permissions.Service_Delete,
        )


class UserHasObservationPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.path.endswith("/bulk_assessment/"):
            return True

        return check_post_permission(request, Product, "product", Permissions.Observation_Create)

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Observation_View,
            put_permission=Permissions.Observation_Edit,
            delete_permission=Permissions.Observation_Delete,
        )
