from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from application.access_control.models import User
from application.commons.models import Settings
from application.core.models import Branch, Product, Service
from application.licenses.models import License_Component
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.services.scancodeio import hash_webhook_token
from application.scancodeio.services.scancodeio_import import SCANCODEIO_FILENAME
from application.scancodeio.types import CreateProjectParameters
from unittests.base_test_case import BaseTestCase

PROJECT_UUID = "6461408c-726c-4b70-aa7a-c9cc9d1c9685"
INPUT_URLS = [
    "https://example.com/a.zip",
    "docker://ghcr.io/secobserve/secobserve-backend:1.64.0",
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
                "message": "Input urls (entry 1): Enter an http(s) URL, a Docker reference (docker://), "
                + "a Git repository (.git) or a package URL (pkg:).\n"
                + "Pipeline: This field is required."
            },
        )
        self.mock_create.assert_not_called()

    def test_name_too_long(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post(
            "db_internal_write", 1, {"name": "n" * 101, "input_urls": INPUT_URLS, "pipeline": "scan_codebase"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"message": "Name: Ensure this field has no more than 100 characters."})
        self.mock_create.assert_not_called()

    def test_branch_and_service(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        branch = Branch.objects.get(pk=1)
        service = Service.objects.get(pk=2)
        self.mock_create.return_value = ScanCodeIO_Project(
            pk=1,
            product=Product.objects.get(pk=1),
            branch=branch,
            service=service,
            project_uuid=PROJECT_UUID,
            project_name="project_name",
        )

        response = self._post(
            "db_internal_write",
            1,
            {"branch": 1, "service": 2, "input_urls": INPUT_URLS, "pipeline": "scan_codebase"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["branch"], 1)
        self.assertEqual(response.data["branch_name"], "db_branch_internal_dev")
        self.assertEqual(response.data["service"], 2)
        self.assertEqual(response.data["service_name"], "db_service_internal_frontend")
        self.assertEqual(self.mock_create.call_args.args[1], branch)
        self.assertEqual(self.mock_create.call_args.args[2], service)
        self.assertEqual(self.mock_create.call_args.args[3].name, "")

    def test_branch_of_other_product(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post(
            "db_internal_write", 1, {"branch": 3, "input_urls": INPUT_URLS, "pipeline": "scan_codebase"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"message": "Branch 3 does not exist for product db_product_internal"})
        self.mock_create.assert_not_called()

    def test_service_of_other_product(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post(
            "db_internal_write", 1, {"service": 3, "input_urls": INPUT_URLS, "pipeline": "scan_codebase"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"message": "Service 3 does not exist for product db_product_internal"})
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

    def _assert_input_url_rejected(self, input_url: str, message: str) -> None:
        response = self._post(
            "db_internal_write", 1, {"name": "project_name", "input_urls": [input_url], "pipeline": "scan_codebase"}
        )

        self.assertEqual(response.status_code, 400, input_url)
        self.assertEqual(response.data, {"message": f"Input urls (entry 1): {message}"}, input_url)
        self.mock_create.assert_not_called()

    def test_input_urls_with_internal_address(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        for input_url in [
            "http://127.0.0.1:8000/a.zip",
            "http://localhost:8000/a.zip",
            "http://foo.localhost/a.zip",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]:8000/a.zip",
            "http://[::ffff:127.0.0.1]/a.git",
            "http://[::ffff:169.254.169.254]/a.zip",
            "http://[fe80::1]/a.zip",
            "http://224.0.0.1/a.zip",
            "http://0.0.0.0/a.zip",
            "http://240.0.0.1/a.zip",
            "docker://127.0.0.1:5000/image:1.0",
            "docker://localhost:5000/image:1.0",
            "docker://169.254.169.254/image",
            "docker://user:password@127.0.0.1:5000/image",
            "pkg:generic/a@1.0?download_url=http://169.254.169.254/a.zip",
            "pkg:generic/a@1.0?download_url=http%3A%2F%2F127.0.0.1%2Fa.zip",
        ]:
            self._assert_input_url_rejected(
                input_url, "Loopback, link-local and other non-routable addresses are not allowed."
            )

    def test_input_urls_with_credentials(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        for input_url in [
            "https://user:token@github.com/secobserve/secobserve.git",
            "https://token@github.com/secobserve/secobserve.git",
            # The parsers don't agree on the host of this URL
            "http://127.0.0.1\\@example.com/a.git",
            "pkg:generic/a@1.0?download_url=https://user:token@example.com/a.zip",
        ]:
            self._assert_input_url_rejected(input_url, "URLs with credentials are not supported.")

    def test_input_urls_with_whitespace_in_package_url(self):
        # ScanCode.io splits at whitespace, and the parts behind it would be fetched without having been checked
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        for input_url in [
            "pkg:pypi/django@5.0 file:///var/data/secret.git",
            "pkg:pypi/django@5.0 git://10.0.0.1/repository.git",
            "pkg:pypi/django@5.0 /var/data/secret.git",
            "pkg:pypi/django@5.0\nfile:///var/data/secret.git",
            "pkg:pypi/django@5.0\tfile:///var/data/secret.git",
            "pkg:pypi/django@5.0\u00a0file:///var/data/secret.git",
            "pkg:pypi/django@5.0?a=b file:///var/data/secret.git",
            "pkg:pypi/django@5.0#a file:///var/data/secret.git",
        ]:
            self._assert_input_url_rejected(input_url, "Invalid package URL.")

    def test_input_urls_with_invalid_scheme(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        for input_url in [
            "file:///var/data/secret.git",
            "git://example.com/repository.git",
            "/var/data/secret.git",
            # ScanCode.io checks URLs for internal addresses only if they start with a lower case http
            "HTTP://example.com/repository.git",
            "Https://example.com/a.zip",
            "pkg:generic/a@1.0?download_url=file:///var/data/secret.git",
        ]:
            self._assert_input_url_rejected(
                input_url,
                "Enter an http(s) URL, a Docker reference (docker://), a Git repository (.git) "
                + "or a package URL (pkg:).",
            )

    def test_input_urls_with_allowed_addresses(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        self.mock_create.return_value = ScanCodeIO_Project(
            product=Product.objects.get(pk=1), project_uuid=PROJECT_UUID, project_name="project_name"
        )
        input_urls = [
            *INPUT_URLS,
            # Internal Git servers and registries are legitimate sources
            "https://10.0.0.1/repository.git",
            "https://git.example.internal/repository.git",
            "docker://10.0.0.1:5000/image:1.0",
            "docker://registry.example.internal:5000/image@sha256:abc123",
            "docker://alpine:3.19",
            "docker://alpine@sha256:abc123",
            "pkg:generic/a@1.0?download_url=https://example.com/a.zip",
        ]

        response = self._post(
            "db_internal_write", 1, {"name": "project_name", "input_urls": input_urls, "pipeline": "scan_codebase"}
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.mock_create.call_args.args[3].input_urls, input_urls)

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
        self.assertIsNone(self.mock_create.call_args.args[1])
        self.assertIsNone(self.mock_create.call_args.args[2])
        parameters: CreateProjectParameters = self.mock_create.call_args.args[3]
        self.assertEqual(parameters.name, "project_name")
        self.assertEqual(parameters.input_urls, INPUT_URLS)
        self.assertEqual(parameters.upload_file.name, "archive.zip")
        self.assertEqual(parameters.pipeline, "scan_codebase")
        self.assertTrue(parameters.execute_now)


class TestScanCodeIOProjectList(ScanCodeIOViewTestCase):
    def setUp(self):
        super().setUp()
        for pk, branch, service in [(1, None, None), (2, 1, None), (3, 1, 1), (4, 2, 2)]:
            ScanCodeIO_Project.objects.create(
                pk=pk,
                product=Product.objects.get(pk=1),
                branch_id=branch,
                service_id=service,
                project_uuid=PROJECT_UUID,
                project_name=f"project_{pk}",
                webhook_token_hash=f"hash_{pk}",
            )

    def _list_ids(self, query: str) -> list[int]:
        response = self._api_client("db_internal_write").get(f"/api/scancodeio_projects/?{query}")
        self.assertEqual(response.status_code, 200)
        return [project["id"] for project in response.data["results"]]

    def test_filter(self):
        self.assertEqual(self._list_ids("product=1"), [1, 2, 3, 4])
        self.assertEqual(self._list_ids("branch=1"), [2, 3])
        self.assertEqual(self._list_ids("service=2"), [4])
        self.assertEqual(self._list_ids("branch=1&service=1"), [3])

    def test_names(self):
        response = self._api_client("db_internal_write").get("/api/scancodeio_projects/3/")

        self.assertEqual(response.data["branch_name"], "db_branch_internal_dev")
        self.assertEqual(response.data["service_name"], "db_service_internal_backend")

        response = self._api_client("db_internal_write").get("/api/scancodeio_projects/1/")

        self.assertEqual(response.data["branch_name"], "")
        self.assertEqual(response.data["service_name"], "")


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


class TestScanCodeIOProjectImportResultsView(ScanCodeIOViewTestCase):
    def setUp(self):
        super().setUp()
        # The import itself runs in the request, only the call to ScanCode.io is mocked
        self.mock_get_results = self._start_patch(
            "application.scancodeio.services.scancodeio_import.get_scancodeio_results"
        )
        self._create_projects()

    def _post(self, username: str, project_id: int):
        return self._api_client(username).post(f"/api/scancodeio_projects/{project_id}/import_results/")

    def test_no_permission(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_internal_read", 1)

        self.assertEqual(response.status_code, 403)
        self.mock_get_results.assert_not_called()

    def test_not_authorized(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_internal_write", 2)

        self.assertEqual(response.status_code, 404)
        self.mock_get_results.assert_not_called()

    def test_feature_disabled(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._post("db_internal_write", 1)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(str(response.data), "{'message': 'ScanCode.io integration is not enabled'}")
        self.mock_get_results.assert_not_called()

    def test_license_management_disabled(self):
        self.mock_settings_load.return_value = Settings(
            feature_scancodeio_integration=True, feature_license_management=False
        )

        response = self._post("db_internal_write", 1)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"message": "ScanCode.io results cannot be imported, because license management is not enabled"},
        )
        self.mock_get_results.assert_not_called()

    def test_scancodeio_error(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        self.mock_get_results.side_effect = ValidationError("ScanCode.io is not reachable")

        response = self._post("db_internal_write", 1)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"message": "ScanCode.io is not reachable"})

    def test_import_results(self):
        self.mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)
        self.mock_get_results.return_value = {
            "packages": [
                {"name": "busybox", "version": "1.34.1-r5", "purl": "pkg:alpine/busybox@1.34.1-r5"},
                {"name": "alpine-keys", "version": "2.4-r1", "purl": "pkg:alpine/alpine-keys@2.4-r1"},
            ],
            "dependencies": [],
        }

        response = self._post("db_internal_write", 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"license_components_new": 2, "license_components_updated": 0, "license_components_deleted": 0},
        )
        self.mock_get_results.assert_called_once_with(ScanCodeIO_Project.objects.get(pk=1))
        self.assertEqual(
            License_Component.objects.filter(product_id=1, upload_filename=SCANCODEIO_FILENAME).count(),
            2,
        )

        self.mock_get_results.return_value["packages"].pop()

        response = self._post("db_internal_write", 1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"license_components_new": 0, "license_components_updated": 1, "license_components_deleted": 1},
        )


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
