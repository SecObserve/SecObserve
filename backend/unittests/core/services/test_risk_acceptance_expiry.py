from datetime import date, timedelta
from unittest.mock import patch

from django.core.management import call_command

from application.commons.models import Settings
from application.core.models import Observation, Product
from application.core.services.assessment import remove_assessment
from application.core.services.risk_acceptance_expiry import (
    calculate_expiry_date,
    calculate_not_affected_expiry_date,
    calculate_risk_acceptance_expiry_date,
    has_expiry,
    update_expiry_date,
)
from application.core.services.risk_acceptance_expiry_task import (
    expire_risk_acceptances,
)
from application.core.types import Status
from unittests.base_test_case import BaseTestCase


class TestCalculateRiskAcceptanceExpiryDate(BaseTestCase):

    def test_product_risk_acceptance_expiry_active_is_none(self):
        product = Product(risk_acceptance_expiry_active=None)
        product.product_group = Product(risk_acceptance_expiry_active=None)
        self.assertEqual(date.today() + timedelta(30), calculate_risk_acceptance_expiry_date(product))

    def test_product_risk_acceptance_expiry_active_is_false(self):
        product = Product(risk_acceptance_expiry_active=False)
        self.assertIsNone(calculate_risk_acceptance_expiry_date(product))

    def test_product_risk_acceptance_expiry_active_is_true_and_days_is_none(self):
        product = Product(risk_acceptance_expiry_active=True, risk_acceptance_expiry_days=None)
        self.assertEqual(date.today() + timedelta(30), calculate_risk_acceptance_expiry_date(product))

    def test_product_risk_acceptance_expiry_active_is_true_and_days_is_zero(self):
        product = Product(risk_acceptance_expiry_active=True, risk_acceptance_expiry_days=0)
        self.assertEqual(date.today() + timedelta(30), calculate_risk_acceptance_expiry_date(product))

    def test_product_risk_acceptance_expiry_active_is_true_and_days_is_positive(self):
        product = Product(risk_acceptance_expiry_active=True, risk_acceptance_expiry_days=1)
        self.assertEqual(date.today() + timedelta(1), calculate_risk_acceptance_expiry_date(product))

    def test_product_group_risk_acceptance_expiry_active_is_false(self):
        product = Product(risk_acceptance_expiry_active=None)
        product.product_group = Product(risk_acceptance_expiry_active=False)
        self.assertIsNone(calculate_risk_acceptance_expiry_date(product))

    def test_product_group_risk_acceptance_expiry_active_is_true_and_days_is_none(self):
        product = Product(risk_acceptance_expiry_active=None)
        product.product_group = Product(risk_acceptance_expiry_active=True, risk_acceptance_expiry_days=None)
        self.assertEqual(date.today() + timedelta(30), calculate_risk_acceptance_expiry_date(product))

    def test_product_group_risk_acceptance_expiry_active_is_true_and_days_is_zero(self):
        product = Product(risk_acceptance_expiry_active=None)
        product.product_group = Product(risk_acceptance_expiry_active=True, risk_acceptance_expiry_days=0)
        self.assertEqual(date.today() + timedelta(30), calculate_risk_acceptance_expiry_date(product))

    def test_product_group_risk_acceptance_expiry_active_is_true_and_days_is_positive(
        self,
    ):
        product = Product(risk_acceptance_expiry_active=None)
        product.product_group = Product(risk_acceptance_expiry_active=True, risk_acceptance_expiry_days=2)
        self.assertEqual(date.today() + timedelta(2), calculate_risk_acceptance_expiry_date(product))

    def test_settings_risk_acceptance_expiry_days_is_zero(self):
        product = Product(risk_acceptance_expiry_active=None)
        product.product_group = Product(risk_acceptance_expiry_active=None)
        settings = Settings.load()
        settings.risk_acceptance_expiry_days = 0
        settings.save()
        self.assertIsNone(calculate_risk_acceptance_expiry_date(product))
        settings.delete()


class TestCalculateNotAffectedExpiryDate(BaseTestCase):
    def test_settings_default(self):
        product = Product(not_affected_expiry_active=None)
        self.assertEqual(date.today() + timedelta(30), calculate_not_affected_expiry_date(product))

    def test_product_disabled(self):
        product = Product(not_affected_expiry_active=False, risk_acceptance_expiry_active=True)
        self.assertIsNone(calculate_not_affected_expiry_date(product))

    def test_product_days(self):
        product = Product(not_affected_expiry_active=True, not_affected_expiry_days=3, risk_acceptance_expiry_days=5)
        self.assertEqual(date.today() + timedelta(3), calculate_not_affected_expiry_date(product))

    def test_product_group_days(self):
        product = Product(not_affected_expiry_active=None)
        product.product_group = Product(not_affected_expiry_active=True, not_affected_expiry_days=4)
        self.assertEqual(date.today() + timedelta(4), calculate_not_affected_expiry_date(product))

    def test_settings_days_is_zero(self):
        settings = Settings.load()
        settings.not_affected_expiry_days = 0
        settings.save()
        self.assertIsNone(calculate_not_affected_expiry_date(Product(not_affected_expiry_active=None)))
        settings.delete()


class TestExpiryDate(BaseTestCase):
    def setUp(self):
        super().setUp()
        for function, value in (
            ("calculate_risk_acceptance_expiry_date", date(2030, 1, 1)),
            ("calculate_not_affected_expiry_date", date(2031, 1, 1)),
        ):
            patcher = patch(f"application.core.services.risk_acceptance_expiry.{function}", return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _set_not_affected_expiry_vex(self, value: bool) -> None:
        settings = Settings.load()
        settings.not_affected_expiry_vex = value
        settings.save()
        self.addCleanup(settings.delete)

    def test_calculate_expiry_date_not_affected(self):
        self.assertEqual(date(2031, 1, 1), calculate_expiry_date(Product(), Status.STATUS_NOT_AFFECTED))

    def test_update_expiry_date_risk_accepted_to_not_affected(self):
        observation = Observation(
            current_status=Status.STATUS_NOT_AFFECTED,
            assessment_status=Status.STATUS_NOT_AFFECTED,
            risk_acceptance_expiry_date=date(2030, 1, 1),
            product=Product(),
        )
        update_expiry_date(observation, Status.STATUS_RISK_ACCEPTED)
        self.assertEqual(date(2031, 1, 1), observation.risk_acceptance_expiry_date)

    def test_has_expiry_not_affected_from_vex(self):
        observation = Observation(current_status=Status.STATUS_NOT_AFFECTED, vex_status=Status.STATUS_NOT_AFFECTED)
        self.assertFalse(has_expiry(observation))
        self._set_not_affected_expiry_vex(True)
        self.assertTrue(has_expiry(observation))

    def test_has_expiry_not_affected_from_assessment_over_vex(self):
        observation = Observation(
            current_status=Status.STATUS_NOT_AFFECTED,
            assessment_status=Status.STATUS_NOT_AFFECTED,
            vex_status=Status.STATUS_NOT_AFFECTED,
        )
        self.assertTrue(has_expiry(observation))

    def test_update_expiry_date_not_affected_from_vex(self):
        observation = Observation(
            current_status=Status.STATUS_NOT_AFFECTED,
            vex_status=Status.STATUS_NOT_AFFECTED,
            risk_acceptance_expiry_date=date(2020, 1, 1),
        )
        update_expiry_date(observation, Status.STATUS_NOT_AFFECTED)
        self.assertIsNone(observation.risk_acceptance_expiry_date)

    def test_update_expiry_date_unchanged_without_date_skips_settings(self):
        observation = Observation(current_status=Status.STATUS_NOT_AFFECTED, vex_status=Status.STATUS_NOT_AFFECTED)
        with self.assertNumQueries(0):
            update_expiry_date(observation, Status.STATUS_NOT_AFFECTED)
        self.assertIsNone(observation.risk_acceptance_expiry_date)

    def test_calculate_expiry_date_risk_accepted(self):
        self.assertEqual(date(2030, 1, 1), calculate_expiry_date(Product(), Status.STATUS_RISK_ACCEPTED))

    def test_calculate_expiry_date_other_status(self):
        self.assertIsNone(calculate_expiry_date(Product(), Status.STATUS_OPEN))

    def test_update_expiry_date_status_without_expiry(self):
        observation = Observation(current_status=Status.STATUS_OPEN, risk_acceptance_expiry_date=date(2029, 1, 1))
        update_expiry_date(observation, Status.STATUS_RISK_ACCEPTED)
        self.assertIsNone(observation.risk_acceptance_expiry_date)

    def test_update_expiry_date_status_changed(self):
        observation = Observation(current_status=Status.STATUS_RISK_ACCEPTED, product=Product())
        update_expiry_date(observation, Status.STATUS_OPEN)
        self.assertEqual(date(2030, 1, 1), observation.risk_acceptance_expiry_date)

    def test_update_expiry_date_status_unchanged(self):
        observation = Observation(
            current_status=Status.STATUS_RISK_ACCEPTED, risk_acceptance_expiry_date=date(2029, 1, 1)
        )
        update_expiry_date(observation, Status.STATUS_RISK_ACCEPTED)
        self.assertEqual(date(2029, 1, 1), observation.risk_acceptance_expiry_date)


class TestExpiryWithDatabase(BaseTestCase):
    def setUp(self):
        super().setUp()
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        self.observation = Observation.objects.get(pk=4)
        self.observation.current_status = Status.STATUS_NOT_AFFECTED
        self.observation.assessment_status = Status.STATUS_NOT_AFFECTED
        self.observation.risk_acceptance_expiry_date = date.today() - timedelta(days=1)

    @patch("application.core.services.assessment.push_observation_to_issue_tracker")
    @patch("application.core.services.assessment.check_security_gate")
    def test_remove_assessment_keeps_no_expiry_for_vex_status(self, _mock_security_gate, _mock_issue_tracker):
        self.observation.vex_status = Status.STATUS_NOT_AFFECTED
        self.observation.save()

        self.assertTrue(remove_assessment(self.observation, "comment"))

        self.observation.refresh_from_db()
        self.assertEqual(Status.STATUS_NOT_AFFECTED, self.observation.current_status)
        self.assertIsNone(self.observation.risk_acceptance_expiry_date)

    @patch("application.core.services.risk_acceptance_expiry_task.remove_assessment", return_value=True)
    def test_expire_not_affected(self, mock_remove_assessment):
        self.observation.save()

        expire_risk_acceptances()

        mock_remove_assessment.assert_called_once_with(self.observation, "Not affected assessment has expired.")
