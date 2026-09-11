from unittest.mock import patch

from django.core.management import call_command
from rest_framework.serializers import ValidationError

from application.access_control.models import User
from application.core.models import Product
from application.rules.api.serializers import (
    ProductRuleSerializer,
    RuleApprovalSerializer,
)
from application.rules.models import Rule
from application.rules.types import Rule_Status
from unittests.base_test_case import BaseTestCase


class TestRuleApprovalSerializer(BaseTestCase):
    """Tests for the validate method of RuleApprovalSerializer"""

    def test_approved_with_rejection_remark_raises(self):
        serializer = RuleApprovalSerializer()
        attrs = {
            "approval_status": Rule_Status.RULE_STATUS_APPROVED,
            "rejection_remark": "This should fail",
        }

        with self.assertRaises(ValidationError) as e:
            serializer.validate(attrs)

        self.assertIn("Remark for rejection cannot be set with approval", str(e.exception))

    def test_approved_without_rejection_remark_valid(self):
        serializer = RuleApprovalSerializer()
        attrs = {
            "approval_status": Rule_Status.RULE_STATUS_APPROVED,
            "rejection_remark": "",
        }

        new_attrs = serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)

    def test_rejected_without_rejection_remark_raises(self):
        serializer = RuleApprovalSerializer()
        attrs = {
            "approval_status": Rule_Status.RULE_STATUS_REJECTED,
            "rejection_remark": "",
        }

        with self.assertRaises(ValidationError) as e:
            serializer.validate(attrs)

        self.assertIn("Rejection needs a remark", str(e.exception))

    def test_rejected_with_rejection_remark_valid(self):
        serializer = RuleApprovalSerializer()
        attrs = {
            "approval_status": Rule_Status.RULE_STATUS_REJECTED,
            "rejection_remark": "This is invalid",
        }

        new_attrs = serializer.validate(attrs)

        self.assertEqual(new_attrs, attrs)


class TestProductRuleSerializerNotification(BaseTestCase):
    """The notification for product rules that need approval is triggered by the serializer."""

    def setUp(self) -> None:
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        self.product = Product.objects.get(pk=1)
        self.product.product_rules_need_approval = True
        self.product.save()

    @patch("application.rules.api.serializers.send_product_rule_approval_notification")
    @patch("application.rules.models.get_current_user")
    def test_create_sends_the_notification(self, mock_user, mock_send) -> None:
        mock_user.return_value = User.objects.get(pk=2)
        serializer = ProductRuleSerializer()

        rule = serializer.create({"product": self.product, "name": "new_rule", "description": "description"})

        self.assertEqual(Rule_Status.RULE_STATUS_NEEDS_APPROVAL, rule.approval_status)
        mock_send.assert_called_once_with(rule)

    @patch("application.rules.api.serializers.send_product_rule_approval_notification")
    @patch("application.rules.models.get_current_user")
    def test_update_sends_the_notification(self, mock_user, mock_send) -> None:
        mock_user.return_value = User.objects.get(pk=2)
        instance = Rule.objects.create(
            product=self.product, name="existing_rule", approval_status=Rule_Status.RULE_STATUS_APPROVED
        )
        serializer = ProductRuleSerializer()

        rule = serializer.update(instance, {"description": "changed"})

        self.assertEqual(Rule_Status.RULE_STATUS_NEEDS_APPROVAL, rule.approval_status)
        mock_send.assert_called_once_with(rule)
