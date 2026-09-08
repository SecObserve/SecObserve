from unittest.mock import MagicMock, patch

from django.db import transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Observation,
    Observation_Log,
    Product,
    Product_Member,
)
from application.core.services.assessment import assessment_approval, save_assessment
from application.core.services.observations_bulk_actions import (
    observation_logs_bulk_approval,
)
from application.core.types import Assessment_Status, Severity, Status
from application.import_observations.models import Parser


class TestAssessmentNotificationLifecycle(TestCase):
    def setUp(self) -> None:
        with patch("application.core.signals.get_current_user", return_value=None):
            self.product = Product.objects.create(name="notification-product", assessments_need_approval=True)
        self.author = User.objects.create(username="notification-author@example.com")
        self.approver = User.objects.create(username="notification-approver@example.com")
        Product_Member.objects.create(product=self.product, user=self.author, role=Roles.Writer)
        Product_Member.objects.create(product=self.product, user=self.approver, role=Roles.Writer)
        self.product.assessment_approvers.add(self.approver)
        parser = Parser.objects.create(name="assessment-lifecycle-parser")
        self.observation = Observation.objects.create(
            product=self.product,
            parser=parser,
            title="Notification lifecycle",
            current_severity=Severity.SEVERITY_HIGH,
            current_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )

    @patch("application.core.services.assessment.send_assessment_approval_request_notification")
    @patch("application.core.services.observation_log.get_current_user")
    def test_pending_assessment_schedules_request_after_commit(
        self,
        mock_current_user: MagicMock,
        mock_send_request: MagicMock,
    ) -> None:
        mock_current_user.return_value = self.author

        with self.captureOnCommitCallbacks(execute=True):
            save_assessment(
                observation=self.observation,
                new_severity=Severity.SEVERITY_CRITICAL,
                new_status=None,
                new_priority=None,
                comment="Raise severity",
                new_vex_justification=None,
                new_vex_remediations=None,
                new_risk_acceptance_expiry_date=None,
            )

        observation_log = Observation_Log.objects.get(observation=self.observation)
        self.assertEqual(Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL, observation_log.assessment_status)
        mock_send_request.assert_called_once_with(observation_log)

    @patch("application.core.services.assessment.send_assessment_approval_request_notification")
    @patch("application.core.services.observation_log.get_current_user")
    def test_rolled_back_assessment_does_not_schedule_request(
        self,
        mock_current_user: MagicMock,
        mock_send_request: MagicMock,
    ) -> None:
        mock_current_user.return_value = self.author

        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    save_assessment(
                        observation=self.observation,
                        new_severity=Severity.SEVERITY_CRITICAL,
                        new_status=None,
                        new_priority=None,
                        comment="Rollback",
                        new_vex_justification=None,
                        new_vex_remediations=None,
                        new_risk_acceptance_expiry_date=None,
                    )
                    raise RuntimeError("rollback")
            except RuntimeError:
                pass

        mock_send_request.assert_not_called()
        self.assertFalse(Observation_Log.objects.filter(observation=self.observation).exists())

    @patch("application.core.services.assessment.send_assessment_approval_result_notification")
    @patch("application.core.services.assessment.get_current_user")
    def test_rejection_schedules_result_after_commit(
        self,
        mock_current_user: MagicMock,
        mock_send_result: MagicMock,
    ) -> None:
        observation_log = self._create_pending_log()
        mock_current_user.return_value = self.approver

        with self.captureOnCommitCallbacks(execute=True):
            assessment_approval(
                observation_log,
                Assessment_Status.ASSESSMENT_STATUS_REJECTED,
                "Insufficient evidence",
                None,
                None,
                None,
            )

        observation_log.refresh_from_db()
        mock_send_result.assert_called_once_with(observation_log)

    @patch("application.core.services.assessment.send_assessment_approval_result_notification")
    @patch("application.core.services.assessment.get_current_user")
    def test_failed_self_approval_does_not_schedule_result(
        self,
        mock_current_user: MagicMock,
        mock_send_result: MagicMock,
    ) -> None:
        observation_log = self._create_pending_log()
        mock_current_user.return_value = self.author

        with self.assertRaises(ValidationError):
            assessment_approval(
                observation_log,
                Assessment_Status.ASSESSMENT_STATUS_REJECTED,
                "No",
                None,
                None,
                None,
            )

        mock_send_result.assert_not_called()

    @patch("application.core.services.observations_bulk_actions.set_potential_duplicate_both_ways")
    @patch("application.core.services.observations_bulk_actions.user_has_permission", return_value=True)
    @patch("application.core.services.observations_bulk_actions.get_current_user")
    @patch("application.core.services.assessment.send_assessment_approval_result_notification")
    @patch("application.core.services.assessment.get_current_user")
    def test_bulk_rejection_uses_same_result_lifecycle(
        self,
        mock_assessment_current_user: MagicMock,
        mock_send_result: MagicMock,
        mock_bulk_current_user: MagicMock,
        _mock_permission: MagicMock,
        _mock_duplicates: MagicMock,
    ) -> None:
        observation_log = self._create_pending_log()
        mock_assessment_current_user.return_value = self.approver
        mock_bulk_current_user.return_value = self.approver

        with self.captureOnCommitCallbacks(execute=True):
            observation_logs_bulk_approval(
                Assessment_Status.ASSESSMENT_STATUS_REJECTED,
                "Insufficient evidence",
                None,
                [observation_log.pk],
            )

        observation_log.refresh_from_db()
        mock_send_result.assert_called_once_with(observation_log)

    def _create_pending_log(self) -> Observation_Log:
        return Observation_Log.objects.create(
            observation=self.observation,
            user=self.author,
            severity=Severity.SEVERITY_CRITICAL,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL,
            comment="Raise severity",
        )
