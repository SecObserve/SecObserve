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


class BackgroundTaskCountsSerializer(Serializer):
    # Number of tasks per huey signal within the observed time window.
    # Signals that did not occur are absent from the source dict, so default to 0.
    enqueued = IntegerField(required=False, default=0)
    scheduled = IntegerField(required=False, default=0)
    executing = IntegerField(required=False, default=0)
    complete = IntegerField(required=False, default=0)
    error = IntegerField(required=False, default=0)
    retrying = IntegerField(required=False, default=0)
    revoked = IntegerField(required=False, default=0)
    canceled = IntegerField(required=False, default=0)
    expired = IntegerField(required=False, default=0)
    locked = IntegerField(required=False, default=0)
    interrupted = IntegerField(required=False, default=0)


class BackgroundTaskStatisticsSerializer(Serializer):
    registered = BackgroundTaskBreakdownSerializer(many=True)
    throughput = BackgroundTaskThroughputSerializer()
    counts = BackgroundTaskCountsSerializer()
    running = BackgroundTaskInflightSerializer(many=True)
