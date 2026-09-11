from datetime import date
from unittest.mock import MagicMock, patch

from application.core.services.observation_log import create_observation_log
from application.core.types import Assessment_Status, Status
from unittests.base_test_case import BaseTestCase


class TestObservationLog(BaseTestCase):
    @patch("application.core.models.Observation.save")
    @patch("application.core.models.Observation_Log.save")
    @patch("application.core.services.observation_log.get_current_user")
    @patch("application.core.models.Product.save")
    @patch("application.core.services.observation_log.send_observation_notification")
    @patch("application.core.services.observation_log.send_observation_title_notification")
    def test_create_observation_log(
        self,
        mock_send_observation_title_notification,
        mock_send_observation_notification,
        mock_product_save,
        mock_user,
        mock_observation_log_save,
        mock_observation_save,
    ):
        mock_user.return_value = self.user_internal

        observation_log = create_observation_log(
            observation=self.observation_1,
            severity="severity",
            status="status",
            priority=1,
            priority_changed=True,
            comment="comment",
            vex_justification="vex_justification",
            vex_remediations="vex_remediation",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
            risk_acceptance_expiry_date=date(2024, 7, 1),
        )

        self.assertEqual(self.observation_1, observation_log.observation)
        self.assertEqual(self.user_internal, observation_log.user)
        self.assertEqual("severity", observation_log.severity)
        self.assertEqual("status", observation_log.status)
        self.assertEqual(1, observation_log.priority)
        self.assertEqual(True, observation_log.priority_changed)
        self.assertEqual("comment", observation_log.comment)
        self.assertEqual("vex_justification", observation_log.vex_justification)
        self.assertEqual("vex_remediation", observation_log.vex_remediations)
        self.assertEqual(
            Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
            observation_log.assessment_status,
        )
        self.assertEqual(date(2024, 7, 1), observation_log.risk_acceptance_expiry_date)

        self.assertEqual(self.observation_1.last_observation_log, observation_log.created)

        observation_log.save.assert_called_once()
        self.observation_1.save.assert_called_once()
        mock_user.assert_called_once()
        self.observation_1.product.save.assert_called_once()
        mock_send_observation_notification.assert_called_once()
        mock_send_observation_title_notification.assert_called_with(self.observation_1)

    def _patch_for_review(self) -> MagicMock:
        """The mocks the tests for the review notification need, so that no database is needed."""
        patchers = {
            "observation_save": patch("application.core.models.Observation.save"),
            "observation_log_save": patch("application.core.models.Observation_Log.save"),
            "product_save": patch("application.core.models.Product.save"),
            "current_user": patch("application.core.services.observation_log.get_current_user"),
            "send_observation": patch("application.core.services.observation_log.send_observation_notification"),
            "send_title": patch("application.core.services.observation_log.send_observation_title_notification"),
            "send_review": patch("application.core.services.observation_log.send_observation_review_notification"),
        }

        mocks = {}
        for name, patcher in patchers.items():
            mocks[name] = patcher.start()
            self.addCleanup(patcher.stop)

        mocks["current_user"].return_value = self.user_internal

        return mocks["send_review"]

    def _create_observation_log(self, status: str) -> None:
        create_observation_log(
            observation=self.observation_1,
            severity="",
            status=status,
            priority=None,
            priority_changed=False,
            comment="comment",
            vex_justification="",
            vex_remediations=None,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
            risk_acceptance_expiry_date=None,
        )

    def test_create_observation_log_set_to_in_review(self):
        mock_send_review = self._patch_for_review()
        self.observation_1.current_status = Status.STATUS_IN_REVIEW

        self._create_observation_log(Status.STATUS_IN_REVIEW)

        mock_send_review.assert_called_once_with(self.observation_1)

    def test_create_observation_log_set_to_another_status(self):
        mock_send_review = self._patch_for_review()
        self.observation_1.current_status = Status.STATUS_OPEN

        self._create_observation_log(Status.STATUS_OPEN)

        mock_send_review.assert_not_called()

    def test_create_observation_log_in_review_not_applied_yet(self):
        # an assessment that needs approval logs its status without applying it
        mock_send_review = self._patch_for_review()
        self.observation_1.current_status = Status.STATUS_OPEN

        self._create_observation_log(Status.STATUS_IN_REVIEW)

        mock_send_review.assert_not_called()

    def test_create_observation_log_still_in_review(self):
        # the status of the log is empty while it has not been changed
        mock_send_review = self._patch_for_review()
        self.observation_1.current_status = Status.STATUS_IN_REVIEW

        self._create_observation_log("")

        mock_send_review.assert_not_called()
