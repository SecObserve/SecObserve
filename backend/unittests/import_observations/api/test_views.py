from dataclasses import dataclass
from os import path
from unittest.mock import ANY, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Branch, Product, Service
from application.import_observations.services.import_observations import (
    FileUploadParameters,
)
from unittests.base_test_case import BaseTestCase


@dataclass
class APITest:
    username: str
    url: str
    post_data: str
    expected_status_code: int
    expected_data: str


class TestImport(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(self, mock_user):
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

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.import_observations.api.views.file_upload_observations")
    def _test_api(self, data: APITest, mock_file_upload_observations, mock_authenticate):
        user = User.objects.get(username=data.username)
        mock_authenticate.return_value = user, None
        mock_file_upload_observations.return_value = 1, 2, 3, 4, 5, 6

        with open(path.dirname(__file__) + "/test_views.py", "rb") as file:
            uploaded_file = SimpleUploadedFile("file.txt", file.read(), content_type="multipart/form-data")

            post_data = {
                "file": uploaded_file,
            }
            post_data.update(data.post_data)

            api_client = APIClient()
            response = api_client.post(data.url, post_data)

            self.assertEqual(response.status_code, data.expected_status_code)
            self.assertEqual(response.data, data.expected_data)

            if response.status_code != 200:
                mock_file_upload_observations.assert_not_called()
            else:
                if data.post_data.get("product"):
                    product = Product.objects.get(id=data.post_data.get("product"))
                else:
                    product = Product.objects.get(name=data.post_data.get("product_name"))
                if data.post_data.get("branch"):
                    branch = Branch.objects.get(id=data.post_data.get("branch"))
                else:
                    branch = Branch.objects.get(product=product.pk, name=data.post_data.get("branch_name"))
                service_name = ""
                if data.post_data.get("service_id"):
                    service_name = Service.objects.get(id=data.post_data.get("service_id")).name
                elif data.post_data.get("service"):
                    service_name = data.post_data.get("service")
                sbom = "sbom" in data.url
                mock_file_upload_observations.assert_called_once_with(
                    FileUploadParameters(
                        product=product,
                        branch=branch,
                        file=ANY,
                        service_name=service_name,
                        docker_image_name_tag=data.post_data.get("docker_image_name_tag", ""),
                        endpoint_url=data.post_data.get("endpoint_url", ""),
                        kubernetes_cluster=data.post_data.get("kubernetes_cluster", ""),
                        suppress_licenses=data.post_data.get("suppress_licenses", False),
                        sbom=sbom,
                    )
                )

    def test_file_upload_observations_by_id_no_product(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_observations_by_id/",
            post_data={},
            expected_status_code=400,
            expected_data={"message": "Product: This field is required."},
        )
        self._test_api(data)

    def test_file_upload_observations_by_id_product_not_found(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_observations_by_id/",
            post_data={
                "product": 99999,
            },
            expected_status_code=400,
            expected_data={"message": "Product 99999 does not exist"},
        )
        self._test_api(data)

    def test_file_upload_observations_by_id_no_permission(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_observations_by_id/",
            post_data={
                "product": 1,
            },
            expected_status_code=403,
            expected_data={"message": "You do not have permission to perform this action."},
        )
        self._test_api(data)

    def test_file_upload_observations_by_id_branch_not_found(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_observations_by_id/",
            post_data={
                "product": 1,
                "branch": 3,
            },
            expected_status_code=400,
            expected_data={"message": "Branch 3 does not exist for product db_product_internal"},
        )
        self._test_api(data)

    def test_file_upload_observations_by_id_service_not_found(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_observations_by_id/",
            post_data={
                "product": 1,
                "service_id": 3,
            },
            expected_status_code=400,
            expected_data={"message": "Service 3 does not exist for product db_product_internal"},
        )
        self._test_api(data)

    def test_file_upload_observations_by_id_service_name_successful(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_observations_by_id/",
            post_data={
                "product": 1,
                "branch": 1,
                "service": "service_name",
                "docker_image_name_tag": "docker_image_name_tag",
                "endpoint_url": "endpoint_url",
                "kubernetes_cluster": "kubernetes_cluster",
                "suppress_licenses": True,
            },
            expected_status_code=200,
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
                "observations_new": 1,
                "observations_resolved": 3,
                "observations_updated": 2,
            },
        )
        self._test_api(data)

    def test_file_upload_observations_by_id_service_id_successful(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_observations_by_id/",
            post_data={
                "product": 1,
                "branch": 1,
                "service_id": 1,
                "docker_image_name_tag": "docker_image_name_tag",
                "endpoint_url": "endpoint_url",
                "kubernetes_cluster": "kubernetes_cluster",
                "suppress_licenses": True,
            },
            expected_status_code=200,
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
                "observations_new": 1,
                "observations_resolved": 3,
                "observations_updated": 2,
            },
        )
        self._test_api(data)

    def test_file_upload_observations_by_name_no_product(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_observations_by_name/",
            post_data={},
            expected_status_code=400,
            expected_data={"message": "Product name: This field is required."},
        )
        self._test_api(data)

    def test_file_upload_observations_by_name_product_not_found(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_observations_by_name/",
            post_data={
                "product_name": "Unknown Product",
            },
            expected_status_code=400,
            expected_data={"message": "Product Unknown Product does not exist"},
        )
        self._test_api(data)

    def test_file_upload_observations_by_name_no_permission(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_observations_by_name/",
            post_data={
                "product_name": "db_product_internal",
            },
            expected_status_code=403,
            expected_data={"message": "You do not have permission to perform this action."},
        )
        self._test_api(data)

    def test_file_upload_observations_by_name_branch_not_found(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_observations_by_name/",
            post_data={
                "product_name": "db_product_internal",
                "branch_name": "Unknown Branch",
                "service": "service_name",
                "docker_image_name_tag": "docker_image_name_tag",
                "endpoint_url": "endpoint_url",
                "kubernetes_cluster": "kubernetes_cluster",
                "suppress_licenses": True,
            },
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
                "observations_new": 1,
                "observations_resolved": 3,
                "observations_updated": 2,
            },
            expected_status_code=200,
        )
        self._test_api(data)

        product = Product.objects.get(name="db_product_internal")
        branch = (Branch.objects.get(product=product.pk, name="db_branch_internal_dev"),)

    def test_file_upload_observations_by_name_successful(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_observations_by_name/",
            post_data={
                "product_name": "db_product_internal",
                "branch_name": "db_branch_internal_dev",
                "service": "service_name",
                "docker_image_name_tag": "docker_image_name_tag",
                "endpoint_url": "endpoint_url",
                "kubernetes_cluster": "kubernetes_cluster",
                "suppress_licenses": True,
            },
            expected_status_code=200,
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
                "observations_new": 1,
                "observations_resolved": 3,
                "observations_updated": 2,
            },
        )
        self._test_api(data)

    def test_file_upload_sbom_by_id_no_product(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_sbom_by_id/",
            post_data={},
            expected_status_code=400,
            expected_data={"message": "Product: This field is required."},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_id_product_not_found(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_sbom_by_id/",
            post_data={
                "product": 99999,
            },
            expected_status_code=400,
            expected_data={"message": "Product 99999 does not exist"},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_id_no_permission(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_sbom_by_id/",
            post_data={
                "product": 1,
            },
            expected_status_code=403,
            expected_data={"message": "You do not have permission to perform this action."},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_id_branch_not_found(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_sbom_by_id/",
            post_data={
                "product": 1,
                "branch": 3,
            },
            expected_status_code=400,
            expected_data={"message": "Branch 3 does not exist for product db_product_internal"},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_id_service_not_found(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_sbom_by_id/",
            post_data={
                "product": 1,
                "service_id": 3,
            },
            expected_status_code=400,
            expected_data={"message": "Service 3 does not exist for product db_product_internal"},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_id_service_name_successful(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_sbom_by_id/",
            post_data={
                "product": 1,
                "branch": 1,
                "service": "service_name",
            },
            expected_status_code=200,
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
            },
        )
        self._test_api(data)

    def test_file_upload_sbom_by_id_service_id_successful(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_sbom_by_id/",
            post_data={"product": 1, "branch": 1, "service_id": 1},
            expected_status_code=200,
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
            },
        )
        self._test_api(data)

    def test_file_upload_sbom_by_name_no_product(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_sbom_by_name/",
            post_data={},
            expected_status_code=400,
            expected_data={"message": "Product name: This field is required."},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_name_product_not_found(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_sbom_by_name/",
            post_data={
                "product_name": "Unknown Product",
            },
            expected_status_code=400,
            expected_data={"message": "Product Unknown Product does not exist"},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_name_no_permission(self):
        data = APITest(
            username="db_internal_read",
            url="/api/import/file_upload_sbom_by_name/",
            post_data={
                "product_name": "db_product_internal",
            },
            expected_status_code=403,
            expected_data={"message": "You do not have permission to perform this action."},
        )
        self._test_api(data)

    def test_file_upload_sbom_by_name_branch_not_found(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_sbom_by_name/",
            post_data={
                "product_name": "db_product_internal",
                "branch_name": "Unknown Branch",
            },
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
            },
            expected_status_code=200,
        )
        self._test_api(data)

        product = Product.objects.get(name="db_product_internal")
        branch = (Branch.objects.get(product=product.pk, name="db_branch_internal_dev"),)

    def test_file_upload_sbom_by_name_successful(self):
        data = APITest(
            username="db_internal_write",
            url="/api/import/file_upload_sbom_by_name/",
            post_data={
                "product_name": "db_product_internal",
                "branch_name": "db_branch_internal_dev",
            },
            expected_status_code=200,
            expected_data={
                "license_components_deleted": 6,
                "license_components_new": 4,
                "license_components_updated": 5,
            },
        )
        self._test_api(data)
