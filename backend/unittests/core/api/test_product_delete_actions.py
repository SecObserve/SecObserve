from urllib.parse import urlencode

from django.utils import timezone
from rest_framework.test import APIClient

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.commons.services import global_request
from application.core.models import Observation, Product, Product_Member
from application.core.types import Status
from application.import_observations.models import Parser
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from unittests.base_test_case import BaseTestCase


class TestProductDeleteActions(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.api_client = APIClient()
        self.owner = User.objects.create(username="delete_owner@example.com")
        self.maintainer = User.objects.create(username="delete_maintainer@example.com")
        self.unrelated_user = User.objects.create(username="delete_unrelated@example.com")
        self.parser = Parser.objects.create(name="delete_parser")

    def tearDown(self) -> None:
        global_request._requests.clear()  # pylint: disable=protected-access
        super().tearDown()

    def test_product_owner_can_confirm_cascade_delete(self) -> None:
        product = self._create_product_with_blockers("Delete Me & + Confirm – 安全")
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.owner)

        response = self.api_client.delete(self._delete_url("products", product.pk, product.name))

        self.assertEqual(204, response.status_code, response.data)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertFalse(Observation.objects.filter(product_id=product.pk).exists())
        self.assertFalse(License_Component.objects.filter(product_id=product.pk).exists())

    def test_product_group_owner_can_confirm_cascade_delete(self) -> None:
        product_group = Product.objects.create(name="delete_group", is_product_group=True)
        child = self._create_product_with_blockers("delete_child", product_group)
        Product_Member.objects.create(product=product_group, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.owner)

        response = self.api_client.delete(self._delete_url("product_groups", product_group.pk, "delete_group"))

        self.assertEqual(204, response.status_code, response.data)
        self.assertFalse(Product.objects.filter(pk__in=[product_group.pk, child.pk]).exists())
        self.assertFalse(Observation.objects.filter(product_id=child.pk).exists())
        self.assertFalse(License_Component.objects.filter(product_id=child.pk).exists())

    def test_confirmation_name_query_parameter_is_required(self) -> None:
        product = Product.objects.create(name="delete_me")
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.owner)

        for payload in (None, {"name": "delete_me"}):
            with self.subTest(payload=payload):
                response = (
                    self.api_client.delete(f"/api/products/{product.pk}/")
                    if payload is None
                    else self.api_client.delete(f"/api/products/{product.pk}/", payload, format="json")
                )

                self.assertEqual(400, response.status_code, response.data)
                self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_invalid_confirmation_names_do_not_delete_product(self) -> None:
        product = Product.objects.create(name="Exact Product")
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.owner)

        for confirmation_name in ("", "exact product", " Exact Product", "Exact Product ", "x" * 256):
            with self.subTest(confirmation_name=confirmation_name):
                response = self.api_client.delete(self._delete_url("products", product.pk, confirmation_name))

                self.assertEqual(400, response.status_code, response.data)
                self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_multiple_confirmation_names_do_not_delete_product(self) -> None:
        product = Product.objects.create(name="Exact Product")
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.owner)

        response = self.api_client.delete(
            f"/api/products/{product.pk}/?{urlencode([('name', product.name), ('name', product.name)])}"
        )

        self.assertEqual(400, response.status_code, response.data)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_user_without_delete_permission_is_rejected_before_confirmation_validation(self) -> None:
        product = Product.objects.create(name="delete_me")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        self.api_client.force_authenticate(user=self.maintainer)

        response = self.api_client.delete(f"/api/products/{product.pk}/")

        self.assertEqual(403, response.status_code, response.data)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_product_group_user_without_delete_permission_is_rejected(self) -> None:
        product_group = Product.objects.create(name="delete_group", is_product_group=True)
        Product_Member.objects.create(product=product_group, user=self.maintainer, role=Roles.Maintainer)
        self.api_client.force_authenticate(user=self.maintainer)

        response = self.api_client.delete(self._delete_url("product_groups", product_group.pk, "delete_group"))

        self.assertEqual(403, response.status_code, response.data)
        self.assertTrue(Product.objects.filter(pk=product_group.pk).exists())

    def test_unrelated_user_cannot_use_confirmation_validation_as_object_oracle(self) -> None:
        product = Product.objects.create(name="private_product")
        product_group = Product.objects.create(name="private_group", is_product_group=True)
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        Product_Member.objects.create(product=product_group, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.unrelated_user)

        for resource, object_id in (("products", product.pk), ("product_groups", product_group.pk)):
            with self.subTest(resource=resource):
                response = self.api_client.delete(f"/api/{resource}/{object_id}/")

                self.assertEqual(404, response.status_code, response.data)

        self.assertEqual(2, Product.objects.filter(pk__in=[product.pk, product_group.pk]).count())

    def test_missing_confirmation_does_not_delete_product_without_dependents(self) -> None:
        product = Product.objects.create(name="confirmation_required")
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.owner)

        response = self.api_client.delete(f"/api/products/{product.pk}/")

        self.assertEqual(400, response.status_code, response.data)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

    def test_missing_confirmation_does_not_delete_product_with_dependents(self) -> None:
        product = self._create_product_with_blockers("confirmation_required_with_dependents")
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        self.api_client.force_authenticate(user=self.owner)

        response = self.api_client.delete(f"/api/products/{product.pk}/")

        self.assertEqual(400, response.status_code, response.data)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
        self.assertTrue(Observation.objects.filter(product=product).exists())
        self.assertTrue(License_Component.objects.filter(product=product).exists())

    def test_openapi_documents_confirmation_query_parameter_and_responses(self) -> None:
        response = self.api_client.get("/api/oa3/schema/?format=json")

        self.assertEqual(200, response.status_code, response.data)
        for path in ("/api/products/{id}/", "/api/product_groups/{id}/"):
            operation = response.data["paths"][path]["delete"]
            name_parameter = next(parameter for parameter in operation["parameters"] if parameter["name"] == "name")
            self.assertEqual("query", name_parameter["in"])
            self.assertTrue(name_parameter["required"])
            self.assertNotIn("requestBody", operation)
            self.assertTrue({"204", "400", "403", "409"}.issubset(operation["responses"]))

    @staticmethod
    def _delete_url(resource: str, object_id: int, name: str) -> str:
        return f"/api/{resource}/{object_id}/?{urlencode({'name': name})}"

    def _create_product_with_blockers(self, name: str, product_group: Product | None = None) -> Product:
        product = Product.objects.create(name=name, product_group=product_group)
        Observation.objects.create(
            title=f"{name}_observation",
            product=product,
            parser=self.parser,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )
        License_Component.objects.create(
            identity_hash=f"{name}_license_component",
            product=product,
            component_name=f"{name}_component",
            component_name_version=f"{name}_component:1.0.0",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            numerical_evaluation_result=License_Policy_Evaluation_Result.NUMERICAL_RESULTS[
                License_Policy_Evaluation_Result.RESULT_UNKNOWN
            ],
        )
        return product
