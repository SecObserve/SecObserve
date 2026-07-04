from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
    User,
)
from application.authorization.services.roles_permissions import Roles
from application.core.models import Observation_Log, Product, Product_Authorization_Group_Member, Product_Member
from application.core.services.assessment import (
    assessment_approval,
    assessment_approvers_configured,
    get_effective_assessment_approvers,
    is_user_designated_assessment_approver,
    user_is_allowed_assessment_approver,
)
from application.core.services.observations_bulk_actions import (
    observation_logs_bulk_approval,
)
from application.core.types import Assessment_Status
from unittests.base_test_case import BaseTestCase


class TestAssessmentApproverResolution(TestCase):
    """Unit tests for the designated-approver resolution and membership check."""

    def setUp(self) -> None:
        self.approver = User.objects.create(username="approver@example.com")
        self.other = User.objects.create(username="other@example.com")
        self.group_user = User.objects.create(username="group_user@example.com")

        self.group = Authorization_Group.objects.create(name="security_team")
        Authorization_Group_Member.objects.create(authorization_group=self.group, user=self.group_user)

        self.product_group = Product.objects.create(name="pg", is_product_group=True)
        self.product = Product.objects.create(name="p", product_group=self.product_group)
        Product_Member.objects.create(product=self.product, user=self.approver, role=Roles.Writer)
        Product_Member.objects.create(product=self.product, user=self.other, role=Roles.Writer)
        Product_Authorization_Group_Member.objects.create(
            product=self.product, authorization_group=self.group, role=Roles.Writer
        )
        Product_Authorization_Group_Member.objects.create(
            product=self.product_group, authorization_group=self.group, role=Roles.Writer
        )

    def test_no_approvers_configured_allows_anyone(self) -> None:
        self.assertTrue(user_is_allowed_assessment_approver(self.product, self.other))

    def test_direct_approver_user(self) -> None:
        self.product.assessment_approvers.add(self.approver)
        self.assertTrue(user_is_allowed_assessment_approver(self.product, self.approver))
        self.assertFalse(user_is_allowed_assessment_approver(self.product, self.other))

    def test_approver_via_authorization_group(self) -> None:
        self.product.assessment_approver_authorization_groups.add(self.group)
        self.assertTrue(user_is_allowed_assessment_approver(self.product, self.group_user))
        self.assertFalse(user_is_allowed_assessment_approver(self.product, self.other))

    def test_inheritance_is_union_of_product_and_group(self) -> None:
        self.product_group.assessment_approvers.add(self.approver)
        self.product.assessment_approvers.add(self.other)

        user_ids, group_ids = get_effective_assessment_approvers(self.product)
        self.assertEqual(user_ids, {self.approver.pk, self.other.pk})
        self.assertEqual(group_ids, set())

        # approver inherited from the product group, other configured on the product
        self.assertTrue(user_is_allowed_assessment_approver(self.product, self.approver))
        self.assertTrue(user_is_allowed_assessment_approver(self.product, self.other))

    def test_inherited_group_membership(self) -> None:
        self.product_group.assessment_approver_authorization_groups.add(self.group)
        self.assertTrue(user_is_allowed_assessment_approver(self.product, self.group_user))
        self.assertFalse(user_is_allowed_assessment_approver(self.product, self.other))

    def test_reader_authorization_group_does_not_count_as_designated_approver(self) -> None:
        reader_group = Authorization_Group.objects.create(name="reader_team")
        Authorization_Group_Member.objects.create(authorization_group=reader_group, user=self.group_user)
        Product_Authorization_Group_Member.objects.create(
            product=self.product, authorization_group=reader_group, role=Roles.Reader
        )
        self.product.assessment_approver_authorization_groups.add(reader_group)

        self.assertFalse(user_is_allowed_assessment_approver(self.product, self.group_user))


class TestDesignatedAssessmentApprover(TestCase):
    """Strict designated-approver check used to grant the assessment permission."""

    def setUp(self) -> None:
        self.approver = User.objects.create(username="designated@example.com")
        self.other = User.objects.create(username="not_designated@example.com")
        self.group_user = User.objects.create(username="group_member@example.com")

        self.group = Authorization_Group.objects.create(name="approver_team")
        Authorization_Group_Member.objects.create(authorization_group=self.group, user=self.group_user)

        self.product_group = Product.objects.create(name="pg2", is_product_group=True)
        self.product = Product.objects.create(name="p2", product_group=self.product_group)
        Product_Authorization_Group_Member.objects.create(
            product=self.product, authorization_group=self.group, role=Roles.Writer
        )
        Product_Authorization_Group_Member.objects.create(
            product=self.product_group, authorization_group=self.group, role=Roles.Writer
        )

    def test_no_approvers_configured_denies_everyone(self) -> None:
        # Unlike user_is_allowed_assessment_approver, the strict check returns False when empty.
        self.assertFalse(is_user_designated_assessment_approver(self.product, self.other))

    def test_direct_designated_user(self) -> None:
        self.product.assessment_approvers.add(self.approver)
        self.assertTrue(is_user_designated_assessment_approver(self.product, self.approver))
        self.assertFalse(is_user_designated_assessment_approver(self.product, self.other))

    def test_designated_via_authorization_group(self) -> None:
        self.product.assessment_approver_authorization_groups.add(self.group)
        self.assertTrue(is_user_designated_assessment_approver(self.product, self.group_user))
        self.assertFalse(is_user_designated_assessment_approver(self.product, self.other))

    def test_designated_inherited_from_product_group(self) -> None:
        self.product_group.assessment_approvers.add(self.approver)
        self.assertTrue(is_user_designated_assessment_approver(self.product, self.approver))
        self.assertFalse(is_user_designated_assessment_approver(self.product, self.other))

    def test_approvers_configured_false_when_empty(self) -> None:
        self.assertFalse(assessment_approvers_configured(self.product))

    def test_approvers_configured_true_with_direct_user(self) -> None:
        self.product.assessment_approvers.add(self.approver)
        self.assertTrue(assessment_approvers_configured(self.product))

    def test_approvers_configured_true_with_group(self) -> None:
        self.product.assessment_approver_authorization_groups.add(self.group)
        self.assertTrue(assessment_approvers_configured(self.product))

    def test_approvers_configured_true_inherited_from_product_group(self) -> None:
        self.product_group.assessment_approvers.add(self.approver)
        self.assertTrue(assessment_approvers_configured(self.product))


class TestAssessmentApprovalEnforcement(BaseTestCase):
    """Enforcement of the designated-approver restriction in the approval services."""

    def setUp(self) -> None:
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        # Observation log 1 belongs to observation 1 / product 1, authored by user 2.
        self.log = Observation_Log.objects.get(pk=1)
        self.log.assessment_status = Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL
        self.log.save()
        self.product = Product.objects.get(pk=1)
        self.author = User.objects.get(pk=2)
        self.outsider = User.objects.get(pk=3)
        self.approver = User.objects.create(username="assessment_writer@example.com")
        Product_Member.objects.create(product=self.product, user=self.approver, role=Roles.Writer)
        self.owner = User.objects.create(username="assessment_owner@example.com")
        Product_Member.objects.create(product=self.product, user=self.owner, role=Roles.Owner)

    @patch("application.core.services.assessment.get_current_user")
    def test_empty_configuration_allows_any_non_author(self, mock_user) -> None:
        mock_user.return_value = self.outsider
        assessment_approval(self.log, Assessment_Status.ASSESSMENT_STATUS_REJECTED, "ok")
        self.log.refresh_from_db()
        self.assertEqual(self.log.assessment_status, Assessment_Status.ASSESSMENT_STATUS_REJECTED)
        self.assertEqual(self.log.approval_user, self.outsider)

    @patch("application.core.services.assessment.get_current_user")
    def test_designated_approver_can_approve(self, mock_user) -> None:
        self.product.assessment_approvers.add(self.approver)
        mock_user.return_value = self.approver
        assessment_approval(self.log, Assessment_Status.ASSESSMENT_STATUS_REJECTED, "ok")
        self.log.refresh_from_db()
        self.assertEqual(self.log.approval_user, self.approver)

    @patch("application.core.services.assessment.get_current_user")
    def test_non_approver_is_rejected_when_configured(self, mock_user) -> None:
        self.product.assessment_approvers.add(self.approver)
        mock_user.return_value = self.outsider
        with self.assertRaises(ValidationError):
            assessment_approval(self.log, Assessment_Status.ASSESSMENT_STATUS_REJECTED, "ok")
        self.log.refresh_from_db()
        self.assertEqual(self.log.assessment_status, Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL)

    @patch("application.core.services.assessment.get_current_user")
    def test_owner_can_approve_other_users_assessments_when_not_designated(self, mock_user) -> None:
        self.product.assessment_approvers.add(self.approver)
        mock_user.return_value = self.owner
        assessment_approval(self.log, Assessment_Status.ASSESSMENT_STATUS_REJECTED, "ok")
        self.log.refresh_from_db()
        self.assertEqual(self.log.approval_user, self.owner)

    @patch("application.core.services.assessment.get_current_user")
    def test_self_approval_blocked_even_if_designated_approver(self, mock_user) -> None:
        self.product.assessment_approvers.add(self.author)
        mock_user.return_value = self.author
        with self.assertRaises(ValidationError):
            assessment_approval(self.log, Assessment_Status.ASSESSMENT_STATUS_REJECTED, "ok")

    @patch("application.core.services.observations_bulk_actions.user_has_permission", return_value=True)
    @patch("application.core.services.observations_bulk_actions.get_current_user")
    @patch("application.core.services.assessment.get_current_user")
    def test_bulk_approval_blocked_for_non_approver(self, mock_user_assessment, mock_user_bulk, _mock_perm) -> None:
        self.product.assessment_approvers.add(self.approver)
        mock_user_assessment.return_value = self.outsider
        mock_user_bulk.return_value = self.outsider
        with self.assertRaises(ValidationError):
            observation_logs_bulk_approval(Assessment_Status.ASSESSMENT_STATUS_REJECTED, "ok", [self.log.pk])
        self.log.refresh_from_db()
        self.assertEqual(self.log.assessment_status, Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL)
