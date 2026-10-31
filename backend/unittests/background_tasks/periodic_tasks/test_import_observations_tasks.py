from datetime import timedelta
from unittest.mock import ANY, MagicMock, patch

import requests
from django.db import OperationalError
from django.utils import timezone
from huey import SKIPPED
from huey.contrib.djhuey import HUEY

from application.background_tasks.models import Periodic_Task
from application.background_tasks.periodic_tasks.import_observations_tasks import (
    OSV_SCAN_RUN_KEY,
    OSV_SCAN_TASK_NAME,
    task_api_import,
    task_osv_scan_product,
    task_osv_scan_summary,
)
from application.background_tasks.types import Status
from application.commons.models import Settings
from application.core.models import Product
from unittests.base_test_case import BaseTestCase

TASK_NAME = "Import observations from API configurations, OSV and VulnerableCode"


def _create_product(name: str, osv: bool = True, vulnerablecode: bool = True) -> Product:
    return Product.objects.create(
        name=name,
        osv_enabled=osv,
        automatic_osv_scanning_enabled=osv,
        vulnerablecode_enabled=vulnerablecode,
        automatic_vulnerablecode_scanning_enabled=vulnerablecode,
    )


def _get_osv_scan_run() -> Periodic_Task:
    return Periodic_Task.objects.filter(task=OSV_SCAN_TASK_NAME).latest("start_time")


def _http_error(status_code: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(f"{status_code} Error", response=response)


class TestImportObservationsTasks(BaseTestCase):
    def _get_task(self) -> Periodic_Task:
        return Periodic_Task.objects.filter(task=TASK_NAME).latest("start_time")

    def _get_task_message(self) -> str:
        # so_periodic_task swallows the return value of the task and stores it on the Periodic_Task
        # entry, so the composed message can only be asserted through the database.
        return self._get_task().message

    # ---------------------------------------------------------------
    # task_api_import
    # ---------------------------------------------------------------

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_all_enabled(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_api_import_observations,
        mock_scan_product_osv,
        mock_scan_product_vc,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = True
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = "http://vulnerablecode.example.com"
        mock_settings_load.return_value = settings

        # Mock API configurations
        mock_api_config = MagicMock()
        mock_api_config.automatic_import_branch = self.branch_1
        mock_api_config.automatic_import_service = self.service_1
        mock_api_config.automatic_import_docker_image_name_tag = "image:tag"
        mock_api_config.automatic_import_endpoint_url = "https://example.com"
        mock_api_config.automatic_import_kubernetes_cluster = "cluster1"
        mock_api_config_filter.return_value = [mock_api_config]

        product = _create_product("product_osv_vulnerablecode")
        _create_product("product_none", osv=False, vulnerablecode=False)

        # Mock import results
        mock_api_import_observations.return_value = (1, 2, 3)  # new, updated, resolved
        mock_scan_product_osv.return_value = (4, 5, 6)  # new, updated, resolved
        mock_scan_product_vc.return_value = (7, 8, 9)  # new, updated, resolved

        # Execute
        task_api_import()

        # Assert
        # Check settings were loaded 3 times (once for API import, once for OSV and once for deleting old entries)
        # self.assertEqual(mock_settings_load.call_count, 3)

        # Check API import was called with correct parameters
        mock_api_config_filter.assert_called_once_with(automatic_import_enabled=True)
        mock_api_import_observations.assert_called_once()
        api_import_params = mock_api_import_observations.call_args[0][0]
        self.assertEqual(api_import_params.api_configuration, mock_api_config)
        self.assertEqual(api_import_params.branch, mock_api_config.automatic_import_branch)
        self.assertEqual(api_import_params.service_name, mock_api_config.automatic_import_service.name)
        self.assertEqual(
            api_import_params.docker_image_name_tag, mock_api_config.automatic_import_docker_image_name_tag
        )
        self.assertEqual(api_import_params.endpoint_url, mock_api_config.automatic_import_endpoint_url)
        self.assertEqual(api_import_params.kubernetes_cluster, mock_api_config.automatic_import_kubernetes_cluster)

        # Check VulnerableCode scanning was called, and OSV scanning by the enqueued task
        mock_scan_product_vc.assert_called_once_with(product)
        mock_scan_product_osv.assert_called_once_with(product)
        self.assertEqual("Scanned 1 of 1 products.", _get_osv_scan_run().message)

        # Check the composed message
        self.assertEqual(
            "Imported observations for 1 products from API configurations."
            "\nImported observations for 1 products from VulnerableCode scanning."
            "\nEnqueued OSV scanning for 1 products.",
            self._get_task_message(),
        )

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_api_disabled(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_api_import_observations,
        mock_scan_product_osv,
        mock_scan_product_vc,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = False
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = "http://vulnerablecode.example.com"
        mock_settings_load.return_value = settings

        product = _create_product("product_osv_vulnerablecode")

        # Mock import results
        mock_scan_product_osv.return_value = (4, 5, 6)  # new, updated, resolved
        mock_scan_product_vc.return_value = (7, 8, 9)  # new, updated, resolved

        # Execute
        task_api_import()

        # Assert
        # Check API import was not called
        mock_api_config_filter.assert_not_called()
        mock_api_import_observations.assert_not_called()

        # Check OSV and VulnerableCode scanning was called
        mock_scan_product_osv.assert_called_once_with(product)
        mock_scan_product_vc.assert_called_once_with(product)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_osv_disabled(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_product_filter,
        mock_api_import_observations,
        mock_scan_product_osv,
        mock_scan_product_vc,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = True
        settings.feature_automatic_osv_scanning = False
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = "http://vulnerablecode.example.com"
        mock_settings_load.return_value = settings

        # Mock API configurations
        mock_api_config = MagicMock()
        mock_api_config_filter.return_value = [mock_api_config]

        # Mock products
        mock_product = MagicMock()
        mock_product_filter.return_value = [mock_product]

        # Mock import results
        mock_api_import_observations.return_value = (1, 2, 3)  # new, updated, resolved
        mock_scan_product_vc.return_value = (7, 8, 9)  # new, updated, resolved

        # Execute
        task_api_import()

        # Assert
        # Check API import was called
        mock_api_config_filter.assert_called_once_with(automatic_import_enabled=True)
        mock_api_import_observations.assert_called_once()

        # Check OSV scanning was not called, but VulnerableCode scanning was
        mock_product_filter.assert_called_once_with(
            vulnerablecode_enabled=True, automatic_vulnerablecode_scanning_enabled=True
        )
        mock_scan_product_osv.assert_not_called()
        mock_scan_product_vc.assert_called_once_with(mock_product)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_vulnerablecode_disabled(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_api_import_observations,
        mock_scan_product_osv,
        mock_scan_product_vc,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = True
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = False
        settings.vulnerablecode_base_url = "http://vulnerablecode.example.com"
        mock_settings_load.return_value = settings

        # Mock API configurations
        mock_api_config = MagicMock()
        mock_api_config_filter.return_value = [mock_api_config]

        product = _create_product("product_osv_vulnerablecode")

        # Mock import results
        mock_api_import_observations.return_value = (1, 2, 3)  # new, updated, resolved
        mock_scan_product_osv.return_value = (4, 5, 6)  # new, updated, resolved

        # Execute
        task_api_import()

        # Assert
        # Check API import was called
        mock_api_config_filter.assert_called_once_with(automatic_import_enabled=True)
        mock_api_import_observations.assert_called_once()

        # Check VulnerableCode scanning was not called, but OSV scanning was
        mock_scan_product_vc.assert_not_called()
        mock_scan_product_osv.assert_called_once_with(product)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_vulnerablecode_no_base_url(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_api_import_observations,
        mock_scan_product_osv,
        mock_scan_product_vc,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = True
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = ""
        mock_settings_load.return_value = settings

        # Mock API configurations
        mock_api_config = MagicMock()
        mock_api_config_filter.return_value = [mock_api_config]

        product = _create_product("product_osv_vulnerablecode")

        # Mock import results
        mock_api_import_observations.return_value = (1, 2, 3)  # new, updated, resolved
        mock_scan_product_osv.return_value = (4, 5, 6)  # new, updated, resolved

        # Execute
        task_api_import()

        # Assert
        # Check API import was called
        mock_api_config_filter.assert_called_once_with(automatic_import_enabled=True)
        mock_api_import_observations.assert_called_once()

        # Check VulnerableCode scanning was not called, but OSV scanning was
        mock_scan_product_vc.assert_not_called()
        mock_scan_product_osv.assert_called_once_with(product)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.handle_task_exception")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_api_exception_handling(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_api_import_observations,
        mock_handle_task_exception,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = True
        settings.feature_automatic_osv_scanning = False
        settings.feature_automatic_vulnerablecode_scanning = False
        mock_settings_load.return_value = settings

        # Mock API configurations
        mock_api_config = MagicMock()
        mock_api_config_filter.return_value = [mock_api_config]

        # Mock API import to raise exception
        test_exception = Exception("Test API import exception")
        mock_api_import_observations.side_effect = test_exception

        # Execute
        task_api_import()

        # Assert
        # Check exception was handled
        mock_handle_task_exception.assert_called_once_with(test_exception, product=mock_api_config.product)

        # Check the task is marked as failed, although the remaining imports have been executed
        self.assertEqual(Status.STATUS_FAILURE, self._get_task().status)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.send_task_exception_notification")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_osv_exception_handling(
        self,
        mock_settings_load,
        mock_scan_product,
        mock_send_task_exception_notification,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = False
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = False
        mock_settings_load.return_value = settings

        _create_product("product_osv")

        # Mock scan_product to raise exception
        test_exception = Exception("Test OSV scanning exception")
        mock_scan_product.side_effect = test_exception

        # Execute
        task_api_import()

        # Assert
        # Check the exception was notified by the summary of the run
        mock_send_task_exception_notification.assert_called_once_with(
            function="task_osv_scan_product", arguments=None, user=None, exception=ANY
        )
        self.assertEqual(
            "OSV scanning failed for 1 of 1 products:\nproduct_osv: Test OSV scanning exception",
            str(mock_send_task_exception_notification.call_args.kwargs["exception"]),
        )
        osv_scan_run = _get_osv_scan_run()
        self.assertEqual(Status.STATUS_FAILURE, osv_scan_run.status)
        self.assertEqual("Scanned 0 of 1 products, 1 failed.", osv_scan_run.message)

        # A failed OSV scan fails the summary of its run, not the task that has enqueued it
        self.assertEqual(Status.STATUS_SUCCESS, self._get_task().status)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.handle_task_exception")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_vulnerablecode_exception_handling(
        self,
        mock_settings_load,
        mock_product_filter,
        mock_scan_product,
        mock_handle_task_exception,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = False
        settings.feature_automatic_osv_scanning = False
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = "http://vulnerablecode.example.com"
        mock_settings_load.return_value = settings

        # Mock products
        mock_product = MagicMock()
        mock_product_filter.return_value = [mock_product]

        # Mock scan_product to raise exception
        test_exception = Exception("Test VulnerableCode scanning exception")
        mock_scan_product.side_effect = test_exception

        # Execute
        task_api_import()

        # Assert
        # Check exception was handled
        mock_handle_task_exception.assert_called_once_with(test_exception, product=mock_product)

        # Check the failed imports are counted with the VulnerableCode counter
        self.assertIn("\nVulnerableCode scanning failed for 1 products.", self._get_task_message())

        # Check the task is marked as failed, although the remaining imports have been executed
        self.assertEqual(Status.STATUS_FAILURE, self._get_task().status)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.send_task_exception_notification")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.handle_task_exception")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_all_failed(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_api_import_observations,
        mock_scan_product_osv,
        mock_scan_product_vc,
        mock_handle_task_exception,
        mock_send_task_exception_notification,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = True
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = "http://vulnerablecode.example.com"
        mock_settings_load.return_value = settings

        # Mock API configurations
        mock_api_config = MagicMock()
        mock_api_config_filter.return_value = [mock_api_config]

        _create_product("product_osv_vulnerablecode")

        # Mock every stage to raise an exception
        mock_api_import_observations.side_effect = Exception("Test API import exception")
        mock_scan_product_osv.side_effect = Exception("Test OSV scanning exception")
        mock_scan_product_vc.side_effect = Exception("Test VulnerableCode scanning exception")

        # Execute
        task_api_import()

        # Assert
        # Check every exception was handled, the one of OSV scanning by the enqueued task
        self.assertEqual(2, mock_handle_task_exception.call_count)
        mock_send_task_exception_notification.assert_called_once()

        # A failed OSV scan fails its own task, not the one that has enqueued it
        message = self._get_task_message()
        self.assertIn("\nAPI import failed for 1 configurations.", message)
        self.assertIn("\nVulnerableCode scanning failed for 1 products.", message)
        self.assertNotIn("OSV scanning failed", message)

        self.assertEqual(Status.STATUS_FAILURE, self._get_task().status)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_no_service(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_api_import_observations,
    ):
        # Setup
        # Mock settings
        settings = Settings()
        settings.feature_automatic_api_import = True
        settings.feature_automatic_osv_scanning = False
        settings.feature_automatic_vulnerablecode_scanning = False
        mock_settings_load.return_value = settings

        # Mock API configuration without a service
        mock_api_config = MagicMock()
        mock_api_config.automatic_import_service = None
        mock_api_config_filter.return_value = [mock_api_config]

        # Mock import results
        mock_api_import_observations.return_value = (1, 2, 3)  # new, updated, resolved

        # Execute
        task_api_import()

        # Assert
        # Check the service name defaults to an empty string
        mock_api_import_observations.assert_called_once()
        api_import_params = mock_api_import_observations.call_args[0][0]
        self.assertEqual("", api_import_params.service_name)


class TestTaskOSVScanProduct(BaseTestCase):
    def _task(self, retries: int) -> MagicMock:
        task = MagicMock()
        task.retries = retries
        return task

    def test_priority_below_default(self):
        # Huey dequeues tasks with a higher priority first, all other tasks have the default priority 0
        self.assertLess(task_osv_scan_product.s(1, "run").priority, 0)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner")
    def test_scan(self, mock_osv_scanner):
        product = _create_product("product_osv")
        mock_osv_scanner.return_value.scan_product.return_value = (1, 2, 3)  # new, updated, resolved

        with self.assertLogs("secobserve.import_observations", level="INFO") as logs:
            task_osv_scan_product.call_local(product.pk, "run")

        mock_osv_scanner.assert_called_once_with("run")
        mock_osv_scanner.return_value.scan_product.assert_called_once_with(product)
        self.assertIn("OSV scanning - product_osv: 1 new, 2 updated, 3 resolved", logs.output[0])

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    def test_product_deleted(self, mock_scan_product):
        product = _create_product("product_osv")
        product_id = product.pk
        product.delete()

        task_osv_scan_product.call_local(product_id, "run")

        mock_scan_product.assert_not_called()

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    def test_product_disabled(self, mock_scan_product):
        product_manual = Product.objects.create(
            name="product_osv_manual", osv_enabled=True, automatic_osv_scanning_enabled=False
        )
        product_no_osv = Product.objects.create(
            name="product_no_osv", osv_enabled=False, automatic_osv_scanning_enabled=True
        )

        task_osv_scan_product.call_local(product_manual.pk, "run")
        task_osv_scan_product.call_local(product_no_osv.pk, "run")

        mock_scan_product.assert_not_called()

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_feature_disabled(self, mock_settings_load, mock_scan_product):
        settings = Settings()
        settings.feature_automatic_osv_scanning = False
        mock_settings_load.return_value = settings
        product = _create_product("product_osv")

        task_osv_scan_product.call_local(product.pk, "run")

        mock_scan_product.assert_not_called()

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    def test_transient_error_is_retried(self, mock_scan_product):
        product = _create_product("product_osv")
        for test_exception in (_http_error(503), _http_error(429), requests.ConnectionError(), OperationalError()):
            mock_scan_product.side_effect = test_exception
            task = self._task(retries=2)

            with self.assertRaises(Exception) as context:
                task_osv_scan_product.call_local(product.pk, "run", task=task)

            self.assertIs(test_exception, context.exception)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    def test_other_error_is_not_retried(self, mock_scan_product):
        product = _create_product("product_osv")
        for test_exception in (_http_error(404), Exception("Test OSV scanning exception")):
            mock_scan_product.side_effect = test_exception

            result = task_osv_scan_product.call_local(product.pk, "run", task=self._task(retries=2))

            self.assertEqual(f"product_osv: {test_exception}", result)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    def test_last_attempt(self, mock_scan_product):
        product = _create_product("product_osv")
        mock_scan_product.side_effect = _http_error(503)

        result = task_osv_scan_product.call_local(product.pk, "run", task=self._task(retries=0))

        self.assertEqual("product_osv: 503 Error", result)


class TestTaskOSVScanSummary(BaseTestCase):
    def setUp(self):
        super().setUp()
        HUEY.delete(OSV_SCAN_RUN_KEY)
        self.start_time = timezone.now() - timedelta(hours=1)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.send_task_exception_notification")
    def test_success(self, mock_send_task_exception_notification):
        HUEY.put(OSV_SCAN_RUN_KEY, ("run", self.start_time, 2))

        task_osv_scan_summary.call_local("run", self.start_time, [None, None])

        osv_scan_run = _get_osv_scan_run()
        self.assertEqual(Status.STATUS_SUCCESS, osv_scan_run.status)
        self.assertEqual("Scanned 2 of 2 products.", osv_scan_run.message)
        self.assertEqual(self.start_time, osv_scan_run.start_time)
        self.assertGreaterEqual(osv_scan_run.duration, 3600000)
        mock_send_task_exception_notification.assert_not_called()
        self.assertIsNone(HUEY.get(OSV_SCAN_RUN_KEY, peek=True))

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.send_task_exception_notification")
    def test_failures(self, mock_send_task_exception_notification):
        failures = [f"product_{i}: 503 Error" for i in range(22)]

        task_osv_scan_summary.call_local("run", self.start_time, [None, SKIPPED] + failures)

        osv_scan_run = _get_osv_scan_run()
        self.assertEqual(Status.STATUS_FAILURE, osv_scan_run.status)
        self.assertEqual("Scanned 1 of 24 products, 22 failed, 1 not scanned.", osv_scan_run.message)
        mock_send_task_exception_notification.assert_called_once()
        message = str(mock_send_task_exception_notification.call_args.kwargs["exception"])
        self.assertTrue(message.startswith("OSV scanning failed for 22 of 24 products:\nproduct_0: 503 Error\n"))
        self.assertTrue(message.endswith("\nproduct_19: 503 Error\n... and 2 more"))

    def test_keeps_the_key_of_another_run(self):
        HUEY.put(OSV_SCAN_RUN_KEY, ("other_run", self.start_time, 2))

        task_osv_scan_summary.call_local("run", self.start_time, [None])

        self.assertEqual("other_run", HUEY.get(OSV_SCAN_RUN_KEY, peek=True)[0])

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_unfinished_run(self, mock_settings_load, mock_scan_product):
        settings = Settings()
        settings.feature_automatic_api_import = False
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = False
        mock_settings_load.return_value = settings
        mock_scan_product.return_value = (0, 0, 0)
        _create_product("product_osv")
        start_time = timezone.now() - timedelta(hours=21)
        HUEY.put(OSV_SCAN_RUN_KEY, ("lost_run", start_time, 5))

        task_api_import()

        unfinished_run = Periodic_Task.objects.get(task=OSV_SCAN_TASK_NAME, start_time=start_time)
        self.assertEqual(Status.STATUS_FAILURE, unfinished_run.status)
        self.assertEqual(
            "Did not finish, some scans of the 5 products were lost when the background tasks stopped.",
            unfinished_run.message,
        )
        self.assertEqual("Scanned 1 of 1 products.", _get_osv_scan_run().message)
        self.assertIsNone(HUEY.get(OSV_SCAN_RUN_KEY, peek=True))

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_younger_run_is_not_reported(self, mock_settings_load, mock_scan_product):
        settings = Settings()
        settings.feature_automatic_api_import = False
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = False
        mock_settings_load.return_value = settings
        mock_scan_product.return_value = (0, 0, 0)
        HUEY.put(OSV_SCAN_RUN_KEY, ("running_run", self.start_time, 5))

        task_api_import()

        self.assertFalse(Periodic_Task.objects.filter(task=OSV_SCAN_TASK_NAME, start_time=self.start_time).exists())
