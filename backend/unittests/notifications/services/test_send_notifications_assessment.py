import json
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
    User,
)
from application.authorization.services.roles_permissions import Roles
from application.commons.models import Settings
from application.core.models import (
    Observation,
    Observation_Log,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.core.types import Assessment_Status, Severity, Status
from application.import_observations.models import Parser
from application.notifications.models import Notification, Notification_Recipient
from application.notifications.services.send_notifications_assessment import (
    get_eligible_assessment_approval_recipients,
    send_assessment_approval_request_notification,
    send_assessment_approval_result_notification,
)
from application.notifications.services.send_notifications_base import (
    _create_notification_message,
)

MODULE = "application.notifications.services.send_notifications_assessment"


class TestAssessmentApprovalNotifications(TestCase):
    def setUp(self) -> None:
        with patch("application.core.signals.get_current_user", return_value=None):
            self.product_group = Product.objects.create(name="approval-group", is_product_group=True)
            self.product = Product.objects.create(name="approval-product", product_group=self.product_group)
        self.author = self._create_product_user("author@example.com", Roles.Writer)
        self.approver = self._create_product_user("approver@example.com", Roles.Writer, email="approver@example.com")
        parser = Parser.objects.create(name="assessment-notification-parser")
        self.observation = Observation.objects.create(
            product=self.product,
            parser=parser,
            title="CVE-2026-0001",
            current_severity=Severity.SEVERITY_HIGH,
            current_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )
        self.observation_log = Observation_Log.objects.create(
            observation=self.observation,
            user=self.author,
            severity=Severity.SEVERITY_CRITICAL,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL,
            comment="Raise severity",
        )

    def _create_product_user(
        self,
        username: str,
        role: Roles,
        *,
        email: str = "",
        is_active: bool = True,
    ) -> User:
        user = User.objects.create(username=username, email=email, is_active=is_active)
        Product_Member.objects.create(product=self.product, user=user, role=role)
        return user

    @patch(f"{MODULE}._send_assessment_approval_notifications")
    def test_resolves_direct_group_inherited_and_deduplicated_recipients(self, mock_send: MagicMock) -> None:
        group_user = self._create_product_user("group@example.com", Roles.Reader)
        duplicate_user = self._create_product_user("duplicate@example.com", Roles.Writer)
        inherited_user = User.objects.create(username="inherited@example.com")
        inactive_user = self._create_product_user("inactive@example.com", Roles.Writer, is_active=False)
        reader = self._create_product_user("reader@example.com", Roles.Reader)

        product_group = Authorization_Group.objects.create(name="product-approvers")
        for user in (group_user, duplicate_user):
            Authorization_Group_Member.objects.create(authorization_group=product_group, user=user)
        Product_Authorization_Group_Member.objects.create(
            product=self.product,
            authorization_group=product_group,
            role=Roles.Writer,
        )

        inherited_group = Authorization_Group.objects.create(name="inherited-approvers")
        Authorization_Group_Member.objects.create(authorization_group=inherited_group, user=inherited_user)
        Product_Authorization_Group_Member.objects.create(
            product=self.product_group,
            authorization_group=inherited_group,
            role=Roles.Writer,
        )

        self.product.assessment_approvers.add(
            self.author,
            self.approver,
            duplicate_user,
            inactive_user,
            reader,
        )
        self.product.assessment_approver_authorization_groups.add(product_group)
        self.product_group.assessment_approver_authorization_groups.add(inherited_group)

        recipients = get_eligible_assessment_approval_recipients(self.observation_log)

        self.assertEqual(
            {self.approver.pk, group_user.pk, duplicate_user.pk, inherited_user.pk},
            {recipient.pk for recipient in recipients},
        )

        notification = send_assessment_approval_request_notification(self.observation_log)
        self.assertIsNotNone(notification)
        self.assertEqual(4, Notification_Recipient.objects.filter(notification=notification).count())
        mock_send.assert_called_once()

    @patch(f"{MODULE}._send_assessment_approval_notifications")
    def test_request_creation_is_idempotent(self, mock_send: MagicMock) -> None:
        self.product.assessment_approvers.add(self.approver)

        first = send_assessment_approval_request_notification(self.observation_log)
        second = send_assessment_approval_request_notification(self.observation_log)

        self.assertEqual(first, second)
        self.assertEqual(
            1,
            Notification.objects.filter(
                type=Notification.TYPE_ASSESSMENT_REQUEST,
                observation_log=self.observation_log,
            ).count(),
        )
        mock_send.assert_called_once()

    def test_request_not_created_without_designated_approvers_or_pending_status(self) -> None:
        self.assertIsNone(send_assessment_approval_request_notification(self.observation_log))

        self.product.assessment_approvers.add(self.approver)
        self.observation_log.assessment_status = Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED
        self.observation_log.save()
        self.assertIsNone(send_assessment_approval_request_notification(self.observation_log))

    @patch(f"{MODULE}._send_assessment_approval_notifications")
    def test_result_closes_request_and_notifies_author(self, mock_send: MagicMock) -> None:
        self.product.assessment_approvers.add(self.approver)
        request = send_assessment_approval_request_notification(self.observation_log, send_external=False)
        self.assertIsNotNone(request)

        self.observation_log.approval_user = self.approver
        self.observation_log.assessment_status = Assessment_Status.ASSESSMENT_STATUS_REJECTED
        self.observation_log.rejection_remark = "Insufficient evidence"
        self.observation_log.save()

        result = send_assessment_approval_result_notification(self.observation_log)

        self.assertIsNotNone(result)
        self.assertFalse(Notification.objects.filter(pk=request.pk).exists())
        self.assertEqual(Notification.TYPE_ASSESSMENT_RESULT, result.type)
        self.assertIn("Insufficient evidence", result.message)
        self.assertTrue(Notification_Recipient.objects.filter(notification=result, user=self.author).exists())
        mock_send.assert_called_once()

    def test_result_not_created_without_request(self) -> None:
        self.observation_log.approval_user = self.approver
        self.observation_log.assessment_status = Assessment_Status.ASSESSMENT_STATUS_APPROVED
        self.observation_log.save()

        self.assertIsNone(send_assessment_approval_result_notification(self.observation_log))

    @patch(f"{MODULE}.send_slack_notification")
    @patch(f"{MODULE}.send_msteams_notification")
    @patch(f"{MODULE}.send_email_notification")
    @patch(f"{MODULE}._get_notification_slack_webhook", return_value="https://slack.example.com/hook")
    @patch(f"{MODULE}._get_notification_ms_teams_webhook", return_value="https://teams.example.com/hook")
    @patch(f"{MODULE}.get_base_url_frontend", return_value="https://secobserve.example.com/")
    @patch(f"{MODULE}.Settings.load")
    def test_external_channels_are_sent_once_per_event(
        self,
        mock_settings_load: MagicMock,
        _mock_base_url: MagicMock,
        _mock_teams_webhook: MagicMock,
        _mock_slack_webhook: MagicMock,
        mock_email: MagicMock,
        mock_teams: MagicMock,
        mock_slack: MagicMock,
    ) -> None:
        settings = Settings()
        settings.email_from = "secobserve@example.com"
        mock_settings_load.return_value = settings
        self.product.assessment_approvers.add(self.approver)

        send_assessment_approval_request_notification(self.observation_log)

        mock_email.assert_called_once()
        mock_teams.assert_called_once()
        mock_slack.assert_called_once()

    @patch(f"{MODULE}._send_assessment_approval_notifications")
    def test_backfill_is_idempotent_and_in_app_only(self, mock_send: MagicMock) -> None:
        self.product.assessment_approvers.add(self.approver)

        call_command("backfill_assessment_approval_notifications")
        call_command("backfill_assessment_approval_notifications")

        self.assertEqual(
            1,
            Notification.objects.filter(
                type=Notification.TYPE_ASSESSMENT_REQUEST,
                observation_log=self.observation_log,
            ).count(),
        )
        mock_send.assert_not_called()

    def test_channel_templates_render_with_direct_assessment_link(self) -> None:
        context = {
            "assessment_url": f"https://secobserve.example.com/#/observation_logs/{self.observation_log.pk}/show",
            "first_line": 'Assessment for observation "CVE-2026-0001" needs approval',
            "message": "An approver is needed.",
            "observation_log": self.observation_log,
        }

        email = _create_notification_message("email_assessment_approval.tpl", first_name=" Ada", **context)
        self.assertIsNotNone(email)
        self.assertIn(context["assessment_url"], email)

        for template in (
            "msteams_assessment_approval.tpl",
            "msteams_v2_assessment_approval.tpl",
            "slack_assessment_approval.tpl",
        ):
            rendered = _create_notification_message(template, **context)
            self.assertIsNotNone(rendered)
            payload = json.loads(rendered)
            self.assertIsInstance(payload, dict)
            self.assertIn(context["assessment_url"], rendered)
