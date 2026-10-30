import unittest
from unittest.mock import ANY, MagicMock, patch

from django.core.management import call_command

from application.background_tasks.types import Status
from application.commons.models import Settings
from application.core.models import Product
from application.core.types import OSVLinuxDistribution
from application.import_observations.models import Vulnerability_Check
from application.licenses.models import License, License_Component
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.services.scancodeio_import import (
    SCANCODEIO_FILENAME,
    TASK_NAME,
    _process_scancodeio_import,
    import_scancodeio_results,
    process_scancodeio_webhook,
)
from unittests.base_test_case import BaseTestCase


def _results(packages: list[dict]) -> dict:
    return {
        "headers": [
            {
                "tool_name": "scanpipe",
                "tool_version": "v38.2.0",
                "extra_data": {"images": [{"distro": {"identifier": "alpine", "version_id": "3.15.4"}}]},
            }
        ],
        "packages": packages,
        "dependencies": [],
    }


def _package(name: str, version: str, license_expression: str) -> dict:
    return {
        "purl": f"pkg:alpine/{name}@{version}?arch=x86_64",
        "name": name,
        "version": version,
        "declared_license_expression_spdx": license_expression,
        "package_uid": f"pkg:alpine/{name}@{version}?arch=x86_64&uuid=1",
    }


class TestImportScanCodeIOResults(BaseTestCase):
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
        self.product = Product.objects.get(pk=1)
        self.scancodeio_project = ScanCodeIO_Project(
            product=self.product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

        patcher = patch("application.scancodeio.services.scancodeio_import.get_scancodeio_results")
        self.addCleanup(patcher.stop)
        self.mock_get_results = patcher.start()

        settings = Settings.load()
        settings.feature_license_management = True
        settings.save()

    def test_import(self):
        self.mock_get_results.return_value = _results(
            [_package("busybox", "1.34.1-r5", "GPL-2.0-only"), _package("alpine-keys", "2.4-r1", "MIT")]
        )

        numbers = import_scancodeio_results(self.scancodeio_project)

        self.assertEqual(numbers, (2, 0, 0))
        self.mock_get_results.assert_called_once_with(self.scancodeio_project)

        license_components = License_Component.objects.filter(
            product=self.product, upload_filename=SCANCODEIO_FILENAME
        ).order_by("component_name")
        self.assertEqual(len(license_components), 2)
        self.assertEqual(license_components[1].component_name_version, "busybox:1.34.1-r5")
        self.assertEqual(license_components[1].component_purl, "pkg:alpine/busybox@1.34.1-r5?arch=x86_64")
        self.assertEqual(license_components[1].component_purl_type, "alpine")
        self.assertEqual(license_components[1].upload_filename, SCANCODEIO_FILENAME)
        self.assertIsNone(license_components[1].branch)
        self.assertIsNone(license_components[1].origin_service)
        self.assertEqual(license_components[1].effective_spdx_license, License.objects.get(spdx_id="GPL-2.0-only"))
        self.assertEqual(license_components[1].evidences.count(), 1)
        self.assertEqual(license_components[1].evidences.first().name, "Package")

        vulnerability_check = Vulnerability_Check.objects.get(product=self.product, filename=SCANCODEIO_FILENAME)
        self.assertIsNone(vulnerability_check.branch)
        self.assertEqual(vulnerability_check.scanner, "ScanCode.io / v38.2.0")
        self.assertEqual(vulnerability_check.last_import_licenses_new, 2)

        self.product.refresh_from_db()
        self.assertEqual(self.product.osv_linux_distribution, OSVLinuxDistribution.DISTRIBUTION_ALPINE)
        self.assertEqual(self.product.osv_linux_release, "v3.15")

    def test_import_again(self):
        self.mock_get_results.return_value = _results(
            [_package("busybox", "1.34.1-r5", "GPL-2.0-only"), _package("alpine-keys", "2.4-r1", "MIT")]
        )
        import_scancodeio_results(self.scancodeio_project)

        self.mock_get_results.return_value = _results(
            [_package("busybox", "1.34.1-r5", "GPL-2.0-only"), _package("musl", "1.2.2-r7", "MIT")]
        )
        numbers = import_scancodeio_results(self.scancodeio_project)

        self.assertEqual(numbers, (1, 1, 1))
        self.assertEqual(
            list(
                License_Component.objects.filter(product=self.product, upload_filename=SCANCODEIO_FILENAME)
                .order_by("component_name")
                .values_list("component_name", flat=True)
            ),
            ["busybox", "musl"],
        )
        self.assertEqual(
            Vulnerability_Check.objects.filter(product=self.product, filename=SCANCODEIO_FILENAME).count(), 1
        )

    def test_license_management_disabled(self):
        settings = Settings.load()
        settings.feature_license_management = False
        settings.save()
        self.mock_get_results.return_value = _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])

        numbers = import_scancodeio_results(self.scancodeio_project)

        self.assertEqual(numbers, (0, 0, 0))
        self.mock_get_results.assert_not_called()
        self.assertFalse(
            License_Component.objects.filter(product=self.product, upload_filename=SCANCODEIO_FILENAME).exists()
        )
        self.assertFalse(
            Vulnerability_Check.objects.filter(product=self.product, filename=SCANCODEIO_FILENAME).exists()
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.osv_linux_distribution, "")


class TestProcessScanCodeIOWebhook(unittest.TestCase):
    def setUp(self):
        self.scancodeio_project = ScanCodeIO_Project(
            pk=5,
            product=Product(name="product"),
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685",
            project_name="project_name",
        )

    @patch("application.scancodeio.services.scancodeio_import.import_scancodeio_results_task")
    def test_success(self, mock_task):
        with self.assertLogs("secobserve.scancodeio", level="INFO") as logs:
            process_scancodeio_webhook(
                self.scancodeio_project, {"run": {"pipeline_name": "scan_codebase", "status": "success"}}
            )

        self.assertIn(
            "ScanCode.io webhook for project project_name: pipeline scan_codebase finished with status success",
            logs.output[0],
        )
        mock_task.assert_called_once_with(5)

    @patch("application.scancodeio.services.scancodeio_import.import_scancodeio_results_task")
    def test_failure(self, mock_task):
        with self.assertLogs("secobserve.scancodeio", level="INFO") as logs:
            process_scancodeio_webhook(
                self.scancodeio_project, {"run": {"pipeline_name": "scan_codebase", "status": "failure"}}
            )

        self.assertIn("pipeline scan_codebase finished with status failure", logs.output[0])
        mock_task.assert_not_called()

    @patch("application.scancodeio.services.scancodeio_import.import_scancodeio_results_task")
    def test_no_run(self, mock_task):
        with self.assertLogs("secobserve.scancodeio", level="INFO") as logs:
            process_scancodeio_webhook(self.scancodeio_project, {"run": "invalid"})

        self.assertIn("pipeline None finished with status None", logs.output[0])
        mock_task.assert_not_called()


class TestProcessScanCodeIOImport(unittest.TestCase):
    def setUp(self):
        self.product = Product(name="product")
        self.scancodeio_project = ScanCodeIO_Project(id=1, product=self.product, project_name="project_name")

        self.mock_periodic_task = self._patch("application.scancodeio.services.scancodeio_import.Periodic_Task")
        self.task_record = self.mock_periodic_task.return_value
        self.mock_delete_older_task_entries = self._patch(
            "application.scancodeio.services.scancodeio_import.delete_older_task_entries"
        )
        self.mock_get_scancodeio_project = self._patch(
            "application.scancodeio.services.scancodeio_import.get_scancodeio_project_by_id"
        )
        self.mock_import = self._patch("application.scancodeio.services.scancodeio_import.import_scancodeio_results")
        self.mock_handle_task_exception = self._patch(
            "application.scancodeio.services.scancodeio_import.handle_task_exception"
        )

    def _patch(self, target: str) -> MagicMock:
        patcher = patch(target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_success(self):
        self.mock_get_scancodeio_project.return_value = self.scancodeio_project
        self.mock_import.return_value = (3, 2, 1)

        _process_scancodeio_import(1)

        self.mock_periodic_task.assert_called_once_with(task=TASK_NAME, start_time=ANY, status=Status.STATUS_RUNNING)
        self.mock_delete_older_task_entries.assert_called_once_with(TASK_NAME)
        self.mock_get_scancodeio_project.assert_called_once_with(1)
        self.mock_import.assert_called_once_with(self.scancodeio_project)
        self.assertEqual(self.task_record.status, Status.STATUS_SUCCESS)
        self.assertEqual(self.task_record.message, "Product 'product': 3 license components new, 2 updated, 1 deleted")
        self.assertEqual(self.task_record.save.call_count, 2)
        self.mock_handle_task_exception.assert_not_called()

    def test_project_not_found(self):
        self.mock_get_scancodeio_project.return_value = None

        _process_scancodeio_import(1)

        self.mock_import.assert_not_called()
        self.assertEqual(self.task_record.status, Status.STATUS_SUCCESS)
        self.assertEqual(self.task_record.message, "ScanCode.io project 1 not found, nothing to import")

    def test_exception(self):
        self.mock_get_scancodeio_project.return_value = self.scancodeio_project
        exception = Exception("something went wrong")
        self.mock_import.side_effect = exception

        # The exception is re-raised, so that Huey marks the task as failed
        with self.assertRaises(Exception) as context:
            _process_scancodeio_import(1)
        self.assertEqual(exception, context.exception)

        self.assertEqual(self.task_record.status, Status.STATUS_FAILURE)
        self.assertEqual(self.task_record.message, "something went wrong")
        self.assertEqual(self.task_record.save.call_count, 2)
        self.mock_handle_task_exception.assert_called_once_with(exception, product=self.product)

    def test_exception_project_lookup(self):
        exception = Exception("database error")
        self.mock_get_scancodeio_project.side_effect = exception

        with self.assertRaises(Exception):
            _process_scancodeio_import(1)

        self.assertEqual(self.task_record.status, Status.STATUS_FAILURE)
        self.mock_handle_task_exception.assert_called_once_with(exception, product=None)
