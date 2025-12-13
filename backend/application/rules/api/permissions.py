from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.authorization.api.permissions_base import (
    check_object_permission,
    check_post_permission,
)
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Product
from application.rules.models import Rule


class UserHasGeneralRulePermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method == "GET":
            return True

        if not request.user:
            return False

        if isinstance(request.user, AnonymousUser):
            return False

        return request.user.is_superuser


class UserHasProductRulePermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if "/simulate" in request.path:
            # Permission will be checked in the view
            return True

        return check_post_permission(request, Product, "product", Permissions.Product_Rule_Create)

    def has_object_permission(self, request: Request, view: APIView, obj: Rule) -> bool:
        return check_object_permission(
            request=request,
            object_to_check=obj,
            get_permission=Permissions.Product_Rule_View,
            put_permission=Permissions.Product_Rule_Edit,
            delete_permission=Permissions.Product_Rule_Delete,
        )
