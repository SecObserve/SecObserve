from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Component, Observation, Product
from application.core.types import Severity, Status
from application.import_observations.models import Parser
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from unittests.base_test_case import BaseTestCase


class TestComponentFilters(BaseTestCase):
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

    @patch("application.core.signals.get_current_user")
    def setUp(self, mock_user) -> None:
        mock_user.return_value = None
        super().setUp()

        product = Product.objects.get(name="db_product_internal")
        parser = Parser.objects.first()

        self.component_observations = self._create_component("component_observations")
        self.component_licenses = self._create_component("component_licenses")
        self.component_nothing = self._create_component("component_nothing")
        self.component_inactive_observation = self._create_component("component_inactive_observation")

        self._create_observation(product, parser, self.component_observations, Status.STATUS_OPEN)
        # A resolved observation must not count as an active observation
        self._create_observation(product, parser, self.component_inactive_observation, Status.STATUS_RESOLVED)

        License_Component.objects.create(
            identity_hash="identity_hash_licenses",
            product=product,
            component=self.component_licenses,
            component_name="component_licenses",
            component_version="1.0.0",
            component_name_version="component_licenses:1.0.0",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED,
        )

    def _create_component(self, name: str) -> Component:
        return Component.objects.create(
            identity_hash=f"identity_hash_{name}",
            name=name,
            version="1.0.0",
            name_version=f"{name}:1.0.0",
        )

    def _create_observation(self, product: Product, parser: Parser, component: Component, status: str) -> Observation:
        return Observation.objects.create(
            product=product,
            parser=parser,
            title=f"observation_{component.name}",
            current_severity=Severity.SEVERITY_MEDIUM,
            numerical_severity=Severity.NUMERICAL_SEVERITIES[Severity.SEVERITY_MEDIUM],
            current_status=status,
            import_last_seen=timezone.now(),
            origin_component=component,
            origin_component_name=component.name,
            origin_component_version=component.version,
        )

    def _get_component_names(self, url: str) -> set[str]:
        auth_path = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        with patch(auth_path) as mock_authenticate:
            mock_authenticate.return_value = User.objects.get(username="db_admin"), None
            response = APIClient().get(url)

        self.assertEqual(200, response.status_code)
        return {component["name"] for component in response.data["results"]}

    def test_no_filter(self):
        names = self._get_component_names("/api/components/")

        self.assertEqual(
            {
                "component_observations",
                "component_licenses",
                "component_nothing",
                "component_inactive_observation",
            },
            names,
        )

    def test_has_observations_true(self):
        names = self._get_component_names("/api/components/?has_observations=true")

        self.assertEqual({"component_observations"}, names)

    def test_has_observations_false(self):
        names = self._get_component_names("/api/components/?has_observations=false")

        self.assertEqual(
            {"component_licenses", "component_nothing", "component_inactive_observation"},
            names,
        )

    def test_has_licenses_true(self):
        names = self._get_component_names("/api/components/?has_licenses=true")

        self.assertEqual({"component_licenses"}, names)

    def test_has_licenses_false(self):
        names = self._get_component_names("/api/components/?has_licenses=false")

        self.assertEqual(
            {"component_observations", "component_nothing", "component_inactive_observation"},
            names,
        )

    def test_has_observations_and_has_licenses(self):
        names = self._get_component_names("/api/components/?has_observations=false&has_licenses=false")

        self.assertEqual({"component_nothing", "component_inactive_observation"}, names)
