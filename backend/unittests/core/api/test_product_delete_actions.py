from rest_framework.test import APIClient

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.commons.services import global_request
from application.core.models import Product, Product_Delete_Request, Product_Member
from unittests.base_test_case import BaseTestCase


class TestProductDeleteActions(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.api_client = APIClient()
        self.owner = User.objects.create(username="delete_owner@example.com")
        self.maintainer = User.objects.create(username="delete_maintainer@example.com")

    def tearDown(self) -> None:
        global_request._requests.clear()  # pylint: disable=protected-access
        super().tearDown()

    def test_product_creator_can_force_delete_product(self):
        self.api_client.force_authenticate(user=self.owner)
        create_response = self.api_client.post("/api/products/", {"name": "delete_me"}, format="json")
        self.assertEqual(201, create_response.status_code, create_response.data)

        product_id = create_response.data["id"]
        self.assertTrue(
            Product_Member.objects.filter(product_id=product_id, user=self.owner, role=Roles.Owner).exists()
        )

        delete_response = self.api_client.post(
            f"/api/products/{product_id}/force_delete/",
            {"confirmation_name": "delete_me"},
            format="json",
        )

        self.assertEqual(204, delete_response.status_code, delete_response.data)
        self.assertFalse(Product.objects.filter(pk=product_id).exists())

    def test_product_group_owner_can_force_delete_product_group(self):
        self.api_client.force_authenticate(user=self.owner)
        create_response = self.api_client.post("/api/product_groups/", {"name": "delete_group"}, format="json")
        self.assertEqual(201, create_response.status_code, create_response.data)

        product_group_id = create_response.data["id"]
        self.assertTrue(
            Product_Member.objects.filter(product_id=product_group_id, user=self.owner, role=Roles.Owner).exists()
        )

        delete_response = self.api_client.post(
            f"/api/product_groups/{product_group_id}/force_delete/",
            {"confirmation_name": "delete_group"},
            format="json",
        )

        self.assertEqual(204, delete_response.status_code, delete_response.data)
        self.assertFalse(Product.objects.filter(pk=product_group_id).exists())

    def test_product_maintainer_can_request_delete(self):
        product = Product.objects.create(name="request_delete_me")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)

        self.api_client.force_authenticate(user=self.maintainer)
        delete_response = self.api_client.post(f"/api/products/{product.pk}/request_delete/", {}, format="json")

        self.assertEqual(201, delete_response.status_code, delete_response.data)
        self.assertTrue(Product_Delete_Request.objects.filter(product=product, user=self.maintainer).exists())

    def test_product_maintainer_can_undo_own_delete_request(self):
        product = Product.objects.create(name="undo_request_delete_me")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        Product_Delete_Request.objects.create(product=product, user=self.maintainer)

        self.api_client.force_authenticate(user=self.maintainer)
        undo_response = self.api_client.post(f"/api/products/{product.pk}/undo_delete_request/", {}, format="json")

        self.assertEqual(204, undo_response.status_code, undo_response.data)
        self.assertFalse(Product_Delete_Request.objects.filter(product=product).exists())

    def test_product_maintainer_cannot_undo_other_user_delete_request(self):
        other_maintainer = User.objects.create(username="delete_other_maintainer@example.com")
        product = Product.objects.create(name="undo_other_request_delete_me")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        Product_Member.objects.create(product=product, user=other_maintainer, role=Roles.Maintainer)
        Product_Delete_Request.objects.create(product=product, user=other_maintainer)

        self.api_client.force_authenticate(user=self.maintainer)
        undo_response = self.api_client.post(f"/api/products/{product.pk}/undo_delete_request/", {}, format="json")

        self.assertEqual(403, undo_response.status_code, undo_response.data)
        self.assertTrue(Product_Delete_Request.objects.filter(product=product, user=other_maintainer).exists())
