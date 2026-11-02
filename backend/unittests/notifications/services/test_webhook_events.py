import json
from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import patch

from django.db import transaction

from application.core.models import Product
from application.core.types import Severity, Status
from application.notifications.models import Webhook, Webhook_Delivery
from application.notifications.services.webhook_events import (
    build_webhook_payload,
    emit_assessment_event,
    emit_import_event,
    emit_observation_event,
    emit_rule_event,
    emit_security_gate_event,
)
from application.notifications.types import Webhook_Event_Type
from application.rules.types import Rule_Status
from unittests.base_test_case import BaseTestCase

NOW = datetime(2026, 11, 2, 12, 0, tzinfo=dt_timezone.utc)
BASE = "https://so.example/"
OBSERVATION_CREATED = Webhook_Event_Type.OBSERVATION_CREATED


class TestWebhookEvents(BaseTestCase):
    def setUp(self):
        super().setUp()
        for name, value in (("timezone.now", NOW), ("get_base_url_frontend", BASE)):
            patcher = patch(f"application.notifications.services.webhook_events.{name}", return_value=value)
            self.addCleanup(patcher.stop)
            patcher.start()
        patcher = patch("application.notifications.services.webhook_events.kick_webhooks")
        self.addCleanup(patcher.stop)
        self.mock_kick = patcher.start()

        self.product_group_1.is_product_group = True
        self.product_group_1.save()
        self.product_1.repository_default_branch = None
        self.product_1.product_group = self.product_group_1
        self.product_1.save()
        self.product_other = Product.objects.create(name="product_other")
        self.group_other = Product.objects.create(name="group_other", is_product_group=True)

        self.branch_1.save()
        self.observation_1.id = 1
        self.observation_1.current_severity = Severity.SEVERITY_HIGH
        self.observation_1.numerical_severity = 2
        self.observation_1.current_status = Status.STATUS_OPEN
        self.observation_1.vulnerability_id = "CVE-2026-0001"
        self.observation_1.origin_component_name_version = "pkg:1.0"
        self.observation_1.scanner = "scanner_1"
        self.observation_log_1.id = 1
        self.observation_log_1.assessment_status = Rule_Status.RULE_STATUS_NEEDS_APPROVAL
        self.user_internal.save()
        self.product_rule_1.id = 1
        self.product_rule_1.user = self.user_internal
        self.product_rule_1.approval_status = Rule_Status.RULE_STATUS_NEEDS_APPROVAL

        self.product = {
            "id": self.product_1.pk,
            "name": "product_1",
            "product_group": "product_group_1",
            "security_gate_passed": None,
            "url": f"{BASE}#/products/{self.product_1.pk}/show",
        }

    def _webhook(self, product=None, **kwargs) -> Webhook:
        kwargs.setdefault("event_types", OBSERVATION_CREATED)
        return Webhook.objects.create(
            name="w", url="https://example.com/h", secret="whsec_c2VjcmV0", product=product, **kwargs
        )

    def _emit(self):
        emit_observation_event(OBSERVATION_CREATED, self.observation_1)

    def _delivery(self) -> Webhook_Delivery:
        return Webhook_Delivery.objects.get()

    def test_no_active_webhook_one_query(self):
        with self.assertNumQueries(1):
            with self.captureOnCommitCallbacks(execute=True):
                self._emit()
        self.assertEqual(0, Webhook_Delivery.objects.count())
        self.mock_kick.assert_not_called()

    def test_subscribed_webhook_gets_pending_delivery(self):
        self._webhook()
        self._emit()
        delivery = self._delivery()
        self.assertEqual("Pending", delivery.status)
        self.assertEqual(OBSERVATION_CREATED, delivery.event_type)
        self.assertEqual(
            {
                "type": "observation.created",
                "timestamp": NOW.isoformat(),
                "data": {
                    "product": self.product,
                    "observation": {
                        "id": 1,
                        "title": "observation_1",
                        "severity": "High",
                        "status": "Open",
                        "priority": None,
                        "vulnerability_id": "CVE-2026-0001",
                        "component": "pkg:1.0",
                        "branch": "branch_1",
                        "service": None,
                        "scanner": "scanner_1",
                        "url": f"{BASE}#/observations/1/show",
                    },
                },
            },
            json.loads(delivery.payload),
        )

    def test_kick_after_commit(self):
        webhook = self._webhook()
        with self.captureOnCommitCallbacks(execute=True):
            self._emit()
        self.mock_kick.assert_called_once_with([webhook.pk])

    def test_rollback_discards_delivery_and_kick(self):
        self._webhook()
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    self._emit()
                    raise RuntimeError()
            except RuntimeError:
                pass
        self.assertEqual(0, Webhook_Delivery.objects.count())
        self.mock_kick.assert_not_called()

    def test_unsubscribed_type(self):
        self._webhook(event_types=Webhook_Event_Type.IMPORT_COMPLETED)
        self._emit()
        self.assertEqual(0, Webhook_Delivery.objects.count())

    def test_inactive_webhook(self):
        self._webhook(active=False)
        self._emit()
        self.assertEqual(0, Webhook_Delivery.objects.count())

    def test_min_severity(self):
        self._webhook(min_severity=Severity.SEVERITY_HIGH)
        self.observation_1.numerical_severity = 3
        self._emit()
        self.assertEqual(0, Webhook_Delivery.objects.count())
        self.observation_1.numerical_severity = 1
        self._emit()
        self.assertEqual(1, Webhook_Delivery.objects.count())

    def test_min_severity_ignored_for_import(self):
        self._webhook(min_severity=Severity.SEVERITY_CRITICAL, event_types=Webhook_Event_Type.IMPORT_COMPLETED)
        self._import()
        self.assertEqual(1, Webhook_Delivery.objects.count())

    def test_scope_matching(self):
        webhooks = [
            self._webhook(),
            self._webhook(self.product_group_1),
            self._webhook(self.product_1),
            self._webhook(self.product_other),
            self._webhook(self.group_other),
        ]
        self._emit()
        self.assertEqual(
            sorted(w.pk for w in webhooks[:3]),
            sorted(Webhook_Delivery.objects.values_list("webhook_id", flat=True)),
        )

    def test_general_rule_only_global(self):
        self._webhook(event_types=Webhook_Event_Type.RULE_APPROVAL_REQUESTED)
        self._webhook(self.product_1, event_types=Webhook_Event_Type.RULE_APPROVAL_REQUESTED)
        self.product_rule_1.product = None
        emit_rule_event(Webhook_Event_Type.RULE_APPROVAL_REQUESTED, self.product_rule_1)
        self.assertEqual(
            {
                "type": "rule.approval_requested",
                "timestamp": NOW.isoformat(),
                "data": {
                    "product": None,
                    "rule": {
                        "id": 1,
                        "name": "rule_1",
                        "scope": "general",
                        "user": "user_internal@example.com",
                        "approval_status": "Needs approval",
                        "approval_user": None,
                        "rejection_remark": "",
                        "url": f"{BASE}#/general_rules/1/show",
                    },
                },
            },
            json.loads(self._delivery().payload),
        )

    def test_product_rule(self):
        self._webhook(event_types=Webhook_Event_Type.RULE_APPROVAL_DECIDED)
        emit_rule_event(Webhook_Event_Type.RULE_APPROVAL_DECIDED, self.product_rule_1)
        self.assertEqual(
            {
                "product": self.product,
                "rule": {
                    "id": 1,
                    "name": "rule_1",
                    "scope": "product",
                    "user": "user_internal@example.com",
                    "approval_status": "Needs approval",
                    "approval_user": None,
                    "rejection_remark": "",
                    "url": f"{BASE}#/product_rules/1/show",
                },
            },
            json.loads(self._delivery().payload)["data"],
        )

    def test_assessment(self):
        self._webhook(event_types=Webhook_Event_Type.ASSESSMENT_APPROVAL_REQUESTED, min_severity="High")
        emit_assessment_event(Webhook_Event_Type.ASSESSMENT_APPROVAL_REQUESTED, self.observation_log_1)
        data = json.loads(self._delivery().payload)["data"]
        self.assertEqual(["assessment", "observation", "product"], sorted(data))
        self.assertEqual(
            {
                "id": 1,
                "user": "user_internal@example.com",
                "severity": "Critical",
                "status": "Duplicate",
                "priority": None,
                "comment": "comment",
                "assessment_status": "Needs approval",
                "approval_user": None,
                "rejection_remark": "",
                "url": f"{BASE}#/observation_logs/1/show",
            },
            data["assessment"],
        )

    def _import(self):
        emit_import_event(
            product=self.product_1,
            branch=self.branch_1,
            service=None,
            parser_name="parser_1",
            filename="f.json",
            api_configuration_name="",
            numbers=(2, 5, 1),
        )

    def test_import(self):
        self._webhook(event_types=Webhook_Event_Type.IMPORT_COMPLETED)
        self._import()
        self.assertEqual(
            {
                "product": self.product,
                "import": {
                    "parser": "parser_1",
                    "branch": "branch_1",
                    "service": None,
                    "filename": "f.json",
                    "api_configuration": "",
                    "observations_new": 2,
                    "observations_updated": 5,
                    "observations_resolved": 1,
                },
            },
            json.loads(self._delivery().payload)["data"],
        )

    def test_security_gate(self):
        self._webhook(event_types=Webhook_Event_Type.SECURITY_GATE_CHANGED)
        self.product_1.security_gate_passed = False
        emit_security_gate_event(self.product_1)
        self.assertEqual(
            {"product": {**self.product, "security_gate_passed": False}},
            json.loads(self._delivery().payload)["data"],
        )

    def test_same_event_id_for_all_webhooks(self):
        self._webhook()
        self._webhook(self.product_1)
        self._emit()
        self.assertEqual(2, Webhook_Delivery.objects.count())
        self.assertEqual(1, Webhook_Delivery.objects.values("event_id").distinct().count())

    def test_untrusted_title_round_trips(self):
        self._webhook()
        self.observation_1.title = 'x "q"   <b>'
        self._emit()
        self.assertEqual('x "q"   <b>', json.loads(self._delivery().payload)["data"]["observation"]["title"])

    def test_build_webhook_payload(self):
        self.assertEqual(
            {"type": "webhook.test", "timestamp": NOW.isoformat(), "data": {"a": 1}},
            json.loads(build_webhook_payload("webhook.test", {"a": 1})),
        )
