from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.core.queries.product import get_product_by_id
from application.scancodeio.services.scancodeio import create_scancodeio_project


class CreateScanCodeIOProjectView(APIView):
    @extend_schema(
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    def post(self, request: Request, product_id: int) -> Response:
        product = get_product_by_id(product_id)
        if not product:
            return Response(status=HTTP_404_NOT_FOUND)

        user_has_permission_or_403(product, Permissions.Product_Edit)

        if not Settings.load().feature_scancodeio_integration:
            raise ValidationError("ScanCode.io integration is not enabled")

        create_scancodeio_project(product)

        return Response(status=HTTP_204_NO_CONTENT)
