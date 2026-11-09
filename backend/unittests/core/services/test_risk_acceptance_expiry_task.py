from datetime import date, timedelta
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from application.core.models import Observation
from application.core.services.risk_acceptance_expiry_task import (
    expire_risk_acceptances,
)
from application.core.types import Status


class TestExpireRiskAcceptances(TestCase):
    def setUp(self) -> None:
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

    @patch("application.core.services.risk_acceptance_expiry_task.remove_assessment")
    def test_removal_is_not_propagated(self, remove_assessment_mock) -> None:
        observation = Observation.objects.get(pk=1)
        observation.assessment_status = Status.STATUS_RISK_ACCEPTED
        observation.current_status = Status.STATUS_RISK_ACCEPTED
        observation.risk_acceptance_expiry_date = date.today() - timedelta(days=1)
        observation.save()

        expire_risk_acceptances()

        remove_assessment_mock.assert_called_once_with(observation, "Risk acceptance has expired.", propagate=False)

    @patch("application.core.services.assessment.propagate_assessment")
    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    @patch("application.core.services.assessment.Rule_Engine")
    def test_expiry_is_no_assessment(self, *_mocks) -> None:
        observation = Observation.objects.get(pk=1)
        observation.rule_status = ""
        observation.parser_status = Status.STATUS_RISK_ACCEPTED
        observation.current_status = Status.STATUS_RISK_ACCEPTED
        observation.risk_acceptance_expiry_date = date.today() - timedelta(days=1)
        observation.last_assessment = timezone.now()
        observation.save()

        expire_risk_acceptances()

        observation.refresh_from_db()
        self.assertEqual(Status.STATUS_OPEN, observation.current_status)
        self.assertIsNone(observation.last_assessment)
