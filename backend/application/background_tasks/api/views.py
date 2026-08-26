from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from huey.contrib.djhuey import HUEY as huey
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_409_CONFLICT
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from application.background_tasks.api.filters import PeriodicTaskFilter
from application.background_tasks.api.serializers import (
    BackgroundTaskStatisticsSerializer,
    PeriodicTaskRegisteredSerializer,
    PeriodicTaskRunSerializer,
    PeriodicTaskSerializer,
)
from application.background_tasks.models import Periodic_Task
from application.background_tasks.services.registry import (
    PERIODIC_TASKS,
    get_periodic_task,
)
from application.background_tasks.types import Status
from application.commons.api.permissions import UserHasSuperuserPermission


class PeriodicTaskViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = PeriodicTaskSerializer
    filterset_class = PeriodicTaskFilter
    permission_classes = [IsAuthenticated, UserHasSuperuserPermission]
    queryset = Periodic_Task.objects.all()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["task"]

    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: PeriodicTaskRegisteredSerializer},
    )
    @action(detail=False, methods=["get"])
    def registered_tasks(self, request: Request) -> Response:
        response_serializer = PeriodicTaskRegisteredSerializer({"tasks": sorted(PERIODIC_TASKS.keys())})
        return Response(response_serializer.data)

    @extend_schema(
        methods=["POST"],
        request=PeriodicTaskRunSerializer,
        responses={HTTP_202_ACCEPTED: None},
    )
    @action(detail=False, methods=["post"])
    def run(self, request: Request) -> Response:
        request_serializer = PeriodicTaskRunSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        task_name = request_serializer.validated_data.get("task")
        periodic_task = get_periodic_task(task_name)
        if periodic_task is None:
            raise ValidationError(f"Task '{task_name}' does not exist")

        if Periodic_Task.objects.filter(task=task_name, status=Status.STATUS_RUNNING).exists():
            return Response(
                {"detail": f"Task '{task_name}' is currently running"},
                status=HTTP_409_CONFLICT,
            )

        periodic_task()

        return Response(status=HTTP_202_ACCEPTED)


class BackgroundTaskView(APIView):
    permission_classes = [IsAuthenticated, UserHasSuperuserPermission]
    serializer_class = BackgroundTaskStatisticsSerializer

    @action(detail=False, methods=["get"], url_name="background_task_statistics")
    def get(self, request: Request) -> Response:
        stats = getattr(huey, "_stats", None)
        if stats is None:
            return Response({"detail": "Huey statistics are not enabled."}, status=503)

        content = {
            "registered": stats.task_breakdown(),
            "throughput": stats.throughput(minutes=60),
            "counts": stats.window_counts(seconds=86400),
            "running": stats.inflight(),
        }

        serializer = BackgroundTaskStatisticsSerializer(content)
        return Response(serializer.data)
