from unittest.mock import patch

from rest_framework.test import APIClient

from application.access_control.models import User
from application.audit_trail.models import Product_Audit_Event
from unittests.authorization.api.test_authorization import TestAuthorizationBase


class TestProductAuditEventViewSet(TestAuthorizationBase):
    def setUp(self) -> None:
        super().setUp()
        for product_id in (1, 2, 99):
            Product_Audit_Event.objects.create(
                product_id=product_id,
                product_name=f"product_{product_id}",
                object_type="Product",
                object_id=product_id,
                object_name=f"product_{product_id}",
                action="Created",
            )

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def _get(self, username: str, url: str, mock_authentication):
        mock_authentication.return_value = User.objects.get(username=username), None
        return APIClient().get(url)

    def _product_ids(self, response) -> list[int]:
        self.assertEqual(200, response.status_code)
        return sorted(event["product"] for event in response.data["results"])

    def test_superuser(self) -> None:
        self.assertEqual([1, 2, 99], self._product_ids(self._get("db_admin", "/api/product_audit_events/")))
        # Events of deleted products
        self.assertEqual([99], self._product_ids(self._get("db_admin", "/api/product_audit_events/?product=99")))

    def test_owner(self) -> None:
        response = self._get("db_internal_write", "/api/product_audit_events/?product=1")
        self.assertEqual([1], self._product_ids(response))
        self.assertEqual("product_1", response.data["results"][0]["object_name"])

    def test_product_required(self) -> None:
        self.assertEqual(400, self._get("db_internal_write", "/api/product_audit_events/").status_code)
        self.assertEqual(400, self._get("db_internal_write", "/api/product_audit_events/?product=abc").status_code)
        self.assertEqual(400, self._get("db_internal_write", "/api/product_audit_events/?product=99").status_code)

    def test_no_permission(self) -> None:
        # Reader of product 1
        self.assertEqual(403, self._get("db_internal_read", "/api/product_audit_events/?product=1").status_code)
        # No member of product 2
        self.assertEqual(403, self._get("db_internal_write", "/api/product_audit_events/?product=2").status_code)
