from dataclasses import dataclass
from typing import Optional, Tuple

from django.contrib.auth.models import AnonymousUser
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import (
    user_has_permission,
    user_has_permission_or_403,
)
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Branch, Product
from application.core.queries.branch import get_branch_by_id
from application.core.queries.component import get_component_by_id
from application.core.queries.product import get_product_by_id
from application.licenses.api.filters import (
    ConcludedLicenseFilter,
    LicenseComponentEvidenceFilter,
    LicenseComponentFilter,
    LicenseFilter,
    LicenseGroupAuthorizationGroupFilter,
    LicenseGroupFilter,
    LicenseGroupMemberFilter,
    LicensePolicyAuthorizationGroupFilter,
    LicensePolicyFilter,
    LicensePolicyItemFilter,
    LicensePolicyMemberFilter,
)
from application.licenses.api.permissions import (
    UserHasConcludedLicensePermission,
    UserHasLicenseGroupAuthenticationGroupMemberPermission,
    UserHasLicenseGroupMemberPermission,
    UserHasLicenseGroupPermission,
    UserHasLicensePolicyAuthorizationGroupMemberPermission,
    UserHasLicensePolicyItemMemberPermission,
    UserHasLicensePolicyPermission,
)
from application.licenses.api.serializers import (
    ConcludedLicenseCreateUpdateSerializer,
    ConcludedLicenseListSerializer,
    ConcludedLicenseSerializer,
    LicenseComponentEvidenceSerializer,
    LicenseComponentIdSerializer,
    LicenseComponentListSerializer,
    LicenseComponentOverviewSerializer,
    LicenseComponentSerializer,
    LicenseGroupAuthorizationGroupMemberSerializer,
    LicenseGroupCopySerializer,
    LicenseGroupLicenseAddRemoveSerializer,
    LicenseGroupMemberSerializer,
    LicenseGroupSerializer,
    LicensePolicyAuthorizationGroupMemberSerializer,
    LicensePolicyCopySerializer,
    LicensePolicyItemSerializer,
    LicensePolicyMemberSerializer,
    LicensePolicySerializer,
    LicenseSerializer,
)
from application.licenses.models import (
    Concluded_License,
    License,
    License_Component,
    License_Component_Evidence,
    License_Group,
    License_Group_Authorization_Group_Member,
    License_Group_Member,
    License_Policy,
    License_Policy_Authorization_Group_Member,
    License_Policy_Item,
    License_Policy_Member,
)
from application.licenses.queries.concluded_license import get_concluded_licenses
from application.licenses.queries.license import get_license
from application.licenses.queries.license_component import (
    get_license_component,
    get_license_component_licenses,
    get_license_components,
)
from application.licenses.queries.license_component_evidence import (
    get_license_component_evidences,
)
from application.licenses.queries.license_group import get_license_groups
from application.licenses.queries.license_group_authorization_group_member import (
    get_license_group_authorization_group_members,
)
from application.licenses.queries.license_group_member import (
    get_license_group_member,
    get_license_group_members,
)
from application.licenses.queries.license_policy import get_license_policies
from application.licenses.queries.license_policy_authorization_group_member import (
    get_license_policy_authorization_group_members,
)
from application.licenses.queries.license_policy_item import get_license_policy_items
from application.licenses.queries.license_policy_member import (
    get_license_policy_member,
    get_license_policy_members,
)
from application.licenses.services.export_license_policy_sbom_utility import (
    export_license_policy_sbom_utility,
)
from application.licenses.services.export_license_policy_secobserve import (
    export_license_policy_secobserve_json,
    export_license_policy_secobserve_yaml,
)
from application.licenses.services.license_component import save_concluded_license
from application.licenses.services.license_group import copy_license_group
from application.licenses.services.license_policy import (
    apply_license_policy,
    apply_license_policy_product,
    copy_license_policy,
)
from application.licenses.types import NO_LICENSE_INFORMATION


@dataclass
class LicenseComponentOverviewElement:
    branch_name: Optional[str]
    effective_license_name: str
    effective_license_type: str
    evaluation_result: str
    num_components: int


@dataclass
class LicenseComponentOverview:
    count: int
    results: list[LicenseComponentOverviewElement]


class ConcludedLicenseViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin, DestroyModelMixin):
    serializer_class = ConcludedLicenseSerializer
    filterset_class = ConcludedLicenseFilter
    queryset = Concluded_License.objects.all()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsAuthenticated, UserHasConcludedLicensePermission]

    def get_serializer_class(self) -> type[ConcludedLicenseListSerializer] | type[BaseSerializer]:
        if self.action == "list":
            return ConcludedLicenseListSerializer
        return super().get_serializer_class()

    def get_queryset(self) -> QuerySet[Concluded_License]:
        return get_concluded_licenses().select_related("product").select_related("user")


class LicenseComponentViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = LicenseComponentSerializer
    filterset_class = LicenseComponentFilter
    queryset = License_Component.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self) -> type[LicenseComponentListSerializer] | type[BaseSerializer]:
        if self.action == "list":
            return LicenseComponentListSerializer
        return super().get_serializer_class()

    def get_queryset(self) -> QuerySet[License_Component]:
        return get_license_components().select_related("branch").select_related("origin_service")

    @extend_schema(
        methods=["GET"],
        responses={200: LicenseComponentListSerializer},
        parameters=[OpenApiParameter(name="component", type=str, required=True)],
    )
    @action(detail=False, methods=["get"])
    def for_component(self, request: Request) -> Response:
        component_id = request.query_params.get("component")
        if not component_id:
            raise ValidationError("No component id provided")
        component = get_component_by_id(component_id)
        if not component or not user_has_permission(component.product, Permissions.Product_View):
            raise NotFound("No Component matches the given query.")
        license_component = License_Component.objects.filter(
            product=component.product,
            branch=component.branch,
            origin_service=component.origin_service,
            component_name_version=component.component_name_version,
            component_purl=component.component_purl,
            component_cpe=component.component_cpe,
            component_dependencies=component.component_dependencies,
            component_cyclonedx_bom_link=component.component_cyclonedx_bom_link,
        ).first()

        if license_component:
            response_serializer = LicenseComponentListSerializer(license_component)
            return Response(status=HTTP_200_OK, data=response_serializer.data)

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(methods=["PATCH"], request=ConcludedLicenseCreateUpdateSerializer, responses={200: None})
    @action(detail=True, methods=["patch"])
    def concluded_license(self, request: Request, pk: int) -> Response:
        request_serializer = ConcludedLicenseCreateUpdateSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        license_component = get_license_component(pk)
        if not license_component:
            raise NotFound(f"License component {pk} not found.")

        user_has_permission_or_403(license_component, Permissions.License_Component_Edit)

        manual_concluded_spdx_license_id = request_serializer.validated_data.get("manual_concluded_spdx_license")
        if manual_concluded_spdx_license_id:
            license_component.manual_concluded_spdx_license = get_license(manual_concluded_spdx_license_id)
            if not license_component.manual_concluded_spdx_license:
                raise ValidationError(f"SPDX license {manual_concluded_spdx_license_id} not found.")
        else:
            license_component.manual_concluded_spdx_license = None
        license_component.manual_concluded_non_spdx_license = request_serializer.validated_data.get(
            "manual_concluded_non_spdx_license", ""
        )
        license_component.manual_concluded_license_expression = request_serializer.validated_data.get(
            "manual_concluded_license_expression", ""
        )

        save_concluded_license(license_component)

        return Response()

    @extend_schema(
        methods=["GET"],
        responses={200: LicenseComponentOverviewSerializer},
        parameters=[
            OpenApiParameter(name="product", type=int, required=True),
            OpenApiParameter(name="branch", type=int),
        ],
    )
    @action(detail=False, methods=["get"])
    def license_overview(self, request: Request) -> Response:
        product_id = request.query_params.get("product")
        if not product_id:
            raise ValidationError("No product id provided")
        if not product_id.isdigit():
            raise ValidationError("Product id is not an integer")
        product = _get_product(int(product_id), Permissions.Product_View)

        filter_branch = None
        branch_id = str(request.query_params.get("branch", ""))
        if branch_id:
            if not branch_id.isdigit():
                raise ValidationError("Branch id is not an integer")
            filter_branch = self._get_branch(product, int(branch_id))

        order_by_1, order_by_2, order_by_3 = self._get_ordering(request.query_params.get("ordering"))

        license_overview_elements = get_license_component_licenses(
            product, filter_branch, order_by_1, order_by_2, order_by_3
        )
        license_overview_elements = self._filter_data(request, license_overview_elements)

        results = []
        for element in license_overview_elements:
            if element["effective_spdx_license__spdx_id"]:
                effective_license_name = element["effective_spdx_license__spdx_id"]
                element_type = "SPDX"
            elif element["effective_license_expression"]:
                effective_license_name = element["effective_license_expression"]
                element_type = "Expression"
            elif element["effective_non_spdx_license"]:
                effective_license_name = element["effective_non_spdx_license"]
                element_type = "Non-SPDX"
            elif element["effective_multiple_licenses"]:
                effective_license_name = element["effective_multiple_licenses"]
                element_type = "Multiple"
            else:
                effective_license_name = NO_LICENSE_INFORMATION
                element_type = ""
            license_component_overview_element = LicenseComponentOverviewElement(
                branch_name=element["branch__name"],
                effective_license_name=effective_license_name,
                effective_license_type=element_type,
                evaluation_result=element["evaluation_result"],
                num_components=element["id__count"],
            )
            results.append(license_component_overview_element)

        license_overview = LicenseComponentOverview(count=len(results), results=results)

        response_serializer = LicenseComponentOverviewSerializer(license_overview)

        return Response(status=HTTP_200_OK, data=response_serializer.data)

    def _get_ordering(self, ordering: Optional[str]) -> Tuple[str, str, str]:
        if ordering and ordering == "-branch_name":
            return ("-branch__name", "-effective_license_name", "-numerical_evaluation_result")
        if ordering and ordering == "branch_name":
            return ("branch__name", "effective_license_name", "numerical_evaluation_result")

        if ordering and ordering == "-effective_license_name":
            return ("-effective_license_name", "-numerical_evaluation_result", "-branch__name")
        if ordering and ordering == "effective_license_name":
            return ("effective_license_name", "numerical_evaluation_result", "branch__name")

        if ordering and ordering == "-evaluation_result":
            return ("-numerical_evaluation_result", "-effective_license_name", "-branch__name")

        return "numerical_evaluation_result", "effective_license_name", "branch__name"

    def _filter_data(self, request: Request, license_overview_elements: QuerySet) -> QuerySet:
        filter_effective_license_name = request.query_params.get("effective_license_name")
        if filter_effective_license_name:
            license_overview_elements = license_overview_elements.filter(
                effective_license_name__icontains=filter_effective_license_name
            )

        filter_evaluation_result = request.query_params.get("evaluation_result")
        if filter_evaluation_result:
            license_overview_elements = license_overview_elements.filter(evaluation_result=filter_evaluation_result)

        filter_component_purl_type = request.query_params.get("component_purl_type")
        if filter_component_purl_type:
            license_overview_elements = license_overview_elements.filter(component_purl_type=filter_component_purl_type)

        filter_origin_service = request.query_params.get("origin_service")
        if filter_origin_service:
            license_overview_elements = license_overview_elements.filter(origin_service=filter_origin_service)

        return license_overview_elements

    def _get_branch(self, product: Product, pk: int) -> Branch:
        branch = get_branch_by_id(product, pk)
        if not branch:
            raise NotFound()

        user_has_permission_or_403(branch, Permissions.Branch_View)

        return branch


class LicenseComponentIdViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = LicenseComponentIdSerializer
    filterset_class = LicenseComponentFilter
    queryset = License_Component.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[License_Component]:
        return get_license_components()


class LicenseComponentEvidenceViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = LicenseComponentEvidenceSerializer
    filterset_class = LicenseComponentEvidenceFilter
    queryset = License_Component_Evidence.objects.none()

    def get_queryset(self) -> QuerySet[License_Component_Evidence]:
        return get_license_component_evidences().select_related("license_component__product")


class LicenseViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = LicenseSerializer
    filterset_class = LicenseFilter
    queryset = License.objects.all()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["spdx_id", "name"]


class LicenseGroupViewSet(ModelViewSet):
    serializer_class = LicenseGroupSerializer
    filterset_class = LicenseGroupFilter
    queryset = License_Group.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]
    permission_classes = [IsAuthenticated, UserHasLicenseGroupPermission]

    def get_queryset(self) -> QuerySet[License_Group]:
        return get_license_groups()

    @extend_schema(
        methods=["POST"], request=LicenseGroupCopySerializer, responses={HTTP_201_CREATED: LicenseGroupSerializer}
    )
    @action(detail=True, methods=["post"])
    def copy(self, request: Request, pk: int) -> Response:
        user = request.user
        if isinstance(user, AnonymousUser):
            raise PermissionDenied("You must be authenticated to copy a license group")
        if user.is_external:
            raise PermissionDenied("You are not allowed to copy a license group")

        request_serializer = LicenseGroupCopySerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        license_group = self._get_license_group(pk)
        if license_group is None:
            raise NotFound("License group not found")

        name = request_serializer.validated_data.get("name")
        try:
            License_Group.objects.get(name=name)
            raise ValidationError("License group with this name already exists")
        except License_Group.DoesNotExist:
            pass

        new_license_group = copy_license_group(license_group, name)

        return Response(status=HTTP_201_CREATED, data=LicenseGroupSerializer(new_license_group).data)

    @extend_schema(
        methods=["POST"], request=LicenseGroupLicenseAddRemoveSerializer, responses={HTTP_204_NO_CONTENT: None}
    )
    @action(detail=True, methods=["post"])
    def add_license(self, request: Request, pk: int) -> Response:
        request_serializer = LicenseGroupLicenseAddRemoveSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        license_group = self._get_license_group(pk, True)
        if license_group is None:
            raise NotFound("License group not found")

        license_id = request_serializer.validated_data.get("license")
        license_to_be_added = get_license(license_id)
        if not license_to_be_added:
            raise ValidationError(f"License {license_id} not found")

        if license_to_be_added in license_group.licenses.filter(id=license_id):
            raise ValidationError(f"License {license_to_be_added} is already in this license group")

        license_group.licenses.add(license_to_be_added)

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"], request=LicenseGroupLicenseAddRemoveSerializer, responses={HTTP_204_NO_CONTENT: None}
    )
    @action(detail=True, methods=["post"])
    def remove_license(self, request: Request, pk: int) -> Response:
        request_serializer = LicenseGroupLicenseAddRemoveSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        license_group = self._get_license_group(pk, True)
        if license_group is None:
            raise NotFound("License group not found")

        license_id = request_serializer.validated_data.get("license")
        license_to_be_removed = get_license(license_id)
        if not license_to_be_removed:
            raise ValidationError(f"License {license_id} not found")

        license_group.licenses.remove(license_to_be_removed)

        return Response(status=HTTP_204_NO_CONTENT)

    def _get_license_group(self, pk: int, manager: Optional[bool] = False) -> License_Group:
        license_group = get_license_groups().filter(pk=pk).first()
        if license_group is None:
            raise NotFound("License group not found")

        if manager:
            user = get_current_user()
            if not user:
                raise PermissionDenied("No user found")

            if user.is_superuser:
                return license_group

            license_group_member = get_license_group_member(license_group, user)

            if not license_group_member or not license_group_member.is_manager:
                raise PermissionDenied("You are not a manager of this license group")

        return license_group


class LicenseGroupMemberViewSet(ModelViewSet):
    serializer_class = LicenseGroupMemberSerializer
    filterset_class = LicenseGroupMemberFilter
    queryset = License_Group_Member.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsAuthenticated, UserHasLicenseGroupMemberPermission]

    def get_queryset(self) -> QuerySet[License_Group_Member]:
        return get_license_group_members().select_related("license_group").select_related("user")


class LicenseGroupAuthorizationGroupMemberViewSet(ModelViewSet):
    serializer_class = LicenseGroupAuthorizationGroupMemberSerializer
    filterset_class = LicenseGroupAuthorizationGroupFilter
    queryset = License_Group_Authorization_Group_Member.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsAuthenticated, UserHasLicenseGroupAuthenticationGroupMemberPermission]

    def get_queryset(self) -> QuerySet[License_Group_Authorization_Group_Member]:
        return (
            get_license_group_authorization_group_members()
            .select_related("license_group")
            .select_related("authorization_group")
        )


class LicensePolicyViewSet(ModelViewSet):
    serializer_class = LicensePolicySerializer
    filterset_class = LicensePolicyFilter
    queryset = License_Policy.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]
    permission_classes = [IsAuthenticated, UserHasLicensePolicyPermission]

    def get_queryset(self) -> QuerySet[License_Policy]:
        return get_license_policies()

    @extend_schema(
        methods=["POST"], request=LicensePolicyCopySerializer, responses={HTTP_201_CREATED: LicensePolicySerializer}
    )
    @action(detail=True, methods=["post"])
    def copy(self, request: Request, pk: int) -> Response:
        user = request.user
        if isinstance(user, AnonymousUser):
            raise PermissionDenied("You must be authenticated to copy a license policy")
        if user.is_external:
            raise PermissionDenied("You are not allowed to copy a license policy")

        request_serializer = LicensePolicyCopySerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        license_policy = self._get_license_policy(pk)
        if license_policy is None:
            raise NotFound("License policy not found")

        name = request_serializer.validated_data.get("name")
        try:
            License_Policy.objects.get(name=name)
            raise ValidationError("License policy with this name already exists")
        except License_Policy.DoesNotExist:
            pass

        new_license_policy = copy_license_policy(license_policy, name)

        return Response(status=HTTP_201_CREATED, data=LicensePolicySerializer(new_license_policy).data)

    @extend_schema(methods=["POST"], request=None, responses={HTTP_204_NO_CONTENT: None})
    @action(detail=True, methods=["post"])
    def apply(self, request: Request, pk: int) -> Response:
        license_policy = self._get_license_policy(pk, True)
        if license_policy is None:
            raise NotFound("License policy not found")

        apply_license_policy(license_policy)

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
        parameters=[OpenApiParameter(name="product", type=int, required=True)],
    )
    @action(detail=False, methods=["post"])
    def apply_product(self, request: Request) -> Response:
        product_id = str(request.query_params.get("product", ""))
        if not product_id:
            raise ValidationError("No product id provided")
        if not product_id.isdigit():
            raise ValidationError("Product id is not an integer")

        product = _get_product(int(product_id), Permissions.Product_Edit)
        apply_license_policy_product(product)

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(methods=["GET"], responses={200: None})
    @action(detail=True, methods=["get"])
    def export_json(self, request: Request, pk: int) -> HttpResponse:
        license_policy = self._get_license_policy(pk, False)
        license_policy_export = export_license_policy_secobserve_json(license_policy)

        response = HttpResponse(  # pylint: disable=http-response-with-content-type-json
            content=license_policy_export, content_type="application/json"
        )
        response["Content-Disposition"] = f"attachment; filename=license_policy_{pk}.json"

        return response

    @extend_schema(methods=["GET"], responses={200: None})
    @action(detail=True, methods=["get"])
    def export_yaml(self, request: Request, pk: int) -> HttpResponse:
        license_policy = self._get_license_policy(pk, False)
        license_policy_export = export_license_policy_secobserve_yaml(license_policy)

        response = HttpResponse(content=license_policy_export, content_type="application/yaml")
        response["Content-Disposition"] = f"attachment; filename=license_policy_{pk}.yaml"

        return response

    @extend_schema(methods=["GET"], responses={200: None})
    @action(detail=True, methods=["get"])
    def export_sbom_utility(self, request: Request, pk: int) -> HttpResponse:
        license_policy = self._get_license_policy(pk, False)
        license_policy_export = export_license_policy_sbom_utility(license_policy)

        response = HttpResponse(  # pylint: disable=http-response-with-content-type-json
            content=license_policy_export, content_type="application/json"
        )
        response["Content-Disposition"] = f"attachment; filename=license_policy_{pk}.json"

        return response

    def _get_license_policy(self, pk: int, manager: Optional[bool] = False) -> License_Policy:
        license_policy = get_license_policies().filter(pk=pk).first()
        if license_policy is None:
            raise NotFound("License policy not found")

        if manager:
            user = get_current_user()
            if not user:
                raise PermissionDenied("No user found")

            if user.is_superuser:
                return license_policy

            license_policy_member = get_license_policy_member(license_policy, user)

            if not license_policy_member or not license_policy_member.is_manager:
                raise PermissionDenied("You are not a manager of this license policy")

        return license_policy


class LicensePolicyItemViewSet(ModelViewSet):
    serializer_class = LicensePolicyItemSerializer
    filterset_class = LicensePolicyItemFilter
    queryset = License_Policy_Item.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsAuthenticated, UserHasLicensePolicyItemMemberPermission]

    def get_queryset(self) -> QuerySet[License_Policy_Item]:
        return (
            get_license_policy_items()
            .select_related("license_policy")
            .select_related("license")
            .select_related("license_group")
        )


class LicensePolicyMemberViewSet(ModelViewSet):
    serializer_class = LicensePolicyMemberSerializer
    filterset_class = LicensePolicyMemberFilter
    queryset = License_Policy_Member.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsAuthenticated, UserHasLicensePolicyItemMemberPermission]

    def get_queryset(self) -> QuerySet[License_Policy_Member]:
        return get_license_policy_members().select_related("license_policy").select_related("user")


class LicensePolicyAuthorizationGroupMemberViewSet(ModelViewSet):
    serializer_class = LicensePolicyAuthorizationGroupMemberSerializer
    filterset_class = LicensePolicyAuthorizationGroupFilter
    queryset = License_Policy_Authorization_Group_Member.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    permission_classes = [IsAuthenticated, UserHasLicensePolicyAuthorizationGroupMemberPermission]

    def get_queryset(self) -> QuerySet[License_Policy_Authorization_Group_Member]:
        return (
            get_license_policy_authorization_group_members()
            .select_related("license_policy")
            .select_related("authorization_group")
        )


def _get_product(product_id: int, permission: Permissions) -> Product:
    if not product_id:
        raise ValidationError("No product id provided")

    product = get_product_by_id(product_id)
    if not product:
        raise NotFound()

    user_has_permission_or_403(product, permission)

    return product
