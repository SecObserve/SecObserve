from datetime import datetime, timezone
from importlib import import_module

from django.apps import apps
from django.core.management import call_command

from application.audit_trail.models import Product_Audit_Event
from application.core.models import Observation_Log
from application.rules.models import Rule
from unittests.base_test_case import BaseTestCase

backfill_approvals = import_module("application.audit_trail.migrations.0002_backfill_approvals").backfill_approvals

APPROVAL_DATE_1 = datetime(2025, 3, 1, 10, 0, tzinfo=timezone.utc)
APPROVAL_DATE_2 = datetime(2025, 3, 2, 10, 0, tzinfo=timezone.utc)


class TestBackfillApprovals(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        # Queryset updates, so that no audit events are created by the signals
        Observation_Log.objects.filter(pk=1).update(
            assessment_status="Approved", approval_date=APPROVAL_DATE_1, approval_user_id=1
        )
        Observation_Log.objects.filter(pk=3).update(
            assessment_status="Rejected", approval_date=APPROVAL_DATE_2, approval_user_id=1, rejection_remark="not ok"
        )
        Observation_Log.objects.filter(pk=4).update(assessment_status="Needs approval", approval_date=APPROVAL_DATE_1)
        Rule.objects.filter(pk=1).update(approval_status="Approved", approval_date=APPROVAL_DATE_1, approval_user_id=1)
        # General rule
        Rule.objects.filter(pk=3).update(approval_status="Approved", approval_date=APPROVAL_DATE_1, approval_user_id=1)
        Product_Audit_Event.objects.all().delete()

    def test_backfill_approvals(self) -> None:
        backfill_approvals(apps, None)

        self.assertEqual(
            [
                (1, "Assessment", 1, "db_observation_internal", "Approved", None, APPROVAL_DATE_1),
                (
                    2,
                    "Assessment",
                    2,
                    "db_observation_internal",
                    "Rejected",
                    {"rejection_remark": {"old": "", "new": "not ok"}},
                    APPROVAL_DATE_2,
                ),
                (1, "Product rule", 1, "db_product_rule_internal", "Approved", None, APPROVAL_DATE_1),
            ],
            list(
                Product_Audit_Event.objects.order_by("id").values_list(
                    "product_id", "object_type", "object_id", "object_name", "action", "changes", "created"
                )
            ),
        )
        event = Product_Audit_Event.objects.first()
        self.assertEqual(1, event.user_id)
        self.assertEqual("db_admin", event.user_full_name)
        self.assertEqual("db_product_internal", event.product_name)
        self.assertFalse(event.is_product_group)
