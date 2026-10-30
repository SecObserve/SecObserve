from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.authorization.api.permissions_base import check_object_permission
from application.authorization.services.roles_permissions import Permissions


class UserHasScanCodeIOProjectPermission(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Product_View,
            put_permission=None,
            delete_permission=Permissions.Product_Edit,
        )
