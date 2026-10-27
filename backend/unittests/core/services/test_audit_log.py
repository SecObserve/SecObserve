from unittest.mock import patch

from django.core.management import call_command

from application.access_control.models import Authorization_Group, User
from application.core.api.serializers_product import (
    ProductGroupSerializer,
    ProductSerializer,
)
from application.core.models import Audit_Log, Product
from application.core.types import Audit_Log_Action
from unittests.base_test_case import BaseTestCase


class TestAuditLog(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.actor = User.objects.get(username="db_internal_write")
        patcher = patch("application.core.services.audit_log.get_current_user", return_value=self.actor)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.product = Product.objects.get(name="db_product_internal")
        self.approver = User.objects.get(username="db_internal_read")
        self.group = Authorization_Group.objects.get(name="non_oidc_group")

    def _entries(self, action):
        return list(Audit_Log.objects.filter(action=action).order_by("id"))

    def test_assessments_need_approval_switched(self):
        serializer = ProductSerializer(self.product, data={"assessments_need_approval": True}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = ProductSerializer(self.product, data={"description": "unrelated"}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        entries = self._entries(Audit_Log_Action.AUDIT_LOG_ACTION_ASSESSMENTS_NEED_APPROVAL)
        self.assertEqual(1, len(entries))
        self.assertEqual(self.product, entries[0].product)
        self.assertEqual(self.actor, entries[0].user)
        self.assertEqual(self.actor.full_name, entries[0].user_name)
        self.assertEqual(("False", "True"), (entries[0].old_value, entries[0].new_value))

    def test_assessments_need_approval_switched_product_group(self):
        product_group = Product.objects.get(name="db_product_group")
        product_group.assessments_need_approval = True
        product_group.save()

        serializer = ProductGroupSerializer(product_group, data={"assessments_need_approval": False}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        entries = self._entries(Audit_Log_Action.AUDIT_LOG_ACTION_ASSESSMENTS_NEED_APPROVAL)
        self.assertEqual(1, len(entries))
        self.assertEqual(product_group, entries[0].product)
        self.assertEqual(("True", "False"), (entries[0].old_value, entries[0].new_value))

    def test_approver_added_and_removed_from_both_sides(self):
        self.product.assessment_approvers.add(self.approver)
        self.approver.assessment_approver_for_products.remove(self.product)

        added = self._entries(Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_ADDED)
        removed = self._entries(Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_REMOVED)
        self.assertEqual(1, len(added))
        self.assertEqual(1, len(removed))
        for entry in added + removed:
            self.assertEqual(self.product, entry.product)
            self.assertEqual(self.approver.full_name, entry.target)

    def test_approvers_set_logs_each_change_once(self):
        other_approver = User.objects.get(username="db_external")
        self.product.assessment_approvers.add(self.approver)

        self.product.assessment_approvers.set([other_approver])

        added = self._entries(Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_ADDED)
        removed = self._entries(Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_REMOVED)
        self.assertEqual([self.approver.full_name, other_approver.full_name], [entry.target for entry in added])
        self.assertEqual([self.approver.full_name], [entry.target for entry in removed])

    def test_approver_group_added_and_removed(self):
        self.product.assessment_approver_authorization_groups.add(self.group)
        self.product.assessment_approver_authorization_groups.remove(self.group)

        entries = list(Audit_Log.objects.order_by("id"))
        self.assertEqual(
            [
                Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_GROUP_ADDED,
                Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_GROUP_REMOVED,
            ],
            [entry.action for entry in entries],
        )
        for entry in entries:
            self.assertEqual(self.group, entry.authorization_group)
            self.assertEqual(self.group.name, entry.target)

    def test_deleted_approver_and_group_are_logged_and_kept(self):
        self.product.assessment_approvers.add(self.approver)
        self.product.assessment_approver_authorization_groups.add(self.group)

        self.approver.delete()
        self.group.delete()

        removed = self._entries(Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_REMOVED)
        self.assertEqual(["db_internal_read"], [entry.target for entry in removed])
        group_entries = list(Audit_Log.objects.exclude(authorization_group_name="").order_by("id"))
        self.assertEqual(
            [
                Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_GROUP_ADDED,
                Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_GROUP_REMOVED,
            ],
            [entry.action for entry in group_entries],
        )
        for entry in group_entries:
            self.assertIsNone(entry.authorization_group)
            self.assertEqual("non_oidc_group", entry.authorization_group_name)

    def test_deleted_product_keeps_its_entries(self):
        self.product.assessment_approvers.add(self.approver)

        self.product.delete()

        entries = list(Audit_Log.objects.all())
        self.assertEqual(1, len(entries))
        self.assertIsNone(entries[0].product)
        self.assertEqual("db_product_internal", entries[0].product_name)
