from unittest.mock import MagicMock, call, patch

from application.background_tasks.models import Periodic_Task
from application.background_tasks.periodic_tasks.import_observations_tasks import (
    task_api_import,
)
from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase

TASK_NAME = "Import observations from API configurations, OSV and VulnerableCode"


class TestImportObservationsTasks(BaseTestCase):
    def _get_task_message(self) -> str:
        # so_periodic_task swallows the return value of the task and stores it on the Periodic_Task
        # entry, so the composed message can only be asserted through the database.
        return Periodic_Task.objects.filter(task=TASK_NAME).latest("start_time").message

    # ---------------------------------------------------------------
    # task_api_import
    # ---------------------------------------------------------------

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_all_enabled(
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

        # Mock products
        mock_product_filter.return_value = [self.product_1]

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

        # Check OSV and VulnerableCode scanning was called
        mock_product_filter.assert_has_calls(
            [
                call(osv_enabled=True, automatic_osv_scanning_enabled=True),
                call(vulnerablecode_enabled=True, automatic_vulnerablecode_scanning_enabled=True),
            ]
        )
        mock_scan_product_osv.assert_called_once_with(self.product_1)
        mock_scan_product_vc.assert_called_once_with(self.product_1)

        # Check the composed message
        self.assertEqual(
            "Imported observations for 1 products from API configurations."
            "\nImported observations for 1 products from OSV scanning."
            "\nImported observations for 1 products from VulnerableCode scanning.",
            self._get_task_message(),
        )

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_api_disabled(
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
        settings.feature_automatic_api_import = False
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = "http://vulnerablecode.example.com"
        mock_settings_load.return_value = settings

        # Mock products
        mock_product = MagicMock()
        mock_product_filter.return_value = [mock_product]

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
        mock_product_filter.assert_has_calls(
            [
                call(osv_enabled=True, automatic_osv_scanning_enabled=True),
                call(vulnerablecode_enabled=True, automatic_vulnerablecode_scanning_enabled=True),
            ]
        )
        mock_scan_product_osv.assert_called_once_with(mock_product)
        mock_scan_product_vc.assert_called_once_with(mock_product)

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
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_vulnerablecode_disabled(
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
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = False
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
        mock_scan_product_osv.return_value = (4, 5, 6)  # new, updated, resolved

        # Execute
        task_api_import()

        # Assert
        # Check API import was called
        mock_api_config_filter.assert_called_once_with(automatic_import_enabled=True)
        mock_api_import_observations.assert_called_once()

        # Check VulnerableCode scanning was not called, but OSV scanning was
        mock_product_filter.assert_called_once_with(osv_enabled=True, automatic_osv_scanning_enabled=True)
        mock_scan_product_vc.assert_not_called()
        mock_scan_product_osv.assert_called_once_with(mock_product)

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_vulnerablecode_no_base_url(
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
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = True
        settings.vulnerablecode_base_url = ""
        mock_settings_load.return_value = settings

        # Mock API configurations
        mock_api_config = MagicMock()
        mock_api_config_filter.return_value = [mock_api_config]

        # Mock products
        mock_product = MagicMock()
        mock_product_filter.return_value = [mock_product]

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
        mock_product_filter.assert_called_once_with(osv_enabled=True, automatic_osv_scanning_enabled=True)
        mock_scan_product_vc.assert_not_called()
        mock_scan_product_osv.assert_called_once_with(mock_product)

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

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.handle_task_exception")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_osv_exception_handling(
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
        settings.feature_automatic_osv_scanning = True
        settings.feature_automatic_vulnerablecode_scanning = False
        mock_settings_load.return_value = settings

        # Mock products
        mock_product = MagicMock()
        mock_product_filter.return_value = [mock_product]

        # Mock scan_product to raise exception
        test_exception = Exception("Test OSV scanning exception")
        mock_scan_product.side_effect = test_exception

        # Execute
        task_api_import()

        # Assert
        # Check exception was handled
        mock_handle_task_exception.assert_called_once_with(test_exception, product=mock_product)

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
        self.assertTrue(self._get_task_message().endswith("\nVulnerableCode scanning failed for 1 products."))

    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.handle_task_exception")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.VulnerableCodeScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.OSVScanner.scan_product")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.api_import_observations")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Product.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Api_Configuration.objects.filter")
    @patch("application.background_tasks.periodic_tasks.import_observations_tasks.Settings.load")
    def test_task_api_import_all_failed(
        self,
        mock_settings_load,
        mock_api_config_filter,
        mock_product_filter,
        mock_api_import_observations,
        mock_scan_product_osv,
        mock_scan_product_vc,
        mock_handle_task_exception,
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

        # Mock products
        mock_product = MagicMock()
        mock_product_filter.return_value = [mock_product]

        # Mock every stage to raise an exception
        mock_api_import_observations.side_effect = Exception("Test API import exception")
        mock_scan_product_osv.side_effect = Exception("Test OSV scanning exception")
        mock_scan_product_vc.side_effect = Exception("Test VulnerableCode scanning exception")

        # Execute
        task_api_import()

        # Assert
        # Check every exception was handled
        self.assertEqual(3, mock_handle_task_exception.call_count)

        # All three failure messages together exceed the length of Periodic_Task.message,
        # so the message is truncated by so_periodic_task
        message = self._get_task_message()
        self.assertEqual(255, len(message))
        self.assertTrue(message.endswith(" ..."))

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
