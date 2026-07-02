from unittest.mock import patch

from rest_framework.exceptions import ValidationError

from application.core.models import Observation_Log
from application.core.services.assessment import assessment_approval
from application.core.types import Assessment_Status, Severity, Status
from unittests.base_test_case import BaseTestCase


class TestAssessmentApproval(BaseTestCase):
    def _needs_approval_log(self) -> Observation_Log:
        return Observation_Log(
            observation=self.observation_1,
            user=self.user_internal,
            severity=Severity.SEVERITY_HIGH,
            status=Status.STATUS_OPEN,
            comment="comment",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL,
        )

    def test_assessment_approval_does_not_need(self):
        observation_log = Observation_Log(
            observation=self.observation_1,
            user=self.user_internal,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
        )
        with self.assertRaises(ValidationError) as e:
            assessment_approval(
                observation_log,
                Assessment_Status.ASSESSMENT_STATUS_APPROVED,
                None,
                None,
            )

        self.assertEqual(
            str(e.exception),
            "[ErrorDetail(string='Observation log does not need approval', code='invalid')]",
        )

    @patch("application.core.services.assessment.get_current_user")
    def test_assessment_approval_own_assessment(self, get_current_user_mock):
        get_current_user_mock.return_value = self.user_internal
        observation_log = self._needs_approval_log()
        with self.assertRaises(ValidationError) as e:
            assessment_approval(
                observation_log,
                Assessment_Status.ASSESSMENT_STATUS_APPROVED,
                None,
                None,
            )

        self.assertEqual(
            str(e.exception),
            "[ErrorDetail(string='Users cannot approve their own assessment', code='invalid')]",
        )

    @patch("application.core.services.assessment.send_observation_title_notification")
    @patch("application.core.services.assessment.send_observation_notification")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    @patch("application.core.services.assessment._update_observation")
    @patch("application.core.models.Observation_Log.save")
    @patch("application.core.services.assessment.get_current_user")
    def test_assessment_approval_rejected(
        self,
        get_current_user_mock,
        save_mock,
        update_observation_mock,
        check_security_gate_mock,
        push_to_issue_tracker_mock,
        send_notification_mock,
        send_title_notification_mock,
    ):
        get_current_user_mock.return_value = self.user_external
        observation_log = self._needs_approval_log()

        assessment_approval(
            observation_log,
            Assessment_Status.ASSESSMENT_STATUS_REJECTED,
            "bad",
            None,
        )

        update_observation_mock.assert_not_called()
        check_security_gate_mock.assert_not_called()
        push_to_issue_tracker_mock.assert_not_called()
        send_notification_mock.assert_not_called()
        send_title_notification_mock.assert_not_called()

        self.assertEqual(observation_log.approval_user, self.user_external)
        self.assertEqual(observation_log.rejection_remark, "bad")
        self.assertEqual(
            observation_log.assessment_status,
            Assessment_Status.ASSESSMENT_STATUS_REJECTED,
        )
        self.assertIsNotNone(observation_log.approval_date)
        self.assertEqual(observation_log.comment, "comment")
        save_mock.assert_called_once()

    @patch("application.core.services.assessment.send_observation_title_notification")
    @patch("application.core.services.assessment.send_observation_notification")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    @patch("application.core.services.assessment._update_observation")
    @patch("application.core.models.Observation_Log.save")
    @patch("application.core.services.assessment.get_current_user")
    def test_assessment_approval_approved(
        self,
        get_current_user_mock,
        save_mock,
        update_observation_mock,
        check_security_gate_mock,
        push_to_issue_tracker_mock,
        send_notification_mock,
        send_title_notification_mock,
    ):
        get_current_user_mock.return_value = self.user_external
        observation_log = self._needs_approval_log()

        assessment_approval(
            observation_log,
            Assessment_Status.ASSESSMENT_STATUS_APPROVED,
            None,
            None,
        )

        update_observation_mock.assert_called_once()
        check_security_gate_mock.assert_called_once_with(self.observation_1.product)
        push_to_issue_tracker_mock.assert_called_once_with(self.observation_1, self.user_external)
        send_notification_mock.assert_called_once_with(self.observation_1)
        send_title_notification_mock.assert_called_once_with(self.observation_1)

        self.assertEqual(observation_log.approval_user, self.user_external)
        self.assertEqual(observation_log.rejection_remark, "")
        self.assertEqual(
            observation_log.assessment_status,
            Assessment_Status.ASSESSMENT_STATUS_APPROVED,
        )
        self.assertIsNotNone(observation_log.approval_date)
        self.assertEqual(observation_log.comment, "comment")
        save_mock.assert_called_once()

    @patch("application.core.services.assessment.send_observation_title_notification")
    @patch("application.core.services.assessment.send_observation_notification")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    @patch("application.core.services.assessment._update_observation")
    @patch("application.core.models.Observation_Log.save")
    @patch("application.core.services.assessment.get_current_user")
    def test_assessment_approval_approved_with_edits_comment(
        self,
        get_current_user_mock,
        save_mock,
        update_observation_mock,
        check_security_gate_mock,
        push_to_issue_tracker_mock,
        send_notification_mock,
        send_title_notification_mock,
    ):
        get_current_user_mock.return_value = self.user_external
        observation_log = self._needs_approval_log()

        assessment_approval(
            observation_log,
            Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
            None,
            "edited",
        )

        self.assertEqual(observation_log.comment, "edited")
        update_observation_mock.assert_called_once()
        check_security_gate_mock.assert_called_once_with(self.observation_1.product)
        push_to_issue_tracker_mock.assert_called_once_with(self.observation_1, self.user_external)
        send_notification_mock.assert_called_once_with(self.observation_1)
        send_title_notification_mock.assert_called_once_with(self.observation_1)

        self.assertEqual(observation_log.approval_user, self.user_external)
        self.assertEqual(
            observation_log.assessment_status,
            Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
        )
        self.assertIsNotNone(observation_log.approval_date)
        # once for the comment edit, once for the final stamp
        self.assertEqual(save_mock.call_count, 2)

    @patch("application.core.services.assessment.send_observation_title_notification")
    @patch("application.core.services.assessment.send_observation_notification")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    @patch("application.core.services.assessment._update_observation")
    @patch("application.core.models.Observation_Log.save")
    @patch("application.core.services.assessment.get_current_user")
    def test_assessment_approval_approved_with_edits_no_comment(
        self,
        get_current_user_mock,
        save_mock,
        update_observation_mock,
        check_security_gate_mock,
        push_to_issue_tracker_mock,
        send_notification_mock,
        send_title_notification_mock,
    ):
        get_current_user_mock.return_value = self.user_external
        observation_log = self._needs_approval_log()

        assessment_approval(
            observation_log,
            Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
            None,
            None,
        )

        self.assertEqual(observation_log.comment, "comment")
        update_observation_mock.assert_called_once()
        check_security_gate_mock.assert_called_once_with(self.observation_1.product)
        push_to_issue_tracker_mock.assert_called_once_with(self.observation_1, self.user_external)
        send_notification_mock.assert_called_once_with(self.observation_1)
        send_title_notification_mock.assert_called_once_with(self.observation_1)

        self.assertEqual(
            observation_log.assessment_status,
            Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
        )
        self.assertIsNotNone(observation_log.approval_date)
        # comment branch skipped, so only the final stamp saves
        save_mock.assert_called_once()
