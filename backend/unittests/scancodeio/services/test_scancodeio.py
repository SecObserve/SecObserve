import hashlib
import re
from unittest.mock import ANY, MagicMock, patch

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import DatabaseError, IntegrityError
from rest_framework.exceptions import ValidationError

from application.commons.models import Settings
from application.core.models import Branch, Product, Service
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.services.scancodeio import (
    SCANCODEIO_REQUEST_TIMEOUT,
    create_scancodeio_project,
    delete_orphaned_scancodeio_project,
    delete_scancodeio_project,
    get_scancodeio_pipelines,
    get_scancodeio_project_details,
    get_scancodeio_project_ui_url,
    get_scancodeio_results,
    hash_webhook_token,
)
from application.scancodeio.types import CreateProjectParameters
from unittests.base_test_case import BaseTestCase


def _response(ok: bool = True, json_data=None, status_code: int = 200, reason: str = "OK") -> MagicMock:
    response = MagicMock()
    response.ok = ok
    response.status_code = status_code
    response.reason = reason
    response.is_redirect = False
    if isinstance(json_data, Exception):
        response.json.side_effect = json_data
    else:
        response.json.return_value = json_data
    return response


class TestScanCodeIO(BaseTestCase):
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
        self.mock_settings_load = self._start_patch("application.scancodeio.services.scancodeio.Settings.load")
        self.mock_request = self._start_patch("application.scancodeio.services.scancodeio.requests.request")
        self.product = Product.objects.get(pk=1)
        self.settings = Settings(
            scancodeio_base_url="https://scancode.example.com/",
            scancodeio_api_key="api_key",
            scancodeio_webhook_base_url="http://backend:8000/",
        )

    def _start_patch(self, target: str) -> MagicMock:
        patcher = patch(target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_create_project_successful(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )
        upload_file = SimpleUploadedFile("archive.zip", b"content")

        scancodeio_project = create_scancodeio_project(
            self.product,
            None,
            None,
            CreateProjectParameters(
                name="project_name",
                input_urls=["https://example.com/a.zip", "https://example.com/b.zip"],
                upload_file=upload_file,
                pipeline="scan_codebase",
                execute_now=True,
            ),
        )

        self.mock_request.assert_called_once_with(
            "post",
            "https://scancode.example.com/api/projects/",
            headers={"Accept": "application/json", "Authorization": "Token api_key"},
            timeout=SCANCODEIO_REQUEST_TIMEOUT,
            allow_redirects=False,
            data={
                "name": "project_name",
                "input_urls": ["https://example.com/a.zip", "https://example.com/b.zip"],
                "pipeline": "scan_codebase",
                "execute_now": "true",
                # The webhook URL contains a random token, see test_create_project_webhook
                "webhook_url": ANY,
            },
            files={"upload_file": ("archive.zip", upload_file)},
        )
        self.assertEqual(scancodeio_project.product, self.product)
        self.assertEqual(scancodeio_project.project_name, "project_name")
        self.assertEqual(str(scancodeio_project.project_uuid), "6461408c-726c-4b70-aa7a-c9cc9d1c9685")
        self.assertEqual(ScanCodeIO_Project.objects.filter(product=self.product).count(), 1)

    def test_create_project_without_file(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )

        create_scancodeio_project(
            self.product,
            None,
            None,
            CreateProjectParameters(
                name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
            ),
        )

        self.mock_request.assert_called_once_with(
            "post",
            "https://scancode.example.com/api/projects/",
            headers={"Accept": "application/json", "Authorization": "Token api_key"},
            timeout=SCANCODEIO_REQUEST_TIMEOUT,
            allow_redirects=False,
            data={
                "name": "project_name",
                "input_urls": ["https://example.com/a.zip"],
                "pipeline": "scan_codebase",
                "execute_now": "false",
                "webhook_url": ANY,
            },
            files=None,
        )

    def test_create_project_already_exists(self):
        ScanCodeIO_Project.objects.create(
            product=self.product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="existing"
        )

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                ),
            )

        self.assertEqual(str(e.exception.detail[0]), "Product db_product_internal already has a ScanCode.io project")
        self.mock_request.assert_not_called()

    def _parameters(self, name: str = "project_name") -> CreateProjectParameters:
        return CreateProjectParameters(name=name, pipeline="scan_codebase", input_urls=["https://example.com/a.zip"])

    def _create_existing_project(self, branch=None, service=None) -> None:
        ScanCodeIO_Project.objects.create(
            product=self.product,
            branch=branch,
            service=service,
            project_uuid="7cbd4e4a-2a1c-4a50-9a4e-2d8f8a8c1f3b",
            project_name="existing",
        )

    def test_create_project_branch_and_service_already_exists(self):
        branch = Branch.objects.get(pk=1)
        service = Service.objects.get(pk=1)
        self._create_existing_project(branch, service)

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(self.product, branch, service, self._parameters())

        self.assertEqual(
            str(e.exception.detail[0]),
            "Product db_product_internal, branch db_branch_internal_dev, service db_service_internal_backend "
            + "already has a ScanCode.io project",
        )
        self.mock_request.assert_not_called()

    def test_create_project_other_branch_or_service(self):
        branch_1 = Branch.objects.get(pk=1)
        branch_2 = Branch.objects.get(pk=2)
        service_1 = Service.objects.get(pk=1)
        service_2 = Service.objects.get(pk=2)
        self._create_existing_project(branch_1, service_1)
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )

        for branch, service in [
            (branch_1, service_2),
            (branch_2, service_1),
            (branch_1, None),
            (None, service_1),
            (None, None),
        ]:
            with self.subTest(branch=branch, service=service):
                scancodeio_project = create_scancodeio_project(self.product, branch, service, self._parameters())

                self.assertEqual(scancodeio_project.branch, branch)
                self.assertEqual(scancodeio_project.service, service)

        self.assertEqual(ScanCodeIO_Project.objects.filter(product=self.product).count(), 6)

    @patch("application.scancodeio.services.scancodeio.get_scancodeio_project")
    def test_create_project_empty_branch_and_service_concurrently_created(self, mock_get_project):
        # The unique constraint doesn't apply to the empty branch and service, the check within the lock has to find it
        mock_get_project.side_effect = [None, ScanCodeIO_Project()]
        self.mock_settings_load.return_value = self.settings
        self.mock_request.side_effect = [
            _response(json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}),
            _response(status_code=204),
        ]

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(self.product, None, None, self._parameters())

        self.assertEqual(str(e.exception.detail[0]), "Product db_product_internal already has a ScanCode.io project")
        self._assert_project_deleted_in_scancodeio()
        self.assertFalse(ScanCodeIO_Project.objects.filter(product=self.product).exists())

    @patch("application.scancodeio.services.scancodeio.get_scancodeio_project")
    @patch("application.scancodeio.services.scancodeio.Product.objects")
    def test_create_project_locks_product_before_checking(self, mock_products, mock_get_project):
        # SQLite ignores select_for_update(), so concurrent requests cannot be exercised here;
        # assert the lock is requested after the request to ScanCode.io and before the second check instead.
        mock_get_project.side_effect = [None, ScanCodeIO_Project()]
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )
        mock_lock = mock_products.select_for_update.return_value.get

        calls = MagicMock()
        calls.attach_mock(mock_get_project, "check")
        calls.attach_mock(self.mock_request, "request")
        calls.attach_mock(mock_lock, "lock")

        with self.assertRaises(ValidationError):
            create_scancodeio_project(self.product, None, None, self._parameters())

        self.assertEqual(
            [call[0] for call in calls.mock_calls if call[0] in ("check", "request", "lock")][:4],
            ["check", "request", "lock", "check"],
        )

    def test_create_project_default_name(self):
        branch = Branch.objects.get(pk=1)
        service = Service.objects.get(pk=1)
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )

        for project_branch, project_service, expected_name in [
            (None, None, "db_product_internal"),
            (branch, None, "db_product_internal - db_branch_internal_dev"),
            (None, service, "db_product_internal - db_service_internal_backend"),
            (branch, service, "db_product_internal - db_branch_internal_dev - db_service_internal_backend"),
        ]:
            with self.subTest(expected_name=expected_name):
                create_scancodeio_project(self.product, project_branch, project_service, self._parameters(name=""))

                self.assertEqual(self.mock_request.call_args.kwargs["data"]["name"], expected_name)

    def test_create_project_default_name_clipped(self):
        product = Product.objects.create(name="p" * 255)
        branch = Branch.objects.create(product=product, name="branch")
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )

        create_scancodeio_project(product, branch, None, self._parameters(name=""))

        self.assertEqual(self.mock_request.call_args.kwargs["data"]["name"], "p" * 100)

    def test_create_project_given_name_is_kept(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "my_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )

        create_scancodeio_project(self.product, Branch.objects.get(pk=1), None, self._parameters(name="my_name"))

        self.assertEqual(self.mock_request.call_args.kwargs["data"]["name"], "my_name")

    def test_create_project_no_input(self):
        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product, None, None, CreateProjectParameters(name="project_name", pipeline="scan_codebase")
            )

        self.assertEqual(str(e.exception.detail[0]), "At least one input URL or a file to upload is required")
        self.mock_request.assert_not_called()

    def test_create_project_addon_pipeline(self):
        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="find_vulnerabilities", input_urls=["https://example.com/a.zip"]
                ),
            )

        self.assertEqual(
            str(e.exception.detail[0]),
            "Pipeline find_vulnerabilities is an add-on and cannot be used to create a project",
        )
        self.mock_request.assert_not_called()

    def _assert_create_project_with_missing_setting(self, setting: str, message: str):
        setattr(self.settings, setting, "")
        self.mock_settings_load.return_value = self.settings

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                ),
            )

        self.assertEqual(str(e.exception.detail[0]), message)
        self.mock_request.assert_not_called()
        self.assertFalse(ScanCodeIO_Project.objects.filter(product=self.product).exists())

    def test_create_project_no_base_url(self):
        self._assert_create_project_with_missing_setting("scancodeio_base_url", "ScanCode.io base URL is not set")

    def test_create_project_no_api_key(self):
        self._assert_create_project_with_missing_setting("scancodeio_api_key", "ScanCode.io API key is not set")

    def test_create_project_no_webhook_base_url(self):
        self._assert_create_project_with_missing_setting(
            "scancodeio_webhook_base_url", "SecObserve URL for ScanCode.io webhooks is not set"
        )

    def test_create_project_error_response(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            ok=False,
            status_code=400,
            json_data={
                "name": ["project with this name already exists."],
                "pipeline": ["unknown is not a valid choice."],
            },
        )

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                ),
            )

        self.assertEqual(
            str(e.exception.detail[0]),
            "ScanCode.io error: name: project with this name already exists.; pipeline: unknown is not a valid choice.",
        )
        self.assertFalse(ScanCodeIO_Project.objects.filter(product=self.product).exists())

    def test_create_project_error_response_no_json(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            ok=False, status_code=502, reason="Bad Gateway", json_data=ValueError("no json")
        )

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                ),
            )

        self.assertEqual(str(e.exception.detail[0]), "ScanCode.io error: 502 Bad Gateway")

    def test_create_project_not_reachable(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.side_effect = requests.exceptions.ConnectionError("connection refused")

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                ),
            )

        # The details of the exception contain internal host names and are only logged
        self.assertEqual(str(e.exception.detail[0]), "ScanCode.io is not reachable")

    def test_redirect_is_not_followed(self):
        self.mock_settings_load.return_value = self.settings
        response = _response(status_code=302, reason="Found")
        response.is_redirect = True
        self.mock_request.return_value = response

        with self.assertRaises(ValidationError) as e:
            get_scancodeio_pipelines()

        self.assertEqual(
            str(e.exception.detail[0]), "ScanCode.io redirected the request, the base URL has to be corrected"
        )
        self.assertFalse(self.mock_request.call_args.kwargs["allow_redirects"])

    def test_get_pipelines(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data=[
                {"name": "scan_codebase", "summary": "Scan a codebase.", "steps": [], "is_available": True},
                {"name": "inspect_packages"},
                {"name": "load_sbom", "summary": "Load an SBOM.", "is_available": False},
                {"name": "find_vulnerabilities", "summary": "Find vulnerabilities.", "is_available": True},
            ]
        )

        pipelines = get_scancodeio_pipelines()

        self.assertEqual(
            pipelines,
            [
                {"name": "scan_codebase", "summary": "Scan a codebase."},
                {"name": "inspect_packages", "summary": ""},
            ],
        )
        self.mock_request.assert_called_once_with(
            "get",
            "https://scancode.example.com/api/projects/pipelines/",
            headers={"Accept": "application/json", "Authorization": "Token api_key"},
            timeout=SCANCODEIO_REQUEST_TIMEOUT,
            allow_redirects=False,
        )

    def test_get_project_details(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(json_data={"name": "project_name", "runs": []})
        scancodeio_project = ScanCodeIO_Project(
            product=self.product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

        details = get_scancodeio_project_details(scancodeio_project)

        self.assertEqual(
            details,
            {
                "name": "project_name",
                "runs": [],
                "ui_url": "https://scancode.example.com/project/project_name-6461408c/",
            },
        )
        self.mock_request.assert_called_once_with(
            "get",
            "https://scancode.example.com/api/projects/6461408c-726c-4b70-aa7a-c9cc9d1c9685/",
            headers={"Accept": "application/json", "Authorization": "Token api_key"},
            timeout=SCANCODEIO_REQUEST_TIMEOUT,
            allow_redirects=False,
        )

    def test_get_project_ui_url_slugified(self):
        self.mock_settings_load.return_value = self.settings
        scancodeio_project = ScanCodeIO_Project(
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="My Project 1.0"
        )

        self.assertEqual(
            get_scancodeio_project_ui_url(scancodeio_project),
            "https://scancode.example.com/project/my-project-10-6461408c/",
        )

    def test_get_project_ui_url_development(self):
        self.mock_settings_load.return_value = Settings(scancodeio_base_url="http://nginx")
        scancodeio_project = ScanCodeIO_Project(
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

        self.assertEqual(
            get_scancodeio_project_ui_url(scancodeio_project),
            "http://localhost:4100/project/project_name-6461408c/",
        )

    def test_get_project_details_error_response(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(ok=False, status_code=404, json_data={"detail": "Not found."})
        scancodeio_project = ScanCodeIO_Project(
            product=self.product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

        with self.assertRaises(ValidationError) as e:
            get_scancodeio_project_details(scancodeio_project)

        self.assertEqual(str(e.exception.detail[0]), "ScanCode.io error: detail: Not found.")

    def _create_project(self) -> ScanCodeIO_Project:
        return ScanCodeIO_Project.objects.create(
            product=self.product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

    def test_delete_project(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(status_code=204)
        scancodeio_project = self._create_project()

        delete_scancodeio_project(scancodeio_project)

        self.mock_request.assert_called_once_with(
            "delete",
            "https://scancode.example.com/api/projects/6461408c-726c-4b70-aa7a-c9cc9d1c9685/",
            headers={"Accept": "application/json", "Authorization": "Token api_key"},
            timeout=SCANCODEIO_REQUEST_TIMEOUT,
            allow_redirects=False,
        )
        self.mock_request.return_value.json.assert_not_called()
        self.assertFalse(ScanCodeIO_Project.objects.filter(product=self.product).exists())

    def test_delete_project_not_found_in_scancodeio(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(ok=False, status_code=404, json_data={"detail": "Not found."})
        scancodeio_project = self._create_project()

        delete_scancodeio_project(scancodeio_project)

        self.assertFalse(ScanCodeIO_Project.objects.filter(product=self.product).exists())

    def test_delete_project_error_response(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            ok=False, status_code=400, json_data={"status": "Cannot delete project while a run is in progress."}
        )
        scancodeio_project = self._create_project()

        with self.assertRaises(ValidationError) as e:
            delete_scancodeio_project(scancodeio_project)

        self.assertEqual(
            str(e.exception.detail[0]),
            "ScanCode.io error: status: Cannot delete project while a run is in progress.",
        )
        self.assertTrue(ScanCodeIO_Project.objects.filter(product=self.product).exists())

    def test_create_project_webhook(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}
        )

        scancodeio_project = create_scancodeio_project(
            self.product,
            None,
            None,
            CreateProjectParameters(
                name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
            ),
        )

        webhook_url = self.mock_request.call_args.kwargs["data"]["webhook_url"]
        match = re.fullmatch(r"http://backend:8000/api/scancodeio/webhook/([A-Za-z0-9_-]{43})/", webhook_url)
        self.assertIsNotNone(match)
        webhook_token = match.group(1)
        self.assertEqual(scancodeio_project.webhook_token_hash, hashlib.sha256(webhook_token.encode()).hexdigest())
        self.assertEqual(scancodeio_project.webhook_token_hash, hash_webhook_token(webhook_token))

    def _assert_project_deleted_in_scancodeio(self):
        self.assertEqual(
            self.mock_request.call_args_list[-1].args,
            ("delete", "https://scancode.example.com/api/projects/6461408c-726c-4b70-aa7a-c9cc9d1c9685/"),
        )

    @patch("application.scancodeio.services.scancodeio.ScanCodeIO_Project.objects.create")
    def test_create_project_database_error(self, mock_create):
        mock_create.side_effect = DatabaseError("database error")
        self.mock_settings_load.return_value = self.settings
        self.mock_request.side_effect = [
            _response(json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}),
            _response(status_code=204),
        ]

        with self.assertRaises(DatabaseError):
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                ),
            )

        self.assertEqual(self.mock_request.call_count, 2)
        self._assert_project_deleted_in_scancodeio()

    @patch("application.scancodeio.services.scancodeio.ScanCodeIO_Project.objects.create")
    def test_create_project_concurrently_created(self, mock_create):
        mock_create.side_effect = IntegrityError("duplicate key")
        self.mock_settings_load.return_value = self.settings
        self.mock_request.side_effect = [
            _response(json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}),
            _response(status_code=204),
        ]

        with self.assertRaises(ValidationError) as e:
            create_scancodeio_project(
                self.product,
                None,
                None,
                CreateProjectParameters(
                    name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                ),
            )

        self.assertEqual(str(e.exception.detail[0]), "Product db_product_internal already has a ScanCode.io project")
        self._assert_project_deleted_in_scancodeio()

    @patch("application.scancodeio.services.scancodeio.ScanCodeIO_Project.objects.create")
    def test_create_project_database_error_and_delete_failed(self, mock_create):
        mock_create.side_effect = DatabaseError("database error")
        self.mock_settings_load.return_value = self.settings
        self.mock_request.side_effect = [
            _response(json_data={"name": "project_name", "uuid": "6461408c-726c-4b70-aa7a-c9cc9d1c9685"}),
            requests.exceptions.ConnectionError("connection refused"),
        ]

        with self.assertLogs("secobserve.scancodeio", level="WARNING") as logs:
            with self.assertRaises(DatabaseError):
                create_scancodeio_project(
                    self.product,
                    None,
                    None,
                    CreateProjectParameters(
                        name="project_name", pipeline="scan_codebase", input_urls=["https://example.com/a.zip"]
                    ),
                )

        self.assertIn(
            "Orphaned ScanCode.io project 6461408c-726c-4b70-aa7a-c9cc9d1c9685 could not be deleted", logs.output[-1]
        )

    def test_delete_orphaned_scancodeio_project(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(status_code=204)

        # call_local calls the undecorated function, without enqueuing a Huey task
        delete_orphaned_scancodeio_project.call_local("6461408c-726c-4b70-aa7a-c9cc9d1c9685")

        self.mock_request.assert_called_once()
        self._assert_project_deleted_in_scancodeio()

    def test_delete_orphaned_scancodeio_project_error_response(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(
            ok=False, status_code=400, json_data={"status": "Cannot delete project while a run is in progress."}
        )

        with self.assertLogs("secobserve.scancodeio", level="WARNING") as logs:
            delete_orphaned_scancodeio_project.call_local("6461408c-726c-4b70-aa7a-c9cc9d1c9685")

        self.assertIn(
            "Orphaned ScanCode.io project 6461408c-726c-4b70-aa7a-c9cc9d1c9685 could not be deleted", logs.output[0]
        )

    def test_get_results(self):
        self.mock_settings_load.return_value = self.settings
        self.mock_request.return_value = _response(json_data={"headers": [], "packages": [], "dependencies": []})
        scancodeio_project = ScanCodeIO_Project(
            product=self.product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

        results = get_scancodeio_results(scancodeio_project)

        self.assertEqual(results, {"headers": [], "packages": [], "dependencies": []})
        self.mock_request.assert_called_once_with(
            "get",
            "https://scancode.example.com/api/projects/6461408c-726c-4b70-aa7a-c9cc9d1c9685/results/",
            headers={"Accept": "application/json", "Authorization": "Token api_key"},
            timeout=SCANCODEIO_REQUEST_TIMEOUT,
            allow_redirects=False,
            params={"sections": ["packages", "dependencies"]},
        )
