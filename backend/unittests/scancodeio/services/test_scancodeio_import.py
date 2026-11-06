import unittest
from unittest.mock import ANY, MagicMock, patch

from django.core.management import call_command
from rest_framework.exceptions import ValidationError

from application.background_tasks.types import Status
from application.commons.models import Settings
from application.core.models import Branch, Product, Service
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
    reimport_scancodeio_results,
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
        self.assertEqual(license_components[1].component_purl, "pkg:apk/alpine/busybox@1.34.1-r5?arch=x86_64")
        self.assertEqual(license_components[1].component_purl_type, "apk")
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

    def _project(self, branch=None, service=None) -> ScanCodeIO_Project:
        return ScanCodeIO_Project(
            product=self.product,
            branch=branch,
            service=service,
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685",
            project_name="project_name",
        )

    def test_import_branch_and_service(self):
        branch = Branch.objects.get(pk=1)
        service = Service.objects.get(pk=1)
        self.mock_get_results.return_value = _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])

        numbers = import_scancodeio_results(self._project(branch, service))

        self.assertEqual(numbers, (1, 0, 0))
        license_component = License_Component.objects.get(product=self.product, upload_filename=SCANCODEIO_FILENAME)
        self.assertEqual(license_component.branch, branch)
        self.assertEqual(license_component.origin_service, service)
        vulnerability_check = Vulnerability_Check.objects.get(product=self.product, filename=SCANCODEIO_FILENAME)
        self.assertEqual(vulnerability_check.branch, branch)
        self.assertEqual(vulnerability_check.service, service)

    def test_import_services_of_same_branch_are_independent(self):
        branch = Branch.objects.get(pk=1)
        project_1 = self._project(branch, Service.objects.get(pk=1))
        project_2 = self._project(branch, Service.objects.get(pk=2))

        self.mock_get_results.return_value = _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])
        self.assertEqual(import_scancodeio_results(project_1), (1, 0, 0))

        # The same component in another service is new, and the component of the first service is not deleted
        self.mock_get_results.return_value = _results(
            [_package("busybox", "1.34.1-r5", "GPL-2.0-only"), _package("alpine-keys", "2.4-r1", "MIT")]
        )
        self.assertEqual(import_scancodeio_results(project_2), (2, 0, 0))
        self.assertEqual(License_Component.objects.filter(product=self.product, origin_service=1).count(), 1)
        self.assertEqual(License_Component.objects.filter(product=self.product, origin_service=2).count(), 2)

        # The next import of the first service only changes its own components
        self.mock_get_results.return_value = _results([_package("alpine-keys", "2.4-r1", "MIT")])
        self.assertEqual(import_scancodeio_results(project_1), (1, 0, 1))
        self.assertEqual(
            list(
                License_Component.objects.filter(product=self.product, origin_service=1).values_list(
                    "component_name", flat=True
                )
            ),
            ["alpine-keys"],
        )
        self.assertEqual(License_Component.objects.filter(product=self.product, origin_service=2).count(), 2)

    def test_import_branches_are_independent(self):
        project_1 = self._project(Branch.objects.get(pk=1))
        project_2 = self._project(Branch.objects.get(pk=2))

        self.mock_get_results.return_value = _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])
        self.assertEqual(import_scancodeio_results(project_1), (1, 0, 0))
        self.assertEqual(import_scancodeio_results(project_2), (1, 0, 0))

        self.mock_get_results.return_value = _results([])
        self.assertEqual(import_scancodeio_results(project_1), (0, 0, 1))
        self.assertEqual(License_Component.objects.filter(product=self.product, branch=1).count(), 0)
        self.assertEqual(License_Component.objects.filter(product=self.product, branch=2).count(), 1)

    def test_import_osv_distribution_and_last_import_for_branch(self):
        branch = Branch.objects.get(pk=1)
        Branch.objects.filter(pk=1).update(last_import=None)
        self.mock_get_results.return_value = _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])

        import_scancodeio_results(self._project(branch))

        branch.refresh_from_db()
        self.assertEqual(branch.osv_linux_distribution, OSVLinuxDistribution.DISTRIBUTION_ALPINE)
        self.assertEqual(branch.osv_linux_release, "v3.15")
        self.assertIsNotNone(branch.last_import)
        self.product.refresh_from_db()
        self.assertEqual(self.product.osv_linux_distribution, "")
        self.assertEqual(self.product.osv_linux_release, "")

    def test_import_osv_distribution_latest_import_of_service_wins(self):
        branch = Branch.objects.get(pk=1)
        results = _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])
        self.mock_get_results.return_value = results
        import_scancodeio_results(self._project(branch, Service.objects.get(pk=1)))

        results["headers"][0]["extra_data"]["images"] = [{"distro": {"identifier": "debian", "version_id": "12"}}]
        import_scancodeio_results(self._project(branch, Service.objects.get(pk=2)))

        branch.refresh_from_db()
        self.assertEqual(branch.osv_linux_distribution, OSVLinuxDistribution.DISTRIBUTION_DEBIAN)
        self.assertEqual(branch.osv_linux_release, "12")

    def test_branch_change_during_request_is_kept(self):
        branch = Branch.objects.get(pk=1)
        Branch.objects.filter(pk=1).update(purl="pkg:generic/changed")
        self.mock_get_results.return_value = _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])

        import_scancodeio_results(self._project(branch))

        branch.refresh_from_db()
        self.assertEqual(branch.purl, "pkg:generic/changed")
        self.assertEqual(branch.osv_linux_distribution, OSVLinuxDistribution.DISTRIBUTION_ALPINE)

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

    def test_product_change_during_request_is_kept(self):
        def get_results(_):
            Product.objects.filter(pk=self.product.pk).update(description="changed during the request")
            return _results([_package("busybox", "1.34.1-r5", "GPL-2.0-only")])

        self.mock_get_results.side_effect = get_results

        import_scancodeio_results(self.scancodeio_project)

        self.product.refresh_from_db()
        self.assertEqual(self.product.description, "changed during the request")
        self.assertEqual(self.product.osv_linux_distribution, OSVLinuxDistribution.DISTRIBUTION_ALPINE)

    @patch("application.scancodeio.services.scancodeio_import.process_license_components")
    @patch("application.scancodeio.services.scancodeio_import.Vulnerability_Check.objects")
    @patch("application.scancodeio.services.scancodeio_import.apply_osv_linux_distribution")
    @patch("application.scancodeio.services.scancodeio_import.Product.objects")
    def test_locks_product_before_changing_anything(self, mock_products, mock_apply, mock_checks, mock_process):
        # SQLite ignores select_for_update(), so concurrent imports cannot be exercised here;
        # assert the lock is requested after the request to ScanCode.io and before any change instead.
        self.mock_get_results.return_value = _results([])
        mock_lock = mock_products.select_for_update.return_value.get
        vulnerability_check = MagicMock()
        mock_checks.update_or_create.return_value = (vulnerability_check, False)
        mock_process.return_value = (1, 2, 3)

        calls = MagicMock()
        calls.attach_mock(self.mock_get_results, "request")
        calls.attach_mock(mock_lock, "lock")
        calls.attach_mock(mock_apply, "apply")
        calls.attach_mock(mock_checks.update_or_create, "update_or_create")
        calls.attach_mock(mock_process, "process")

        numbers = import_scancodeio_results(self.scancodeio_project)

        self.assertEqual(numbers, (1, 2, 3))
        self.assertEqual(
            [call[0] for call in calls.mock_calls],
            ["request", "lock", "apply", "update_or_create", "process"],
        )
        mock_products.select_for_update.assert_called_once_with()
        mock_lock.assert_called_once_with(pk=self.product.pk)
        mock_apply.assert_called_once_with(mock_lock.return_value, ANY)
        self.assertEqual(mock_checks.update_or_create.call_args.kwargs["product"], mock_lock.return_value)

    def test_import_wolfi(self):
        results = _results([_package("busybox", "1.36.0-r0", "GPL-2.0-only")])
        results["headers"][0]["extra_data"]["images"] = [{"distro": {"identifier": "wolfi", "version_id": "20230201"}}]
        self.mock_get_results.return_value = results

        import_scancodeio_results(self.scancodeio_project)

        license_component = License_Component.objects.get(product=self.product, upload_filename=SCANCODEIO_FILENAME)
        self.assertEqual(license_component.component_purl, "pkg:apk/wolfi/busybox@1.36.0-r0?arch=x86_64")
        self.assertEqual(license_component.component_purl_type, "apk")

        self.product.refresh_from_db()
        self.assertEqual(self.product.osv_linux_distribution, OSVLinuxDistribution.DISTRIBUTION_WOLFI)
        self.assertEqual(self.product.osv_linux_release, "")

    def test_import_same_name_in_different_namespaces(self):
        self.mock_get_results.return_value = _results(
            [
                {
                    "purl": f"pkg:npm/{namespace.replace('@', '%40')}/types@3.0.0",
                    "type": "npm",
                    "namespace": namespace,
                    "name": "types",
                    "version": "3.0.0",
                    "package_uid": f"pkg:npm/{namespace.replace('@', '%40')}/types@3.0.0?uuid=1",
                }
                for namespace in ["@aws-sdk", "@smithy"]
            ]
        )

        numbers = import_scancodeio_results(self.scancodeio_project)

        self.assertEqual(numbers, (2, 0, 0))
        self.assertEqual(
            list(
                License_Component.objects.filter(product=self.product, upload_filename=SCANCODEIO_FILENAME)
                .order_by("component_name")
                .values_list("component_name_version", flat=True)
            ),
            ["@aws-sdk/types:3.0.0", "@smithy/types:3.0.0"],
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


class TestReimportScanCodeIOResults(unittest.TestCase):
    def setUp(self):
        self.scancodeio_project = ScanCodeIO_Project(pk=5, product=Product(name="product"), project_name="project_name")

    @patch("application.scancodeio.services.scancodeio_import.import_scancodeio_results")
    @patch("application.scancodeio.services.scancodeio_import.Settings.load")
    def test_import(self, mock_settings_load, mock_import):
        mock_settings_load.return_value = Settings(feature_license_management=True)
        mock_import.return_value = (3, 2, 1)

        numbers = reimport_scancodeio_results(self.scancodeio_project)

        self.assertEqual(numbers, (3, 2, 1))
        mock_import.assert_called_once_with(self.scancodeio_project)

    @patch("application.scancodeio.services.scancodeio_import.import_scancodeio_results")
    @patch("application.scancodeio.services.scancodeio_import.Settings.load")
    def test_license_management_disabled(self, mock_settings_load, mock_import):
        mock_settings_load.return_value = Settings(feature_license_management=False)

        with self.assertRaises(ValidationError) as context:
            reimport_scancodeio_results(self.scancodeio_project)

        self.assertEqual(
            context.exception.detail,
            ["ScanCode.io results cannot be imported, because license management is not enabled"],
        )
        mock_import.assert_not_called()


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
        self.assertEqual(
            self.task_record.message,
            f"Product 'product', project '{self.scancodeio_project.project_name}': "
            + "3 license components new, 2 updated, 1 deleted",
        )
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
