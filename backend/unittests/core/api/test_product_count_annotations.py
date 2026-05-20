from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from application.access_control.models import User
from application.commons.models import Settings
from application.core.models import Branch, Observation, Product
from application.core.types import Severity, Status
from application.import_observations.models import Parser
from application.metrics.models import Product_Metrics, Product_Metrics_Status
from application.metrics.services.metrics import calculate_product_metrics
from unittests.base_test_case import BaseTestCase


class TestProductCountAnnotationsApi(BaseTestCase):
    patch.TEST_PREFIX = (
        "test",
        "setUp",
    )

    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )
        super().setUpClass()

    def _set_observation_count_from_metrics(self, enabled: bool) -> None:
        Settings.objects.update(observation_count_from_metrics=enabled)

    def _get_as_admin(self, url: str):
        auth_path = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        with patch(auth_path) as mock_authenticate:
            mock_authenticate.return_value = User.objects.get(username="db_admin"), None
            return APIClient().get(url)

    def _get_response_item(self, url: str, product: Product) -> dict:
        response = self._get_as_admin(url)

        self.assertEqual(200, response.status_code)
        return next(item for item in response.data["results"] if item["id"] == product.pk)

    def _create_observation(self, product: Product, branch: Branch, severity: str, title: str) -> None:
        Observation.objects.create(
            title=title,
            product=product,
            branch=branch,
            parser=Parser.objects.first(),
            parser_severity=severity,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )

    def test_live_mode_counts_current_observations_for_products_and_product_groups(self):
        product = Product.objects.get(name="db_product_internal")
        product_group = Product.objects.get(name="db_product_group")
        branch = Branch.objects.get(product=product, is_default_branch=True)
        self._create_observation(product, branch, Severity.SEVERITY_HIGH, "live_mode_high")
        Product_Metrics.objects.update_or_create(
            product=product,
            date=timezone.localdate(),
            defaults={"active_high": 33},
        )
        self._set_observation_count_from_metrics(False)

        product_data = self._get_response_item("/api/products/", product)
        product_group_data = self._get_response_item("/api/product_groups/", product_group)

        self.assertEqual(1, product_data["active_high_observation_count"])
        self.assertEqual(1, product_group_data["active_high_observation_count"])

    def test_metrics_mode_loads_precalculated_counts_for_products_and_product_groups(self):
        product = Product.objects.get(name="db_product_internal")
        product_group = Product.objects.get(name="db_product_group")
        branch = Branch.objects.get(product=product, is_default_branch=True)

        self._create_observation(product, branch, Severity.SEVERITY_HIGH, "before_metrics_high")
        product.last_observation_change = timezone.now()
        product.save()
        before_calculation = timezone.now()

        calculate_product_metrics()
        metrics = Product_Metrics.objects.get(product=product, date=timezone.localdate())

        self._create_observation(product, branch, Severity.SEVERITY_CRITICAL, "after_metrics_critical")
        self._set_observation_count_from_metrics(True)
        product_data = self._get_response_item("/api/products/", product)
        product_group_data = self._get_response_item("/api/product_groups/", product_group)

        self.assertEqual(0, product_data["active_critical_observation_count"])
        self.assertEqual(1, product_data["active_high_observation_count"])
        self.assertEqual(1, metrics.active_high)
        self.assertEqual(0, product_group_data["active_critical_observation_count"])
        self.assertEqual(1, product_group_data["active_high_observation_count"])
        self.assertGreaterEqual(Product_Metrics_Status.load().last_calculated, before_calculation)

        self._set_observation_count_from_metrics(False)
        live_product_data = self._get_response_item("/api/products/", product)
        live_product_group_data = self._get_response_item("/api/product_groups/", product_group)

        self.assertEqual(1, live_product_data["active_critical_observation_count"])
        self.assertEqual(1, live_product_data["active_high_observation_count"])
        self.assertEqual(1, live_product_group_data["active_critical_observation_count"])
        self.assertEqual(1, live_product_group_data["active_high_observation_count"])
