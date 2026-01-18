from typing import Any

from django.db.models import (
    CASCADE,
    PROTECT,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKey,
    Index,
    Model,
    TextField,
)

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.commons.models import Settings
from application.core.models import Product
from application.core.types import Severity, Status, VEX_Justification
from application.rules.types import Rule_Status


class Rule(Model):
    name = CharField(max_length=255)
    description = TextField(max_length=2048, blank=True)
    product = ForeignKey(Product, blank=True, null=True, on_delete=CASCADE)
    parser = ForeignKey("import_observations.Parser", null=True, on_delete=CASCADE)
    scanner_prefix = CharField(max_length=255, blank=True)
    title = CharField(max_length=255, blank=True)
    description_observation = CharField(max_length=255, blank=True)
    origin_component_name_version = CharField(max_length=513, blank=True)
    origin_component_purl = CharField(max_length=255, blank=True)
    origin_docker_image_name_tag = CharField(max_length=513, blank=True)
    origin_endpoint_url = TextField(max_length=2048, blank=True)
    origin_service_name = CharField(max_length=255, blank=True)
    origin_source_file = CharField(max_length=255, blank=True)
    origin_cloud_qualified_resource = CharField(max_length=255, blank=True)
    origin_kubernetes_qualified_resource = CharField(max_length=255, blank=True)
    new_severity = CharField(max_length=12, choices=Severity.SEVERITY_CHOICES, blank=True)
    new_status = CharField(max_length=16, choices=Status.STATUS_CHOICES, blank=True)
    new_vex_justification = CharField(max_length=64, choices=VEX_Justification.VEX_JUSTIFICATION_CHOICES, blank=True)
    enabled = BooleanField(default=True)
    user = ForeignKey(
        User,
        related_name="rule",
        on_delete=PROTECT,
        null=True,
    )
    approval_status = CharField(max_length=16, choices=Rule_Status.RULE_STATUS_CHOICES)
    approval_remark = TextField(max_length=255, blank=True)
    approval_date = DateTimeField(null=True)
    approval_user = ForeignKey(
        User,
        related_name="rule_approver",
        on_delete=PROTECT,
        null=True,
    )

    class Meta:
        unique_together = (
            "product",
            "name",
        )
        indexes = [
            Index(fields=["name"]),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.approval_status:
            self.user = get_current_user()

            self.approval_remark = ""
            self.approval_date = None
            self.approval_user = None

            needs_approval = False
            if not self.product:
                settings = Settings.load()
                needs_approval = settings.feature_general_rules_need_approval
            else:
                if self.product.product_group:
                    product_group_product_rules_needs_approval = self.product.product_group.product_rules_need_approval
                    needs_approval = (
                        self.product.product_rules_need_approval or product_group_product_rules_needs_approval
                    )
                else:
                    needs_approval = self.product.product_rules_need_approval

            if needs_approval:
                self.approval_status = Rule_Status.RULE_STATUS_NEEDS_APPROVAL
            else:
                self.approval_status = Rule_Status.RULE_STATUS_AUTO_APPROVED

        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
