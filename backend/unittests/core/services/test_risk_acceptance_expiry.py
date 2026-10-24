from datetime import date, timedelta
from unittest.mock import patch

from application.commons.models import Settings
from application.core.models import Observation, Product
from application.core.services.risk_acceptance_expiry import (
    calculate_expiry_date,
    calculate_risk_acceptance_expiry_date,
    update_expiry_date,
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


class TestExpiryDate(BaseTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch(
            "application.core.services.risk_acceptance_expiry.calculate_risk_acceptance_expiry_date",
            return_value=date(2030, 1, 1),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

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
