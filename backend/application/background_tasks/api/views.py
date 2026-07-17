from django_filters.rest_framework import DjangoFilterBackend
from huey.contrib.djhuey import HUEY as huey
from huey.contrib.stats import enable_stats
from peewee import SqliteDatabase
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from application.background_tasks.api.filters import PeriodicTaskFilter
from application.background_tasks.api.serializers import (
    BackgroundTaskStatisticsSerializer,
    PeriodicTaskSerializer,
)
from application.background_tasks.models import Periodic_Task
from application.commons.api.permissions import UserHasSuperuserPermission


class PeriodicTaskViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = PeriodicTaskSerializer
    filterset_class = PeriodicTaskFilter
    permission_classes = [IsAuthenticated, UserHasSuperuserPermission]
    queryset = Periodic_Task.objects.all()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["task"]


class BackgroundTaskView(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = BackgroundTaskStatisticsSerializer

    @action(detail=False, methods=["get"], url_name="background_task_statistics")
    def get(self, request: Request) -> Response:
        stats_db = SqliteDatabase("/var/lib/huey/huey_stats.db")
        stats = enable_stats(huey, stats_db)

        content = {
            "task_breakdown": stats.task_breakdown(),  # per-task executed/completed/errors/avg
            "throughput": stats.throughput(minutes=60),  # {'complete': [...], 'error': [...]} per minute
            "inflight": stats.inflight(),  # tasks currently executing
        }
        serializer = BackgroundTaskStatisticsSerializer(content)
        return Response(serializer.data)
