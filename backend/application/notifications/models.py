from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    Model,
    OneToOneField,
    TextField,
)

from application.access_control.models import User
from application.core.models import Observation, Product
from application.core.types import Severity, Status


class Notification(Model):
    TYPE_EXCEPTION = "Exception"
    TYPE_OBSERVATION = "Observation"
    TYPE_SECURITY_GATE = "Security gate"
    TYPE_TASK = "Task"

    TYPE_CHOICES = [
        (TYPE_EXCEPTION, TYPE_EXCEPTION),
        (TYPE_OBSERVATION, TYPE_OBSERVATION),
        (TYPE_SECURITY_GATE, TYPE_SECURITY_GATE),
        (TYPE_TASK, TYPE_TASK),
    ]

    name = CharField(max_length=255)
    created = DateTimeField(auto_now_add=True)
    message = TextField(max_length=4096)
    user = ForeignKey(User, on_delete=CASCADE, null=True)
    product = ForeignKey(Product, on_delete=CASCADE, null=True)
    observation = ForeignKey(Observation, on_delete=CASCADE, null=True)
    type = CharField(max_length=20, choices=TYPE_CHOICES)
    function = CharField(max_length=255, blank=True)
    arguments = TextField(max_length=4096, blank=True)

    class Meta:
        db_table = "commons_notification"


class Notification_Viewed(Model):
    notification = ForeignKey(Notification, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)

    class Meta:
        db_table = "commons_notification_viewed"


class Observation_Notified(Model):
    observation = OneToOneField(Observation, on_delete=CASCADE)
    severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)
    status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)
    priority = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)], null=True)


class Observation_Title_Notified(Model):
    title = CharField(max_length=255, unique=True)
    severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)
    status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)
    priority = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)], null=True)
