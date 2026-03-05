from tempfile import NamedTemporaryFile

from django.db.models import QuerySet
from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.core.api.filters import (
    EvidenceFilter,
    ObservationFilter,
    ObservationLogFilter,
    PotentialDuplicateFilter,
)
from application.core.api.permissions import UserHasObservationPermission
from application.core.api.serializers_observation import (
    CountSerializer,
    EvidenceSerializer,
    ObservationAssessmentSerializer,
    ObservationBulkAssessmentSerializer,
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
from application.core.models import (
    Evidence,
    Observation,
    Observation_Log,
    Potential_Duplicate,
)
from application.core.queries.observation import (
    get_current_observation_log,
    get_evidences,
    get_observation_by_id,
    get_observation_log_by_id,
    get_observation_logs,
    get_observations,
    get_potential_duplicates,
)
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
)
from application.core.services.potential_duplicates import (
    set_potential_duplicate_both_ways,
)
from application.core.services.security_gate import check_security_gate
from application.core.types import Assessment_Status, Status


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
            .select_related("origin_service")
        )

    def perform_destroy(self, instance: Observation) -> None:
        product = instance.product

        super().perform_destroy(instance)
        if (instance.branch and instance.branch.is_default_branch) or (
            not instance.branch and not instance.product.repository_default_branch
        ):
            check_security_gate(product)

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

        save_assessment(
            observation=observation,
            new_severity=request_serializer.validated_data.get("severity"),
            new_status=request_serializer.validated_data.get("status"),
            new_priority=request_serializer.validated_data.get("priority"),
            comment=request_serializer.validated_data.get("comment"),
            new_vex_justification=request_serializer.validated_data.get("vex_justification"),
            new_risk_acceptance_expiry_date=request_serializer.validated_data.get("risk_acceptance_expiry_date"),
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
            new_priority=request_serializer.validated_data.get("priority"),
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

    @extend_schema(
        methods=["GET"],
        responses={200: None},
    )
    @action(detail=False, methods=["get"])
    def export_excel(self, request: Request) -> HttpResponse:
        queryset = self._filter_queryset(request)
        workbook = export_observations_excel(queryset)

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
        parameters=[],
    )
    @action(detail=False, methods=["get"])
    def export_csv(self, request: Request) -> HttpResponse:
        queryset = self._filter_queryset(request)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=observations.csv"
        export_observations_csv(response, queryset)
        return response

    def _filter_queryset(self, request: Request) -> QuerySet:
        queryset = self.get_queryset()
        for backend in self.filter_backends:
            queryset = backend().filter_queryset(request, queryset, self)
        return queryset


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
        return (
            get_observation_logs()
            .select_related("observation")
            .select_related("observation__product")
            .select_related("observation__branch")
            .select_related("observation__parser")
            .select_related("observation__origin_service")
            .select_related("user")
        )

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
        return get_evidences().select_related("observation").select_related("observation__product")


class PotentialDuplicateViewSet(GenericViewSet, ListModelMixin):
    serializer_class = PotentialDuplicateSerializer
    filterset_class = PotentialDuplicateFilter
    queryset = Potential_Duplicate.objects.none()

    def get_queryset(self) -> QuerySet[Potential_Duplicate]:
        return (
            get_potential_duplicates()
            .select_related("observation")
            .select_related("observation__product")
            .select_related("observation__branch")
            .select_related("observation__parser")
            .select_related("observation__origin_service")
        )
