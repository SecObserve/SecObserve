from unittest.mock import call, patch

from rest_framework.exceptions import ValidationError

from application.rules.models import Rule
from application.rules.services.approval import rule_approval
from application.rules.types import Rule_Status
from unittests.base_test_case import BaseTestCase


class TestRuleEngine(BaseTestCase):
    def test_rule_approval_does_not_need(self):
        rule = Rule(approval_status=Rule_Status.RULE_STATUS_APPROVED)
        with self.assertRaises(ValidationError) as e:
            rule_approval(rule, Rule_Status.RULE_STATUS_APPROVED, "test")

        self.assertEqual(
            str(e.exception),
            "[ErrorDetail(string='Rule does not need approval', code='invalid')]",
        )

    @patch("application.rules.services.approval.get_current_user")
    def test_rule_approval_user(self, get_current_user_mock):
        get_current_user_mock.return_value = self.user_internal
        rule = Rule(
            approval_status=Rule_Status.RULE_STATUS_NEEDS_APPROVAL,
            user=self.user_internal,
        )
        with self.assertRaises(ValidationError) as e:
            rule_approval(rule, Rule_Status.RULE_STATUS_APPROVED, "test")

        self.assertEqual(
            str(e.exception),
            "[ErrorDetail(string='Users cannot approve the rules they created/modified', code='invalid')]",
        )

    @patch("application.rules.services.approval.get_current_user")
    @patch("application.rules.models.Rule.save")
    def test_rule_approval_successful(self, save_mock, get_current_user_mock):
        get_current_user_mock.return_value = self.user_external
        rule = Rule(
            approval_status=Rule_Status.RULE_STATUS_NEEDS_APPROVAL,
            user=self.user_internal,
        )

        rule_approval(rule, Rule_Status.RULE_STATUS_REJECTED, "test")

        self.assertEqual(rule.approval_status, Rule_Status.RULE_STATUS_REJECTED)
        self.assertEqual(rule.approval_user, self.user_external)
        self.assertEqual(rule.rejection_remark, "test")
        self.assertIsNotNone(rule.approval_date)
        save_mock.assert_called_once()
