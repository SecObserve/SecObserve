from unittest.mock import patch

from django.core.management import call_command
from rest_framework.test import APIClient

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import Audit_Log, Product, Product_Member
from application.core.types import Audit_Log_Action
from unittests.base_test_case import BaseTestCase


class TestAuditLogs(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def setUp(self):
        super().setUp()
        for product_name in ["db_product_internal", "db_product_group", "db_product_external", ""]:
            Audit_Log.objects.create(
                product=Product.objects.filter(name=product_name).first(),
                product_name=product_name,
                action=Audit_Log_Action.AUDIT_LOG_ACTION_APPROVER_ADDED,
            )

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def _get(self, username, url, mock_authentication):
        mock_authentication.return_value = User.objects.get(username=username), None
        return APIClient().get(url)

    def _product_names(self, response):
        self.assertEqual(200, response.status_code)
        return sorted(entry["product_name"] for entry in response.data["results"])

    def test_reader_is_forbidden(self):
        response = self._get("db_internal_read", "/api/audit_logs/?product=1")

        self.assertEqual(403, response.status_code)

    def test_maintainer_gets_product_and_product_group(self):
        Product_Member.objects.filter(product_id=1, user__username="db_internal_write").update(role=Roles.Maintainer)

        response = self._get("db_internal_write", "/api/audit_logs/?product=1")

        self.assertEqual(["db_product_group", "db_product_internal"], self._product_names(response))

    def test_product_group_owner_gets_product_group(self):
        response = self._get("db_product_group_user", "/api/audit_logs/?product=3")

        self.assertEqual(["db_product_group"], self._product_names(response))

    def test_no_product_is_empty_for_non_superuser(self):
        response = self._get("db_internal_write", "/api/audit_logs/")

        self.assertEqual([], self._product_names(response))

    def test_superuser_gets_all(self):
        response = self._get("db_admin", "/api/audit_logs/")

        self.assertEqual(
            ["", "db_product_external", "db_product_group", "db_product_internal"], self._product_names(response)
        )
