from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Branch, Component, Observation, Product
from application.core.types import Severity, Status
from application.import_observations.models import Parser
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from unittests.base_test_case import BaseTestCase


class TestProductComponentFilter(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user: MagicMock) -> None:
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

    def setUp(self) -> None:
        super().setUp()
        self.product_internal = Product.objects.get(name="db_product_internal")
        self.product_external = Product.objects.get(name="db_product_external")
        self.component = Component.objects.create(
            identity_hash="test_product_component_filter",
            name="test_component",
            version="1.0.0",
            name_version="test_component:1.0.0",
        )

    def _get_product_names(self, query: str) -> set[str]:
        auth_path = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        with patch(auth_path) as mock_authenticate:
            mock_authenticate.return_value = User.objects.get(username="db_admin"), None
            response = APIClient().get(f"/api/products/?component={self.component.pk}{query}")

        self.assertEqual(200, response.status_code)
        return {item["name"] for item in response.data["results"]}

    def _create_license_component(self, product: Product, branch: Branch) -> None:
        License_Component.objects.create(
            identity_hash=f"{product.name}_{branch.name}",
            product=product,
            branch=branch,
            component=self.component,
            component_name=self.component.name,
            component_name_version=self.component.name_version,
            evaluation_result=License_Policy_Evaluation_Result.RESULT_ALLOWED,
            numerical_evaluation_result=License_Policy_Evaluation_Result.NUMERICAL_RESULTS[
                License_Policy_Evaluation_Result.RESULT_ALLOWED
            ],
        )

    def _create_observation(self, product: Product, branch: Branch, status: str) -> None:
        Observation.objects.create(
            title=f"{product.name}_{branch.name}_{status}",
            product=product,
            branch=branch,
            parser=Parser.objects.first(),
            parser_severity=Severity.SEVERITY_HIGH,
            parser_status=status,
            origin_component=self.component,
            import_last_seen=timezone.now(),
        )

    def test_license_components_and_active_observations_on_any_branch(self) -> None:
        self._create_license_component(self.product_internal, Branch.objects.get(name="db_branch_internal_main"))
        self._create_observation(
            self.product_external, Branch.objects.get(name="db_branch_external"), Status.STATUS_OPEN
        )

        self.assertEqual({"db_product_internal", "db_product_external"}, self._get_product_names(""))

    def test_inactive_observations_are_ignored(self) -> None:
        self._create_observation(
            self.product_internal, Branch.objects.get(name="db_branch_internal_dev"), Status.STATUS_RESOLVED
        )

        self.assertEqual(set(), self._get_product_names(""))

    def test_default_branch_only(self) -> None:
        internal_main = Branch.objects.get(name="db_branch_internal_main")
        self._create_license_component(self.product_internal, internal_main)
        self._create_observation(self.product_internal, internal_main, Status.STATUS_OPEN)
        self._create_observation(
            self.product_external, Branch.objects.get(name="db_branch_external"), Status.STATUS_OPEN
        )

        self.assertEqual({"db_product_external"}, self._get_product_names("&component_default_branch_only=true"))
        self.assertEqual(
            {"db_product_internal", "db_product_external"},
            self._get_product_names("&component_default_branch_only=false"),
        )
