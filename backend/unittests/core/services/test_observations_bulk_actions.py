from datetime import date
from unittest.mock import call, patch

from django.core.management import call_command
from rest_framework.exceptions import ValidationError

from application.core.models import Observation, Product
from application.core.services.observations_bulk_actions import (
    _check_observations,
    observations_bulk_assessment,
    observations_bulk_delete,
)
from application.core.types import Severity, Status, VEX_Justification
from unittests.base_test_case import BaseTestCase


class TestObservationsBulkActions(BaseTestCase):
    def setUp(self):
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

    @patch("application.core.services.observations_bulk_actions._check_observations")
    @patch("application.core.services.observations_bulk_actions.save_assessment")
    def test_observations_bulk_assessment(self, save_mock, check_mock):
        observation_2 = Observation()
        check_mock.return_value = [self.observation_1, observation_2]

        observations_bulk_assessment(
            product=self.product_1,
            new_severity=Severity.SEVERITY_CRITICAL,
            new_status=Status.STATUS_OPEN,
            comment="comment",
            observation_ids=[1, 2],
            new_vex_justification=VEX_Justification.JUSTIFICATION_COMPONENT_NOT_PRESENT,
            new_risk_acceptance_expiry_date=date(2024, 7, 1),
        )

        check_mock.assert_called_with(self.product_1, [1, 2])
        expected_calls = [
            call(
                observation=self.observation_1,
                new_severity=Severity.SEVERITY_CRITICAL,
                new_status=Status.STATUS_OPEN,
                comment="comment",
                new_vex_justification=VEX_Justification.JUSTIFICATION_COMPONENT_NOT_PRESENT,
                new_risk_acceptance_expiry_date=date(2024, 7, 1),
            ),
            call(
                observation=observation_2,
                new_severity=Severity.SEVERITY_CRITICAL,
                new_status=Status.STATUS_OPEN,
                comment="comment",
                new_vex_justification=VEX_Justification.JUSTIFICATION_COMPONENT_NOT_PRESENT,
                new_risk_acceptance_expiry_date=date(2024, 7, 1),
            ),
        ]
        save_mock.assert_has_calls(expected_calls, any_order=False)

    @patch("application.core.services.observations_bulk_actions._check_observations")
    @patch("django.db.models.query.QuerySet.delete")
    @patch("application.core.services.observations_bulk_actions.get_current_user")
    @patch("application.core.services.observations_bulk_actions.check_security_gate")
    @patch("application.core.models.Product.save")
    def test_observations_bulk_delete(
        self,
        product_save_mock,
        check_security_gate_mock,
        current_user_mock,
        delete_mock,
        check_mock,
    ):
        observations = Observation.objects.all()
        for observation in observations:
            observation.issue_tracker_issue_id = f"issue_{observation.pk}"
        check_mock.return_value = observations
        current_user_mock.return_value = self.user_internal

        observations_bulk_delete(self.product_1, [1, 2])

        check_mock.assert_called_with(self.product_1, [1, 2])
        delete_mock.assert_called_once()
        calls = [
            call(self.product_1, "issue_1", self.user_internal),
            call(self.product_1, "issue_2", self.user_internal),
        ]
        check_security_gate_mock.assert_called_once()
        self.product_1.save.assert_called_once()

    @patch("application.core.models.Observation.objects.filter")
    def test_check_observations_count(self, mock):
        mock.return_value.count.return_value = 1

        with self.assertRaises(ValidationError) as e:
            _check_observations(self.product_1, [1, 2])

        self.assertEqual(
            str(e.exception),
            "[ErrorDetail(string='Some observations do not exist', code='invalid')]",
        )

    def test_check_observation_not_in_product(self):
        product_2 = Product.objects.get(pk=2)

        with self.assertRaises(ValidationError) as e:
            _check_observations(product_2, [1])

        self.assertEqual(
            str(e.exception),
            "[ErrorDetail(string='Observation 1 does not belong to product 2', code='invalid')]",
        )

    def test_check_observation_product_success(self):
        product_1 = Product.objects.get(pk=1)

        observations = _check_observations(product_1, [1])

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0], Observation.objects.get(pk=1))

    @patch("application.core.services.observations_bulk_actions.user_has_permission")
    def test_check_observation_no_product_no_permission(self, mock_user_has_permission):
        mock_user_has_permission.return_value = False

        with self.assertRaises(ValidationError) as e:
            _check_observations(None, [1])

        self.assertEqual(
            str(e.exception),
            "[ErrorDetail(string='First observation without assessment permission: db_product_internal / db_observation_internal', code='invalid')]",
        )

    @patch("application.core.services.observations_bulk_actions.user_has_permission")
    def test_check_observation_no_product_success(self, mock_user_has_permission):
        mock_user_has_permission.return_value = True

        observations = _check_observations(None, [1])

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0], Observation.objects.get(pk=1))
