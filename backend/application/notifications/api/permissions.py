from typing import Any

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.authorization.api.permissions_base import check_object_permission
from application.authorization.services.roles_permissions import Permissions


class UserHasNotificationPermission(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if obj.product:
            return check_object_permission(
                request=request,
                object_to_check=obj.product,
                get_permission=Permissions.Product_View,
                put_permission=None,
                delete_permission=Permissions.Product_Delete,
            )

        if request.user and request.user.is_superuser:
            return True

        return False


class UserHasProductNotificationPermission(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if not request.user:
            return False

        # Notification settings are personal, everybody can only change their own ones
        if obj.user_id == request.user.pk:
            return True

        # Superusers can read all notification settings, but not change them
        return bool(request.user.is_superuser and request.method in SAFE_METHODS)
