from rest_framework.serializers import ValidationError

from application.rules.api.serializers import RuleApprovalSerializer
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
