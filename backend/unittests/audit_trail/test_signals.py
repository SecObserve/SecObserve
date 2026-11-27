from unittest.mock import patch
from uuid import uuid4

from django.utils import timezone

from application.access_control.models import Authorization_Group, User
from application.audit_trail.models import Product_Audit_Event
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Branch,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
    Service,
)
from application.import_observations.models import Api_Configuration, Parser
from application.notifications.models import Webhook
from application.rules.models import Rule
from application.scancodeio.models import ScanCodeIO_Project
from unittests.base_test_case import BaseTestCase


class TestAuditTrailSignals(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username="audit_user", first_name="Audit", last_name="User")
        patcher = patch("application.audit_trail.services.audit_trail.get_current_user", return_value=self.user)
        patcher.start()
        self.addCleanup(patcher.stop)
        scancodeio_patcher = patch("application.scancodeio.signals.delete_orphaned_scancodeio_project")
        scancodeio_patcher.start()
        self.addCleanup(scancodeio_patcher.stop)

        self.product = Product.objects.create(name="audit_product")

    def _events(self) -> list[tuple]:
        return list(
            Product_Audit_Event.objects.filter(product_id=self.product.pk)
            .order_by("id")
            .values_list("object_type", "object_name", "action", "changes")
        )

    def test_product_created_and_changed(self) -> None:
        self.product.description = "new description"
        self.product.issue_tracker_api_key = "secret"
        self.product.save()
        # Technical fields only, no event
        self.product.last_observation_change = timezone.now()
        self.product.save()

        self.assertEqual(
            [
                ("Product", "audit_product", "Created", None),
                (
                    "Product",
                    "audit_product",
                    "Changed",
                    {
                        "description": {"old": "", "new": "new description"},
                        "issue_tracker_api_key": {"old": "***", "new": "***"},
                    },
                ),
            ],
            self._events(),
        )
        event = Product_Audit_Event.objects.first()
        self.assertEqual(self.user, event.user)
        self.assertEqual("Audit User", event.user_full_name)

    @patch("application.core.services.security_gate.emit_security_gate_event")
    @patch("application.core.services.security_gate.send_product_security_gate_notification")
    def test_security_gate_recorded_once(self, *_mocks) -> None:
        # The security gate is recalculated and saved while the product is being saved
        self.product.security_gate_active = True
        for severity in ("critical", "high", "medium", "low", "none", "unknown"):
            setattr(self.product, f"security_gate_threshold_{severity}", 0)
        self.product.save()

        self.product.refresh_from_db()
        self.assertTrue(self.product.security_gate_passed)
        self.assertEqual(["Created", "Changed"], [event[2] for event in self._events()])

    def test_branch_lifecycle(self) -> None:
        branch = Branch.objects.create(product=self.product, name="main", is_default_branch=True)
        branch.last_import = timezone.now()
        branch.save()
        branch.name = "develop"
        branch.save()
        branch.delete()

        self.assertEqual(
            [
                ("Product", "audit_product", "Created", None),
                ("Branch", "main", "Created", None),
                ("Product", "audit_product", "Changed", {"repository_default_branch": {"old": None, "new": "main"}}),
                ("Branch", "develop", "Changed", {"name": {"old": "main", "new": "develop"}}),
                ("Branch", "develop", "Deleted", None),
            ],
            self._events(),
        )

    def test_members(self) -> None:
        member = Product_Member.objects.create(product=self.product, user=self.user, role=Roles.Reader)
        member.role = Roles.Owner
        member.save()
        group = Authorization_Group.objects.create(name="audit_group")
        group_member = Product_Authorization_Group_Member.objects.create(
            product=self.product, authorization_group=group, role=Roles.Writer
        )
        # Deletion of the group cascades to the membership
        group.delete()
        member.delete()

        self.assertEqual(
            [
                ("Product member", "audit_user", "Created", None),
                ("Product member", "audit_user", "Changed", {"role": {"old": Roles.Reader, "new": Roles.Owner}}),
                ("Product authorization group member", "audit_group", "Created", None),
                ("Product authorization group member", "audit_group", "Deleted", None),
                ("Product member", "audit_user", "Deleted", None),
            ],
            self._events()[1:],
        )
        self.assertEqual(
            group_member.pk, Product_Audit_Event.objects.get(action="Deleted", object_name="audit_group").object_id
        )

    def test_service_rule_api_configuration_webhook_scancodeio(self) -> None:
        service = Service.objects.create(product=self.product, name="service")
        rule = Rule.objects.create(product=self.product, name="rule", title="title")
        rule.title = "new title"
        rule.save()
        api_configuration = Api_Configuration.objects.create(
            product=self.product, name="api", parser=Parser.objects.create(name="audit_parser"), base_url="https://a"
        )
        api_configuration.api_key = "secret"
        api_configuration.save()
        webhook = Webhook.objects.create(
            product=self.product, name="webhook", url="https://w", secret="secret", event_types="observation.created"
        )
        webhook.consecutive_failures = 3
        webhook.save()
        ScanCodeIO_Project.objects.create(
            product=self.product, project_uuid=uuid4(), project_name="scancode", webhook_token_hash="hash"
        )

        self.assertEqual(
            [
                ("Service", "service", "Created", None),
                ("Product rule", "rule", "Created", None),
                ("Product rule", "rule", "Changed", {"title": {"old": "title", "new": "new title"}}),
                ("API configuration", "api", "Created", None),
                ("API configuration", "api", "Changed", {"api_key": {"old": "***", "new": "***"}}),
                ("Webhook", "webhook", "Created", None),
                ("ScanCode.io project", "scancode", "Created", None),
            ],
            self._events()[1:],
        )
        self.assertIsNotNone(service.pk)

    def test_general_rule_and_global_webhook_not_recorded(self) -> None:
        Rule.objects.create(name="general_rule")
        Webhook.objects.create(name="global", url="https://w", secret="secret", event_types="observation.created")

        self.assertEqual(1, Product_Audit_Event.objects.count())

    def test_branch_deletion_records_cascaded_scancodeio_project(self) -> None:
        branch = Branch.objects.create(product=self.product, name="feature")
        ScanCodeIO_Project.objects.create(
            product=self.product, branch=branch, project_uuid=uuid4(), project_name="scancode", webhook_token_hash="h"
        )
        branch.delete()

        self.assertCountEqual(
            [("ScanCode.io project", "scancode", "Deleted", None), ("Branch", "feature", "Deleted", None)],
            self._events()[-2:],
        )

    def test_product_deletion_records_only_product(self) -> None:
        Branch.objects.create(product=self.product, name="main")
        Service.objects.create(product=self.product, name="service")
        Product_Member.objects.create(product=self.product, user=self.user, role=Roles.Owner)
        Rule.objects.create(product=self.product, name="rule")
        product_id = self.product.pk

        self.product.delete()

        events = Product_Audit_Event.objects.filter(product_id=product_id)
        self.assertEqual(["Product"], list(events.filter(action="Deleted").values_list("object_type", flat=True)))
        self.assertEqual("audit_product", events.get(action="Deleted").product_name)

    def test_product_group_deletion_records_products(self) -> None:
        product_group = Product.objects.create(name="audit_group", is_product_group=True)
        self.product.product_group = product_group
        self.product.save()
        product_group_id = product_group.pk

        product_group.delete()

        self.assertEqual(("Product", "audit_product", "Deleted", None), self._events()[-1])
        self.assertTrue(
            Product_Audit_Event.objects.filter(product_id=product_group_id, object_name="audit_group", action="Deleted")
        )
        self.assertEqual(
            {True},
            set(
                Product_Audit_Event.objects.filter(product_id=product_group_id).values_list(
                    "is_product_group", flat=True
                )
            ),
        )
        self.assertFalse(Product_Audit_Event.objects.filter(product_id=self.product.pk, is_product_group=True))

    def test_assessment_approvers(self) -> None:
        group = Authorization_Group.objects.create(name="approvers")
        self.product.assessment_approvers.add(self.user)
        self.product.assessment_approver_authorization_groups.set([group])
        self.product.assessment_approvers.remove(self.user)

        self.assertEqual(
            [
                ("Product", "audit_product", "Changed", {"assessment_approvers": {"added": ["audit_user"]}}),
                (
                    "Product",
                    "audit_product",
                    "Changed",
                    {"assessment_approver_authorization_groups": {"added": ["approvers"]}},
                ),
                ("Product", "audit_product", "Changed", {"assessment_approvers": {"removed": ["audit_user"]}}),
            ],
            self._events()[1:],
        )
