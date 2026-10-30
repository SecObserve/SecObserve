from datetime import datetime, timezone

from application.core.models import Product
from application.scancodeio.models import ScanCodeIO_Project
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)


class TestAuthorizationScanCodeIOProjects(TestAuthorizationBase):
    def setUp(self):
        super().setUp()
        ScanCodeIO_Project.objects.create(
            pk=1,
            product=Product.objects.get(pk=1),
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685",
            project_name="project_internal",
            webhook_token_hash="webhook_token_hash_internal",
        )
        ScanCodeIO_Project.objects.create(
            pk=2,
            product=Product.objects.get(pk=2),
            project_uuid="7cbd4e4a-2a1c-4a50-9a4e-2d8f8a8c1f3b",
            project_name="project_external",
            webhook_token_hash="webhook_token_hash_external",
        )
        ScanCodeIO_Project.objects.update(created=datetime(2026, 10, 23, 12, 0, 0, tzinfo=timezone.utc))

    def test_authorization_scancodeio_projects_product_member(self):
        self._test_authorization_scancodeio_projects()

    def test_authorization_scancodeio_projects_product_authorization_group_member(self):
        prepare_authorization_groups()
        self._test_authorization_scancodeio_projects()

    def _test_authorization_scancodeio_projects(self):
        project_internal = "{'id': 1, 'product': 1, 'project_uuid': '6461408c-726c-4b70-aa7a-c9cc9d1c9685', 'project_name': 'project_internal', 'created': '2026-10-23T14:00:00+02:00'}"
        project_external = "{'id': 2, 'product': 2, 'project_uuid': '7cbd4e4a-2a1c-4a50-9a4e-2d8f8a8c1f3b', 'project_name': 'project_external', 'created': '2026-10-23T14:00:00+02:00'}"

        expected_data = (
            f"{{'count': 2, 'next': None, 'previous': None, 'results': [{project_internal}, {project_external}]}}"
        )
        self._test_api(APITest("db_admin", "get", "/api/scancodeio_projects/", None, 200, expected_data))

        expected_data = f"{{'count': 1, 'next': None, 'previous': None, 'results': [{project_internal}]}}"
        self._test_api(APITest("db_internal_write", "get", "/api/scancodeio_projects/", None, 200, expected_data))
        self._test_api(
            APITest("db_internal_write", "get", "/api/scancodeio_projects/?product=1", None, 200, expected_data)
        )

        expected_data = "{'count': 0, 'next': None, 'previous': None, 'results': []}"
        self._test_api(
            APITest("db_internal_write", "get", "/api/scancodeio_projects/?product=2", None, 200, expected_data)
        )

        self._test_api(APITest("db_internal_write", "get", "/api/scancodeio_projects/1/", None, 200, project_internal))

        expected_data = "{'message': 'No ScanCodeIO_Project matches the given query.'}"
        self._test_api(APITest("db_internal_write", "get", "/api/scancodeio_projects/2/", None, 404, expected_data))
        self._test_api(APITest("db_internal_write", "get", "/api/scancodeio_projects/99999/", None, 404, expected_data))
