from unittest.mock import patch

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.test import APIClient

from application.authorization.services.roles_permissions import Roles
from application.commons.models import Settings
from application.commons.services.security_gate_conditions import (
    normalize_security_gate_conditions,
)
from application.core.models import Product_Member
from unittests.base_test_case import BaseTestCase
from unittests.core.observation_fixtures import ObservationFixtureMixin

THRESHOLDS = {
    "security_gate_threshold_critical": 0,
    "security_gate_threshold_high": 99999,
    "security_gate_threshold_medium": 99999,
    "security_gate_threshold_low": 99999,
    "security_gate_threshold_none": 99999,
    "security_gate_threshold_unknown": 99999,
}
KEV = {"default": [{"known_exploited": True}]}


def _row(rows, severity):
    return next(row for row in rows if row["severity"] == severity)


class TestSecurityGatePreview(ObservationFixtureMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self._observation("kev", cve_found_in="CISA KEV")
        self._observation("plain")
        # A class level patch breaks setUpClass when the whole suite runs
        patcher = patch(
            "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        )
        self.mock_authentication = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_authentication.return_value = self.user_admin, None

    def test_product_preview_returns_rows(self):

        response = APIClient().post(
            f"/api/products/{self.product_1.pk}/security_gate_preview/",
            {"security_gate_advanced": True, "security_gate_conditions": KEV, **THRESHOLDS},
            format="json",
        )

        self.assertEqual(HTTP_200_OK, response.status_code)
        critical = _row(response.data, "Critical")
        self.assertEqual((critical["active"], critical["counted"], critical["threshold"]), (2, 1, 0))
        self.assertFalse(critical["passed"])
        self.assertTrue(_row(response.data, "High")["passed"])

    def test_product_preview_without_advanced_counts_everything(self):
        response = APIClient().post(
            f"/api/products/{self.product_1.pk}/security_gate_preview/",
            {"security_gate_advanced": False, "security_gate_conditions": KEV, **THRESHOLDS},
            format="json",
        )

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(_row(response.data, "Critical")["counted"], 2)

    def test_product_preview_rejects_bad_conditions(self):
        response = APIClient().post(
            f"/api/products/{self.product_1.pk}/security_gate_preview/",
            {"security_gate_advanced": True, "security_gate_conditions": {"default": [{"operator": "nor"}]}},
            format="json",
        )

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)

    def test_product_preview_uses_effective_thresholds_when_omitted(self):
        settings = Settings.load()
        settings.security_gate_threshold_critical = 5
        settings.save()

        response = APIClient().post(
            f"/api/products/{self.product_1.pk}/security_gate_preview/",
            {"security_gate_advanced": True, "security_gate_conditions": KEV},
            format="json",
        )

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(_row(response.data, "Critical")["threshold"], 5)

    def _configure_product_gate(self):
        self.product_1.security_gate_active = True
        self.product_1.security_gate_advanced = True
        self.product_1.security_gate_conditions = normalize_security_gate_conditions(KEV)
        for field, threshold in THRESHOLDS.items():
            setattr(self.product_1, field, threshold)
        self.product_1.save()

    def test_product_preview_get_returns_the_configured_gate(self):
        self._configure_product_gate()

        response = APIClient().get(f"/api/products/{self.product_1.pk}/security_gate_preview/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        critical = _row(response.data, "Critical")
        self.assertEqual((critical["active"], critical["counted"], critical["threshold"]), (2, 1, 0))

    def test_product_preview_get_is_empty_without_a_gate(self):
        self.product_1.security_gate_active = False
        self.product_1.save()

        response = APIClient().get(f"/api/products/{self.product_1.pk}/security_gate_preview/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual([], response.data)

    def test_product_preview_get_works_for_external_readers(self):
        # External users may not POST to products, but the show page must explain the gate to them
        self._configure_product_gate()
        self.user_external.save()
        Product_Member.objects.create(product=self.product_1, user=self.user_external, role=Roles.Reader)
        self.mock_authentication.return_value = self.user_external, None

        response = APIClient().get(f"/api/products/{self.product_1.pk}/security_gate_preview/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(_row(response.data, "Critical")["counted"], 1)

    def test_product_preview_post_without_a_draft_counts_everything(self):
        self._configure_product_gate()

        response = APIClient().post(f"/api/products/{self.product_1.pk}/security_gate_preview/", {}, format="json")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(_row(response.data, "Critical")["counted"], 2)

    def test_settings_preview_counts_all_products(self):
        response = APIClient().post(
            "/api/settings/1/security_gate_preview/",
            {"security_gate_advanced": True, "security_gate_conditions": KEV, **THRESHOLDS},
            format="json",
        )

        self.assertEqual(HTTP_200_OK, response.status_code)
        critical = _row(response.data, "Critical")
        self.assertEqual((critical["active"], critical["counted"]), (2, 1))

    def test_settings_preview_needs_superuser(self):
        self.mock_authentication.return_value = self.user_internal, None

        response = APIClient().post(
            "/api/settings/1/security_gate_preview/",
            {"security_gate_advanced": True, "security_gate_conditions": KEV, **THRESHOLDS},
            format="json",
        )

        self.assertEqual(403, response.status_code)
