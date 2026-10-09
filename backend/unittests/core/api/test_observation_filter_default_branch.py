from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from drf_spectacular.drainage import GENERATOR_STATS
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Branch, Observation, Product
from application.core.types import Status
from application.import_observations.models import Parser
from unittests.base_test_case import BaseTestCase


class TestObservationFilterDefaultBranch(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
            ],
        )
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.group = Product.objects.create(name="default_branch_group", is_product_group=True)

        product_with_branches = Product.objects.create(name="default_branch_with_branches", product_group=self.group)
        main = Branch.objects.create(product=product_with_branches, name="main", is_default_branch=True)
        feature = Branch.objects.create(product=product_with_branches, name="feature")
        self._create_observation(product_with_branches, main, "with_branches_main")
        self._create_observation(product_with_branches, feature, "with_branches_feature")
        self._create_observation(product_with_branches, None, "with_branches_none")

        product_without_branches = Product.objects.create(
            name="default_branch_without_branches", product_group=self.group
        )
        self._create_observation(product_without_branches, None, "without_branches_none")

        product_outside_group = Product.objects.create(name="default_branch_outside_group")
        self._create_observation(product_outside_group, None, "outside_group_none")

    def _create_observation(self, product: Product, branch: Branch | None, title: str) -> None:
        Observation.objects.create(
            title=title,
            product=product,
            branch=branch,
            parser=Parser.objects.first(),
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )

    def _get_as_admin(self, url: str):
        auth_path = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        with patch(auth_path) as mock_authenticate:
            mock_authenticate.return_value = User.objects.get(username="db_admin"), None
            return APIClient().get(url)

    def _get_titles(self, query: str = "") -> set[str]:
        url = f"/api/observations/?product_group={self.group.pk}"
        if query:
            url += f"&{query}"
        response = self._get_as_admin(url)
        self.assertEqual(200, response.status_code)
        return {observation["title"] for observation in response.data["results"]}

    def test_default_branch_true(self):
        self.assertEqual(
            {"with_branches_main", "without_branches_none"},
            self._get_titles("default_branch=true"),
        )

    def test_default_branch_false(self):
        self.assertEqual(
            {"with_branches_feature", "with_branches_none"},
            self._get_titles("default_branch=false"),
        )

    def test_default_branch_absent(self):
        self.assertEqual(
            {"with_branches_main", "with_branches_feature", "with_branches_none", "without_branches_none"},
            self._get_titles(),
        )

    def test_default_branch_matches_header_counts(self):
        response = self._get_as_admin(f"/api/product_groups/{self.group.pk}/")
        self.assertEqual(200, response.status_code)
        header_count = sum(value for key, value in response.data.items() if key.endswith("_observation_count"))

        self.assertEqual(header_count, len(self._get_titles("default_branch=true")))

    def test_openapi_schema(self):
        with GENERATOR_STATS.silence():
            response = self._get_as_admin("/api/oa3/schema/?format=json")
        self.assertEqual(200, response.status_code)

        parameters = response.data["paths"]["/api/observations/"]["get"]["parameters"]
        self.assertIn("default_branch", [parameter["name"] for parameter in parameters])
