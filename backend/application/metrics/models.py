from typing import Any

from django.db.models import (
    CASCADE,
    DateField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    Model,
)
from django.utils import timezone

from application.core.models import Product


class Product_Metrics(Model):
    product = ForeignKey(Product, on_delete=CASCADE)
    date = DateField()

    active_critical = IntegerField(default=0)
    active_high = IntegerField(default=0)
    active_medium = IntegerField(default=0)
    active_low = IntegerField(default=0)
    active_none = IntegerField(default=0)
    active_unknown = IntegerField(default=0)

    open = IntegerField(default=0)
    affected = IntegerField(default=0)
    resolved = IntegerField(default=0)
    duplicate = IntegerField(default=0)
    false_positive = IntegerField(default=0)
    in_review = IntegerField(default=0)
    not_affected = IntegerField(default=0)
    not_security = IntegerField(default=0)
    risk_accepted = IntegerField(default=0)

    class Meta:
        unique_together = (
            "product",
            "date",
        )


class Product_License_Metrics(Model):
    product = ForeignKey(Product, on_delete=CASCADE)
    date = DateField()

    allowed = IntegerField(default=0)
    forbidden = IntegerField(default=0)
    ignored = IntegerField(default=0)
    review_required = IntegerField(default=0)
    unknown = IntegerField(default=0)

    class Meta:
        unique_together = (
            "product",
            "date",
        )


class Product_Metrics_Status(Model):
    last_calculated = DateTimeField(default=timezone.now)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        return 0, {}

    @classmethod
    def load(cls) -> "Product_Metrics_Status":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
