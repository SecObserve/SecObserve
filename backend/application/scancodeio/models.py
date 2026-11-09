from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    ForeignKey,
    Model,
    UUIDField,
)

from application.core.models import Branch, Product, Service


class ScanCodeIO_Project(Model):
    product = ForeignKey(Product, on_delete=CASCADE, related_name="scancodeio_projects")
    branch = ForeignKey(Branch, on_delete=CASCADE, null=True, blank=True, related_name="scancodeio_projects")
    service = ForeignKey(Service, on_delete=CASCADE, null=True, blank=True, related_name="scancodeio_projects")
    project_uuid = UUIDField()
    project_name = CharField(max_length=255)
    created = DateTimeField(auto_now_add=True)
    # SHA-256 of the token in the webhook URL
    webhook_token_hash = CharField(max_length=64, unique=True)

    class Meta:
        # Doesn't apply to an empty branch or service, see create_scancodeio_project()
        unique_together = (
            "product",
            "branch",
            "service",
        )

    def __str__(self) -> str:
        return self.project_name
