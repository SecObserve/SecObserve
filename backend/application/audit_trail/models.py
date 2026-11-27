from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import (
    DO_NOTHING,
    SET_NULL,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    Index,
    IntegerField,
    JSONField,
    Model,
)
from django.utils import timezone

from application.access_control.models import User
from application.audit_trail.types import Audit_Object_Type


class Product_Audit_Event(Model):
    # No DB constraint, the events must outlive the product. No own index, Meta.indexes starts with the product.
    product = ForeignKey("core.Product", on_delete=DO_NOTHING, db_constraint=False, db_index=False, related_name="+")
    product_name = CharField(max_length=255)
    # Kept for deleted products, is_product_group of a product never changes
    is_product_group = BooleanField(default=False)
    created = DateTimeField(default=timezone.now)
    # API token users are deleted when the token is revoked, the full name is kept
    user = ForeignKey(User, on_delete=SET_NULL, null=True, related_name="+")
    user_full_name = CharField(max_length=301, blank=True)
    object_type = CharField(max_length=40, choices=Audit_Object_Type.OBJECT_TYPE_CHOICES)
    object_id = IntegerField()
    object_name = CharField(max_length=513)
    action = CharField(max_length=20)
    changes = JSONField(null=True, encoder=DjangoJSONEncoder)

    class Meta:
        indexes = [
            Index(fields=["product", "-created"]),
            Index(fields=["-created"]),
        ]

    def __str__(self) -> str:
        return f"{self.product_name} / {self.object_type} {self.object_name} / {self.action}"
