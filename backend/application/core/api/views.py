import logging
import re
from tempfile import NamedTemporaryFile
from typing import Any

from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ViewSet

from application.access_control.api.serializers import (
    ApiTokenCreateResponseSerializer,
)
from application.access_control.queries.api_token import get_api_token_by_id
from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import (
    user_has_permission,
    user_has_permission_or_403,
)
from application.authorization.services.roles_permissions import Permissions
from application.commons.services.log_message import format_log_message
from application.core.api.filters import (
    BranchFilter,
    ComponentFilter,
    EvidenceFilter,
    ObservationFilter,
    ObservationLogFilter,
    PotentialDuplicateFilter,
    ProductAuthorizationGroupMemberFilter,
    ProductFilter,
    ProductGroupFilter,
    ProductMemberFilter,
    ServiceFilter,
)
from application.core.api.permissions import (
    UserHasBranchPermission,
    UserHasObservationPermission,
    UserHasProductAuthorizationGroupMemberPermission,
    UserHasProductGroupPermission,
    UserHasProductMemberPermission,
    UserHasProductPermission,
    UserHasServicePermission,
)
from application.core.api.serializers_component import (
    ComponentNameSerializer,
    ComponentSerializer,
)
from application.core.api.serializers_observation import (
    CountSerializer,
    EvidenceSerializer,
    ObservationAssessmentSerializer,
    ObservationBulkAssessmentSerializer,
    ObservationBulkDeleteSerializer,
    ObservationBulkMarkDuplicatesSerializer,
    ObservationCreateSerializer,
    ObservationListSerializer,
    ObservationLogApprovalSerializer,
    ObservationLogBulkApprovalSerializer,
    ObservationLogBulkDeleteSerializer,
    ObservationLogListSerializer,
    ObservationLogSerializer,
    ObservationRemoveAssessmentSerializer,
    ObservationSerializer,
    ObservationTitleSerializer,
    ObservationUpdateSerializer,
    PotentialDuplicateSerializer,
)
from application.core.api.serializers_product import (
    BranchNameSerializer,
    BranchSerializer,
    ProductApiTokenSerializer,
    ProductAuthorizationGroupMemberSerializer,
    ProductGroupSerializer,
    ProductMemberSerializer,
    ProductNameSerializer,
    ProductSerializer,
    PURLTypeElementSerializer,
    PURLTypeSerializer,
    ServiceNameSerializer,
    ServiceSerializer,
)
from application.core.models import (
    Branch,
    Component,
    Evidence,
    Observation,
    Observation_Log,
    Potential_Duplicate,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
    Service,
)
from application.core.queries.branch import get_branches
from application.core.queries.component import get_components
from application.core.queries.observation import (
    get_current_observation_log,
    get_evidences,
    get_observation_by_id,
    get_observation_log_by_id,
    get_observation_logs,
    get_observations,
    get_potential_duplicates,
)
from application.core.queries.product import get_product_by_id, get_products
from application.core.queries.product_member import (
    get_product_authorization_group_members,
    get_product_members,
)
from application.core.queries.service import get_services
from application.core.services.assessment import (
    assessment_approval,
    remove_assessment,
    save_assessment,
)
from application.core.services.export_observations import (
    export_observations_csv,
    export_observations_excel,
)
from application.core.services.observations_bulk_actions import (
    observation_logs_bulk_approval,
    observations_bulk_assessment,
    observations_bulk_delete,
    observations_bulk_mark_duplicates,
)
from application.core.services.potential_duplicates import (
    set_potential_duplicate_both_ways,
)
from application.core.services.product_api_token import (
    create_product_api_token,
    get_product_api_tokens,
    revoke_product_api_token,
)
from application.core.services.purl_type import get_purl_type, get_purl_types
from application.core.services.security_gate import check_security_gate
from application.core.types import Assessment_Status, Status
from application.issue_tracker.services.issue_tracker import (
    push_deleted_observation_to_issue_tracker,
    push_observations_to_issue_tracker,
)
from application.licenses.api.serializers import LicenseComponentBulkDeleteSerializer
from application.licenses.services.export_license_components import (
    export_license_components_csv,
    export_license_components_excel,
)
from application.licenses.services.license_component import (
    license_components_bulk_delete,
)
from application.rules.services.rule_engine import Rule_Engine

logger = logging.getLogger("secobserve.core")


class ProductGroupViewSet(ModelViewSet):
    serializer_class = ProductGroupSerializer
    filterset_class = ProductGroupFilter
    permission_classes = (IsAuthenticated, UserHasProductGroupPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        return get_products(is_product_group=True)


class ProductGroupNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ProductNameSerializer
    filterset_class = ProductGroupFilter
    permission_classes = (IsAuthenticated, UserHasProductGroupPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        return get_products(is_product_group=True)


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    permission_classes = (IsAuthenticated, UserHasProductPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        return (
            get_products(is_product_group=False, with_annotations=True)
            .select_related("product_group")
            .select_related("product_group__license_policy")
            .select_related("repository_default_branch")
        )

    @extend_schema(
        methods=["GET"],
        responses={200: None},
        parameters=[
            OpenApiParameter(name="status", description="status", type=str),
        ],
    )
    @action(detail=True, methods=["get"])
    def export_observations_excel(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        status = self.request.query_params.get("status")
        if status and (status, status) not in Status.STATUS_CHOICES:
            raise ValidationError(f"Status {status} is not a valid choice")

        workbook = export_observations_excel(product, status)

        with NamedTemporaryFile() as tmp:
            workbook.save(tmp.name)  # nosemgrep: python.lang.correctness.tempfile.flush.tempfile-without-flush
            # export works fine without .flush()
            tmp.seek(0)
            stream = tmp.read()

        response = HttpResponse(
            content=stream,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = "attachment; filename=observations.xlsx"

        return response

    @extend_schema(
        methods=["GET"],
        responses={200: None},
        parameters=[
            OpenApiParameter(name="status", description="status", type=str),
        ],
    )
    @action(detail=True, methods=["get"])
    def export_observations_csv(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        status = self.request.query_params.get("status")
        if status and (status, status) not in Status.STATUS_CHOICES:
            raise ValidationError(f"Status {status} is not a valid choice")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=observations.csv"

        export_observations_csv(response, product, status)

        return response

    @action(detail=True, methods=["get"])
    def export_license_components_excel(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        workbook = export_license_components_excel(product)

        with NamedTemporaryFile() as tmp:
            workbook.save(tmp.name)  # nosemgrep: python.lang.correctness.tempfile.flush.tempfile-without-flush
            # export works fine without .flush()
            tmp.seek(0)
            stream = tmp.read()

        response = HttpResponse(
            content=stream,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = "attachment; filename=license_components.xlsx"

        return response

    @extend_schema(
        methods=["GET"],
        responses={200: None},
    )
    @action(detail=True, methods=["get"])
    def export_license_components_csv(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=license_observations.csv"

        export_license_components_csv(response, product)

        return response

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def apply_rules(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Product_Rule_Apply)

        rule_engine = Rule_Engine(product)
        rule_engine.apply_all_rules_for_product()

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=ObservationBulkAssessmentSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def observations_bulk_assessment(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Observation_Assessment)

        request_serializer = ObservationBulkAssessmentSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observations_bulk_assessment(
            product=product,
            new_severity=request_serializer.validated_data.get("severity"),
            new_status=request_serializer.validated_data.get("status"),
            comment=request_serializer.validated_data.get("comment"),
            observation_ids=request_serializer.validated_data.get("observations"),
            new_vex_justification=request_serializer.validated_data.get("vex_justification"),
            new_risk_acceptance_expiry_date=request_serializer.validated_data.get("risk_acceptance_expiry_date"),
        )
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=ObservationBulkMarkDuplicatesSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def observations_bulk_mark_duplicates(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Observation_Assessment)

        request_serializer = ObservationBulkMarkDuplicatesSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observations_bulk_mark_duplicates(
            product,
            request_serializer.validated_data.get("observation_id"),
            request_serializer.validated_data.get("potential_duplicates"),
        )
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=ObservationBulkDeleteSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def observations_bulk_delete(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Observation_Delete)

        request_serializer = ObservationBulkDeleteSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observations_bulk_delete(product, request_serializer.validated_data.get("observations"))
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=LicenseComponentBulkDeleteSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def license_components_bulk_delete(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.License_Component_Delete)

        request_serializer = LicenseComponentBulkDeleteSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        license_components_bulk_delete(product, request_serializer.validated_data.get("components"))
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def synchronize_issues(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Product_Edit)

        observations = Observation.objects.filter(product=product)
        push_observations_to_issue_tracker(product, set(observations))

        return Response(status=HTTP_204_NO_CONTENT)

    def __get_product(self, pk: int) -> Product:
        if not pk:
            raise ValidationError("No id provided")

        product = get_product_by_id(pk)
        if not product:
            raise NotFound()

        user_has_permission_or_403(product, Permissions.Product_View)

        return product


class ProductNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ProductNameSerializer
    filterset_class = ProductFilter
    permission_classes = (IsAuthenticated, UserHasProductPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        return get_products(is_product_group=False)


class ProductMemberViewSet(ModelViewSet):
    serializer_class = ProductMemberSerializer
    filterset_class = ProductMemberFilter
    permission_classes = (IsAuthenticated, UserHasProductMemberPermission)
    queryset = Product_Member.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[Product_Member]:
        return get_product_members().select_related("product").select_related("user")


class ProductAuthorizationGroupMemberViewSet(ModelViewSet):
    serializer_class = ProductAuthorizationGroupMemberSerializer
    filterset_class = ProductAuthorizationGroupMemberFilter
    permission_classes = (
        IsAuthenticated,
        UserHasProductAuthorizationGroupMemberPermission,
    )
    queryset = Product_Authorization_Group_Member.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[Product_Authorization_Group_Member]:
        return get_product_authorization_group_members().select_related("product").select_related("authorization_group")


class BranchViewSet(ModelViewSet):
    serializer_class = BranchSerializer
    filterset_class = BranchFilter
    permission_classes = (IsAuthenticated, UserHasBranchPermission)
    queryset = Branch.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Branch]:
        return get_branches().select_related("product")

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance: Branch = self.get_object()
        if instance == instance.product.repository_default_branch:
            raise ValidationError("You cannot delete the default branch of a product.")

        return super().destroy(request, *args, **kwargs)


class BranchNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = BranchNameSerializer
    filterset_class = BranchFilter
    permission_classes = (IsAuthenticated, UserHasBranchPermission)
    queryset = Branch.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Branch]:
        return get_branches().select_related("product")


class ServiceViewSet(ModelViewSet):
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    permission_classes = (IsAuthenticated, UserHasServicePermission)
    queryset = Service.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Service]:
        return get_services().select_related("product")


class ServiceNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ServiceNameSerializer
    filterset_class = ServiceFilter
    permission_classes = (IsAuthenticated, UserHasServicePermission)
    queryset = Service.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Service]:
        return get_services().select_related("product")


class ObservationViewSet(ModelViewSet):
    serializer_class = ObservationSerializer
    filterset_class = ObservationFilter
    permission_classes = (IsAuthenticated, UserHasObservationPermission)
    queryset = Observation.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["title"]

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return ObservationListSerializer

        if self.action == "create":
            return ObservationCreateSerializer

        if self.action in ["update", "partial_update"]:
            return ObservationUpdateSerializer

        return super().get_serializer_class()

    def get_queryset(self) -> QuerySet[Observation]:
        return (
            get_observations()
            .select_related("product")
            .select_related("product__product_group")
            .select_related("branch")
            .select_related("parser")
        )

    def perform_destroy(self, instance: Observation) -> None:
        product = instance.product
        issue_id = instance.issue_tracker_issue_id
        observation_branch = instance.branch
        super().perform_destroy(instance)
        if observation_branch == product.repository_default_branch:
            check_security_gate(product)
        push_deleted_observation_to_issue_tracker(product, issue_id, get_current_user())
        product.last_observation_change = timezone.now()
        product.save()

    @extend_schema(
        methods=["PATCH"],
        request=ObservationAssessmentSerializer,
        responses={200: None},
    )
    @action(detail=True, methods=["patch"])
    def assessment(self, request: Request, pk: int) -> Response:
        request_serializer = ObservationAssessmentSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observation = get_observation_by_id(pk)
        if not observation:
            raise NotFound(f"Observation {pk} not found")

        user_has_permission_or_403(observation, Permissions.Observation_Assessment)

        current_observation_log = get_current_observation_log(observation)
        if (
            current_observation_log
            and current_observation_log.assessment_status == Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL
        ):
            raise ValidationError("Cannot create new assessment while last assessment still needs approval")

        new_severity = request_serializer.validated_data.get("severity")
        new_status = request_serializer.validated_data.get("status")
        comment = request_serializer.validated_data.get("comment")
        new_vex_justification = request_serializer.validated_data.get("vex_justification")
        new_risk_acceptance_expiry_date = request_serializer.validated_data.get("risk_acceptance_expiry_date")

        save_assessment(
            observation=observation,
            new_severity=new_severity,
            new_status=new_status,
            comment=comment,
            new_vex_justification=new_vex_justification,
            new_risk_acceptance_expiry_date=new_risk_acceptance_expiry_date,
        )
        set_potential_duplicate_both_ways(observation)

        return Response()

    @extend_schema(
        methods=["PATCH"],
        request=ObservationRemoveAssessmentSerializer,
        responses={200: None},
    )
    @action(detail=True, methods=["patch"])
    def remove_assessment(self, request: Request, pk: int) -> Response:
        request_serializer = ObservationRemoveAssessmentSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observation = get_observation_by_id(pk)
        if not observation:
            raise NotFound(f"Observation {pk} not found")

        user_has_permission_or_403(observation, Permissions.Observation_Assessment)

        current_observation_log = get_current_observation_log(observation)
        if (
            current_observation_log
            and current_observation_log.assessment_status == Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL
        ):
            raise ValidationError("Cannot remove assessment while last assessment still needs approval")

        comment = request_serializer.validated_data.get("comment")

        remove_assessment(observation, comment)
        set_potential_duplicate_both_ways(observation)

        return Response()

    @extend_schema(
        methods=["POST"],
        request=ObservationBulkAssessmentSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=["post"])
    def bulk_assessment(self, request: Request) -> Response:
        request_serializer = ObservationBulkAssessmentSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observations_bulk_assessment(
            product=None,
            new_severity=request_serializer.validated_data.get("severity"),
            new_status=request_serializer.validated_data.get("status"),
            comment=request_serializer.validated_data.get("comment"),
            observation_ids=request_serializer.validated_data.get("observations"),
            new_vex_justification=request_serializer.validated_data.get("vex_justification"),
            new_risk_acceptance_expiry_date=request_serializer.validated_data.get("risk_acceptance_expiry_date"),
        )
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: CountSerializer},
    )
    @action(detail=False, methods=["get"])
    def count_reviews(self, request: Request) -> Response:
        count = get_observations().filter(current_status=Status.STATUS_IN_REVIEW).count()
        return Response(status=HTTP_200_OK, data={"count": count})


class ObservationTitleViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ObservationTitleSerializer
    filterset_class = ObservationFilter
    permission_classes = (IsAuthenticated, UserHasObservationPermission)
    queryset = Observation.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["title"]

    def get_queryset(self) -> QuerySet[Observation]:
        return get_observations()


class ObservationLogViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ObservationLogSerializer
    filterset_class = ObservationLogFilter
    queryset = Observation_Log.objects.all()
    filter_backends = [SearchFilter, DjangoFilterBackend]

    def get_serializer_class(
        self,
    ) -> type[ObservationLogListSerializer] | type[BaseSerializer]:
        if self.action == "list":
            return ObservationLogListSerializer

        return super().get_serializer_class()

    def get_queryset(self) -> QuerySet[Observation_Log]:
        return get_observation_logs().select_related("observation").select_related("user")

    @extend_schema(
        methods=["PATCH"],
        request=ObservationLogApprovalSerializer,
        responses={200: None},
    )
    @action(detail=True, methods=["patch"])
    def approval(self, request: Request, pk: int) -> Response:
        request_serializer = ObservationLogApprovalSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observation_log = get_observation_log_by_id(pk)
        if not observation_log:
            raise NotFound(f"Observation Log {pk} not found")

        user_has_permission_or_403(observation_log, Permissions.Observation_Log_Approval)

        assessment_status = request_serializer.validated_data.get("assessment_status")
        approval_remark = request_serializer.validated_data.get("approval_remark")
        assessment_approval(observation_log, assessment_status, approval_remark)

        set_potential_duplicate_both_ways(observation_log.observation)

        return Response()

    @extend_schema(
        methods=["POST"],
        request=ObservationLogBulkApprovalSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=["post"])
    def bulk_approval(self, request: Request) -> Response:
        request_serializer = ObservationLogBulkApprovalSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observation_logs_bulk_approval(
            request_serializer.validated_data.get("assessment_status"),
            request_serializer.validated_data.get("approval_remark"),
            request_serializer.validated_data.get("observation_logs"),
        )
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: CountSerializer},
    )
    @action(detail=False, methods=["get"])
    def count_approvals(self, request: Request) -> Response:
        count = (
            get_observation_logs().filter(assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL).count()
        )
        return Response(status=HTTP_200_OK, data={"count": count})

    @extend_schema(
        methods=["DELETE"],
        request=ObservationLogBulkApprovalSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request: Request) -> Response:
        request_serializer = ObservationLogBulkDeleteSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        result = Observation_Log.objects.filter(
            id__in=request_serializer.validated_data.get("observation_logs"),
            user=get_current_user(),
        ).delete()

        if result[0] == 0:
            raise ValidationError("No assessments were deleted. You can only delete your own assessments.")

        return Response({"count": result[0]}, status=HTTP_200_OK)


class EvidenceViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = EvidenceSerializer
    filterset_class = EvidenceFilter
    queryset = Evidence.objects.none()

    def get_queryset(self) -> QuerySet[Evidence]:
        return get_evidences().select_related("observation__product")


class PotentialDuplicateViewSet(GenericViewSet, ListModelMixin):
    serializer_class = PotentialDuplicateSerializer
    filterset_class = PotentialDuplicateFilter
    queryset = Potential_Duplicate.objects.none()

    def get_queryset(self) -> QuerySet[Potential_Duplicate]:
        return get_potential_duplicates()


class PURLTypeOneView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: PURLTypeSerializer},
    )
    @action(detail=True, methods=["get"])
    def get(self, request: Request, purl_type_id: str) -> Response:
        purl_type = get_purl_type(purl_type_id)
        if purl_type:
            response_serializer = PURLTypeElementSerializer(purl_type)
            return Response(
                status=HTTP_200_OK,
                data=response_serializer.data,
            )

        return Response(status=HTTP_404_NOT_FOUND)


class PURLTypeManyView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: PURLTypeSerializer},
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> Response:
        product_id = request.query_params.get("product")
        if not product_id:
            return Response(status=HTTP_404_NOT_FOUND)
        product = get_product_by_id(int(product_id))
        if not product:
            return Response(status=HTTP_404_NOT_FOUND)
        if not user_has_permission(product, Permissions.Product_View):
            return Response(status=HTTP_404_NOT_FOUND)

        for_observations = bool(request.query_params.get("for_observations"))
        for_license_components = bool(request.query_params.get("for_license_components"))
        purl_types = get_purl_types(product, for_observations, for_license_components)

        response_serializer = PURLTypeSerializer(purl_types)
        return Response(
            status=HTTP_200_OK,
            data=response_serializer.data,
        )


class ProductApiTokenViewset(ViewSet):
    serializer_class = ProductApiTokenSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name="product", location=OpenApiParameter.QUERY, required=True, type=int),
        ],
    )
    def list(self, request: Request) -> Response:
        product_id = str(request.query_params.get("product", ""))
        if not product_id:
            raise ValidationError("Product is required")
        if not product_id.isdigit():
            raise ValidationError("Product id must be an integer")

        product = _get_product(int(str(product_id)))
        user_has_permission_or_403(product, Permissions.Product_View)
        tokens = get_product_api_tokens(product)
        serializer = ProductApiTokenSerializer(tokens, many=True)
        response_data = {"results": serializer.data}
        return Response(response_data)

    @extend_schema(
        request=ProductApiTokenSerializer,
        responses={HTTP_200_OK: ApiTokenCreateResponseSerializer},
    )
    def create(self, request: Request) -> Response:
        request_serializer = ProductApiTokenSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        product = _get_product(request_serializer.validated_data.get("product"))

        user_has_permission_or_403(product, Permissions.Product_Api_Token_Create)

        token = create_product_api_token(
            product,
            request_serializer.validated_data.get("role"),
            request_serializer.validated_data.get("name"),
            request_serializer.validated_data.get("expiration_date"),
        )

        response = Response({"token": token}, status=HTTP_201_CREATED)
        logger.info(format_log_message(message="Product API token created", response=response))
        return response

    @extend_schema(
        responses={HTTP_204_NO_CONTENT: None},
    )
    def destroy(self, request: Request, pk: int) -> Response:
        API_TOKEN_NOT_VALID = "API token not valid"

        api_token = get_api_token_by_id(pk)
        if not api_token:
            raise ValidationError(API_TOKEN_NOT_VALID)

        if not re.match("-product-(\\d)*(-.*)?-api_token-", api_token.user.username):
            raise ValidationError(API_TOKEN_NOT_VALID)

        product_member = Product_Member.objects.filter(user=api_token.user).first()
        if not product_member:
            raise ValidationError(API_TOKEN_NOT_VALID)

        product = _get_product(product_member.product.pk)
        user_has_permission_or_403(product, Permissions.Product_Api_Token_Revoke)

        revoke_product_api_token(product, api_token)

        response = Response(status=HTTP_204_NO_CONTENT)
        logger.info(format_log_message(message="Product API token revoked", response=response))
        return response


class ComponentViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ComponentSerializer
    filterset_class = ComponentFilter
    permission_classes = (IsAuthenticated,)
    queryset = Component.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["component_name_version"]

    def get_queryset(self) -> QuerySet[Component]:
        return (
            get_components()
            .select_related("product")
            .select_related("product__product_group")
            .select_related("branch")
            .select_related("origin_service")
        )


class ComponentNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ComponentNameSerializer
    filterset_class = ComponentFilter
    permission_classes = (IsAuthenticated,)
    queryset = Component.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["component_name_version"]

    def get_queryset(self) -> QuerySet[Component]:
        return get_components()


def _get_product(product_id: int) -> Product:
    product = get_product_by_id(product_id)
    if not product:
        raise ValidationError(f"Product {product_id} does not exist")

    return product
