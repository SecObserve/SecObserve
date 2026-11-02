from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    Index,
    IntegerField,
    Model,
    OneToOneField,
    TextField,
    UUIDField,
)
from encrypted_model_fields.fields import EncryptedCharField

from application.access_control.models import User
from application.core.models import Observation, Product
from application.core.types import Severity, Status
from application.notifications.types import Webhook_Delivery_Status


class Notification(Model):
    TYPE_EXCEPTION = "Exception"
    TYPE_OBSERVATION = "Observation"
    TYPE_OBSERVATION_TITLE = "Observation title"
    TYPE_SECURITY_GATE = "Security gate"
    TYPE_TASK = "Task"

    TYPE_CHOICES = [
        (TYPE_EXCEPTION, TYPE_EXCEPTION),
        (TYPE_OBSERVATION, TYPE_OBSERVATION),
        (TYPE_OBSERVATION_TITLE, TYPE_OBSERVATION_TITLE),
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


class Product_Notification(Model):
    product = ForeignKey(Product, on_delete=CASCADE, null=True, blank=True)
    user = ForeignKey(User, on_delete=CASCADE)
    security_gate_changed = BooleanField(default=False)
    observation_new_changed = BooleanField(default=False)
    observation_to_be_reviewed = BooleanField(default=False)
    assessment_to_be_reviewed = BooleanField(default=False)
    assessment_approval_receipt = BooleanField(default=False)
    product_rule_to_be_reviewed = BooleanField(default=False)
    product_rule_approval_receipt = BooleanField(default=False)

    class Meta:
        unique_together = (
            "product",
            "user",
        )

    def __str__(self) -> str:
        if self.product:
            return f"{self.product} / {self.user}"
        return str(self.user)


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


class Webhook(Model):
    product = ForeignKey(Product, on_delete=CASCADE, null=True)
    name = CharField(max_length=255)
    url = TextField(max_length=2048)
    secret = EncryptedCharField(max_length=255)  # nosemgrep
    # We treat EncryptedCharField as a regular CharField
    event_types = CharField(max_length=512)
    min_severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)
    active = BooleanField(default=True)
    consecutive_failures = IntegerField(default=0)
    # Lease of the running drain, kick delay or endpoint backoff; null when idle
    next_attempt_at = DateTimeField(null=True)
    created = DateTimeField(auto_now_add=True)


class Webhook_Delivery(Model):
    webhook = ForeignKey(Webhook, on_delete=CASCADE, related_name="deliveries")
    event_id = UUIDField()
    event_type = CharField(max_length=64)
    payload = TextField()
    status = CharField(max_length=16, choices=Webhook_Delivery_Status.CHOICES, default=Webhook_Delivery_Status.PENDING)
    attempts = IntegerField(default=0)
    created = DateTimeField(auto_now_add=True)
    last_attempt_at = DateTimeField(null=True)
    response_status_code = IntegerField(null=True)
    error = CharField(max_length=1024, blank=True)

    class Meta:
        indexes = [Index(fields=["webhook", "status"])]
