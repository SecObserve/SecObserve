from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient

from application.access_control.models import User
from application.commons.models import Settings
from application.core.models import Product
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.services.scancodeio import hash_webhook_token
from application.scancodeio.types import CreateProjectParameters
from unittests.base_test_case import BaseTestCase

PROJECT_UUID = "6461408c-726c-4b70-aa7a-c9cc9d1c9685"
INPUT_URLS = [
    "https://example.com/a.zip",
    "docker://ghcr.io/secobserve/secobserve-backend:1.62.2",
    "https://github.com/secobserve/secobserve.git",
    "pkg:pypi/django@5.0",
]


class ScanCodeIOViewTestCase(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpTestData(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
            ],
        )

    def setUp(self):
        super().setUp()
        # Patches are started here instead of decorating the class, because other test classes
        # change patch.TEST_PREFIX, which would make class decorators patch setUpTestData as well.
        self.mock_authenticate = self._start_patch(
            "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        )
        self.mock_settings_load = self._start_patch("application.scancodeio.api.views.Settings.load")

    def _start_patch(self, target: str) -> MagicMock:
        patcher = patch(target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _api_client(self, username: str) -> APIClient:
        self.mock_authenticate.return_value = User.objects.get(username=username), None
        return APIClient()

    def _create_projects(self) -> None:
        ScanCodeIO_Project.objects.create(
            pk=1,
            product=Product.objects.get(pk=1),
            project_uuid=PROJECT_UUID,
            project_name="project_internal",
            webhook_token_hash=hash_webhook_token("webhook_token_internal"),
        )
        ScanCodeIO_Project.objects.create(
            pk=2,
            product=Product.objects.get(pk=2),
            project_uuid="7cbd4e4a-2a1c-4a50-9a4e-2d8f8a8c1f3b",
            project_name="project_external",
            webhook_token_hash=hash_webhook_token("webhook_token_external"),
        )


class TestCreateScanCodeIOProjectView(ScanCodeIOViewTestCase):
    def setUp(self):
        super().setUp()
        self.mock_create = self._start_patch("application.scancodeio.api.views.create_scancodeio_project")

    def _post(self, username: str, product_id: int, data: dict):
        return self._api_client(username).post(f"/api/products/{product_id}/create_scancodeio_project/", data)

    def test_product_not_found(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_admin", 99999, {"name": "project_name"})

        self.assertEqual(response.status_code, 404)
        self.mock_create.assert_not_called()

    def test_no_permission(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_internal_read", 1, {"name": "project_name"})

        self.assertEqual(response.status_code, 403)
        self.mock_create.assert_not_called()

    def test_feature_disabled(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._post("db_internal_write", 1, {"name": "project_name"})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data), "{'message': 'ScanCode.io integration is not enabled'}")
        self.mock_create.assert_not_called()

    def test_invalid_data(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_internal_write", 1, {"input_urls": ["no_url"]})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                "message": "Name: This field is required.\n"
                + "Input urls (entry 1): Enter an http(s) URL, a Docker reference (docker://), "
                + "a Git repository (.git) or a package URL (pkg:).\n"
                + "Pipeline: This field is required."
            },
        )
        self.mock_create.assert_not_called()

    def test_invalid_input_urls(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post(
            "db_internal_write",
            1,
            {
                "name": "project_name",
                "input_urls": ["docker://bad reference!", "pkg:invalid", "git@github.com:x/y.git"],
                "pipeline": "scan_codebase",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                "message": "Input urls (entry 1): Invalid Docker reference.\n"
                + "Input urls (entry 2): Invalid package URL.\n"
                + "Input urls (entry 3): SSH URLs are not supported, use https:// instead."
            },
        )
        self.mock_create.assert_not_called()

    def test_success(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        product = Product.objects.get(pk=1)
        self.mock_create.return_value = ScanCodeIO_Project(
            product=product, project_uuid=PROJECT_UUID, project_name="project_name"
        )
        upload_file = SimpleUploadedFile("archive.zip", b"content")

        response = self._post(
            "db_internal_write",
            1,
            {
                "name": "project_name",
                "input_urls": INPUT_URLS,
                "upload_file": upload_file,
                "pipeline": "scan_codebase",
                "execute_now": "true",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["project_uuid"], PROJECT_UUID)
        self.assertEqual(response.data["project_name"], "project_name")
        self.mock_create.assert_called_once()
        self.assertEqual(self.mock_create.call_args.args[0], product)
        parameters: CreateProjectParameters = self.mock_create.call_args.args[1]
        self.assertEqual(parameters.name, "project_name")
        self.assertEqual(parameters.input_urls, INPUT_URLS)
        self.assertEqual(parameters.upload_file.name, "archive.zip")
        self.assertEqual(parameters.pipeline, "scan_codebase")
        self.assertTrue(parameters.execute_now)


class TestScanCodeIOPipelinesView(ScanCodeIOViewTestCase):
    def setUp(self):
        super().setUp()
        self.mock_get_pipelines = self._start_patch("application.scancodeio.api.views.get_scancodeio_pipelines")

    def test_feature_disabled(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._api_client("db_internal_read").get("/api/scancodeio/pipelines/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data), "{'message': 'ScanCode.io integration is not enabled'}")
        self.mock_get_pipelines.assert_not_called()

    def test_pipelines(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        self.mock_get_pipelines.return_value = [{"name": "scan_codebase", "summary": "Scan a codebase."}]

        response = self._api_client("db_internal_read").get("/api/scancodeio/pipelines/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{"name": "scan_codebase", "summary": "Scan a codebase."}])


class TestScanCodeIOProjectDetailsView(ScanCodeIOViewTestCase):
    def setUp(self):
        super().setUp()
        self.mock_get_details = self._start_patch("application.scancodeio.api.views.get_scancodeio_project_details")
        self._create_projects()

    def test_feature_disabled(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._api_client("db_internal_read").get("/api/scancodeio_projects/1/details/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data), "{'message': 'ScanCode.io integration is not enabled'}")
        self.mock_get_details.assert_not_called()

    def test_feature_disabled_before_object_lookup(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._api_client("db_internal_read").get("/api/scancodeio_projects/99999/details/")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data), "{'message': 'ScanCode.io integration is not enabled'}")

    def test_not_authorized(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._api_client("db_internal_write").get("/api/scancodeio_projects/2/details/")

        self.assertEqual(response.status_code, 404)
        self.mock_get_details.assert_not_called()

    def test_details(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        self.mock_get_details.return_value = {
            "name": "project_internal",
            "uuid": PROJECT_UUID,
            "created_date": "2026-10-24T08:43:06.058350+02:00",
            "input_root": "/var/scancodeio/workspace/projects/project_internal/input",
            "input_sources": [
                {
                    "filename": "a.zip",
                    "download_url": "https://example.com/a.zip",
                    "is_uploaded": False,
                    "uuid": "1d5b4a40-6a05-4b53-b2c3-8c8f3b0bc8b1",
                }
            ],
            "runs": [
                {
                    "pipeline_name": "scan_codebase",
                    "status": "success",
                    "task_start_date": "2026-10-24T08:43:07.000000+02:00",
                    "task_end_date": "2026-10-24T08:45:07.000000+02:00",
                    "execution_time": 120,
                    "log": "very long log",
                }
            ],
            "message_count": 1,
            "resource_count": 2,
            "package_count": 3,
            "dependency_count": 4,
            "relation_count": 5,
            "ui_url": "http://localhost:4100/project/project_internal-6461408c/",
        }

        response = self._api_client("db_internal_read").get("/api/scancodeio_projects/1/details/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "name": "project_internal",
                "uuid": PROJECT_UUID,
                "created_date": "2026-10-24T08:43:06.058350+02:00",
                "input_sources": [
                    {"filename": "a.zip", "download_url": "https://example.com/a.zip", "is_uploaded": False}
                ],
                "runs": [
                    {
                        "pipeline_name": "scan_codebase",
                        "status": "success",
                        "task_start_date": "2026-10-24T08:43:07.000000+02:00",
                        "task_end_date": "2026-10-24T08:45:07.000000+02:00",
                        "execution_time": 120,
                    }
                ],
                "message_count": 1,
                "resource_count": 2,
                "package_count": 3,
                "dependency_count": 4,
                "relation_count": 5,
                "ui_url": "http://localhost:4100/project/project_internal-6461408c/",
            },
        )
        self.mock_get_details.assert_called_once_with(ScanCodeIO_Project.objects.get(pk=1))


class TestScanCodeIOProjectDeleteView(ScanCodeIOViewTestCase):
    def setUp(self):
        super().setUp()
        self.mock_delete = self._start_patch("application.scancodeio.api.views.delete_scancodeio_project")
        self._create_projects()

    def _delete(self, username: str, project_id: int, query: str = ""):
        return self._api_client(username).delete(f"/api/scancodeio_projects/{project_id}/{query}")

    def test_wrong_name(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._delete("db_internal_write", 1, "?name=wrong")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"message": "Name: Confirmation name must match the project name."})
        self.mock_delete.assert_not_called()

    def test_missing_name(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._delete("db_internal_write", 1)

        self.assertEqual(response.status_code, 400)
        self.mock_delete.assert_not_called()

    def test_no_permission(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._delete("db_internal_read", 1, "?name=project_internal")

        self.assertEqual(response.status_code, 403)
        self.mock_delete.assert_not_called()

    def test_not_authorized(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._delete("db_internal_write", 2, "?name=project_external")

        self.assertEqual(response.status_code, 404)
        self.mock_delete.assert_not_called()

    def test_feature_disabled(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._delete("db_internal_write", 1, "?name=project_internal")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data), "{'message': 'ScanCode.io integration is not enabled'}")
        self.mock_delete.assert_not_called()

    def test_delete(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._delete("db_internal_write", 1, "?name=project_internal")

        self.assertEqual(response.status_code, 204)
        self.mock_delete.assert_called_once_with(ScanCodeIO_Project.objects.get(pk=1))


class TestScanCodeIOWebhookView(ScanCodeIOViewTestCase):
    def setUp(self):
        super().setUp()
        self.mock_process = self._start_patch("application.scancodeio.api.views.process_scancodeio_webhook")
        ScanCodeIO_Project.objects.create(
            pk=1,
            product=Product.objects.get(pk=1),
            project_uuid=PROJECT_UUID,
            project_name="project_internal",
            webhook_token_hash=hash_webhook_token("webhook_token"),
        )
        self.payload = {
            "project": {"uuid": PROJECT_UUID, "name": "project_internal"},
            "run": {"pipeline_name": "scan_codebase", "status": "success"},
        }

    def _post_webhook(self, token: str, payload: dict):
        # ScanCode.io doesn't authenticate, so no user is set
        return APIClient().post(f"/api/scancodeio/webhook/{token}/", payload, format="json")

    def test_webhook(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post_webhook("webhook_token", self.payload)

        self.assertEqual(response.status_code, 200)
        self.mock_process.assert_called_once_with(ScanCodeIO_Project.objects.get(pk=1), self.payload)
        self.mock_authenticate.assert_not_called()

    def test_unknown_token(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post_webhook("unknown_token", self.payload)

        self.assertEqual(response.status_code, 404)
        self.mock_process.assert_not_called()

    def test_wrong_project(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        self.payload["project"]["uuid"] = "7cbd4e4a-2a1c-4a50-9a4e-2d8f8a8c1f3b"

        response = self._post_webhook("webhook_token", self.payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"message": "Webhook payload doesn't belong to the ScanCode.io project"})
        self.mock_process.assert_not_called()

    def test_feature_disabled(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._post_webhook("webhook_token", self.payload)

        # Same response as for an unknown token
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(response.data)
        self.mock_process.assert_not_called()
