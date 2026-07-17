from rest_framework.serializers import (
    CharField,
    FloatField,
    IntegerField,
    ListField,
    ModelSerializer,
    Serializer,
)

from application.background_tasks.models import Periodic_Task


class PeriodicTaskSerializer(ModelSerializer):
    class Meta:
        model = Periodic_Task
        fields = "__all__"


class BackgroundTaskBreakdownSerializer(Serializer):
    task = CharField()
    full = CharField()
    executed = IntegerField()
    completed = IntegerField()
    errors = IntegerField()  # type: ignore[assignment]
    retries = IntegerField()
    avg = FloatField(allow_null=True)


class BackgroundTaskThroughputSerializer(Serializer):
    complete = ListField(child=IntegerField())
    error = ListField(child=IntegerField())


class BackgroundTaskInflightSerializer(Serializer):
    task = CharField()
    id = CharField()
    started = FloatField()
    elapsed = FloatField()


class BackgroundTaskStatisticsSerializer(Serializer):
    task_breakdown = BackgroundTaskBreakdownSerializer(many=True)
    throughput = BackgroundTaskThroughputSerializer()
    inflight = BackgroundTaskInflightSerializer(many=True)
