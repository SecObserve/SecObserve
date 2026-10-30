from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    Model,
    OneToOneField,
    UUIDField,
)

from application.core.models import Product


class ScanCodeIO_Project(Model):
    product = OneToOneField(Product, on_delete=CASCADE, related_name="scancodeio_project")
    project_uuid = UUIDField()
    project_name = CharField(max_length=255)
    created = DateTimeField(auto_now_add=True)
    # SHA-256 of the token in the webhook URL
    webhook_token_hash = CharField(max_length=64, unique=True)

    def __str__(self) -> str:
        return self.project_name
