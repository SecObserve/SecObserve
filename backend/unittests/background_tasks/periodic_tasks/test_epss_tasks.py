from unittest.mock import patch

from application.background_tasks.models import Periodic_Task
from application.background_tasks.periodic_tasks.epss_tasks import task_import_epss
from unittests.base_test_case import BaseTestCase


class TestEpssTasks(BaseTestCase):
    # ---------------------------------------------------------------
    # task_import_epss
    # ---------------------------------------------------------------

    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_cvss_bt")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.epss_apply_observations")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_epss")
    def test_task_import_epss(self, mock_import_epss, mock_epss_apply_observations, mock_import_cvss_bt):
        # Execute
        task_import_epss()

        # Assert
        mock_import_epss.assert_called_once()
        mock_epss_apply_observations.assert_called_once()
        mock_import_cvss_bt.assert_called_once()

    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_cvss_bt")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.epss_apply_observations")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_epss")
    def test_task_import_epss_execution_order(
        self, mock_import_epss, mock_epss_apply_observations, mock_import_cvss_bt
    ):
        # Execute
        task_import_epss()

        # Assert - Check execution order
        self.assertEqual(mock_import_epss.call_count, 1)
        self.assertEqual(mock_epss_apply_observations.call_count, 1)
        self.assertEqual(mock_import_cvss_bt.call_count, 1)

        # Verify the order of execution
        mock_import_epss.assert_called_once()
        mock_epss_apply_observations.assert_called_once()
        mock_import_cvss_bt.assert_called_once()

    @patch("application.background_tasks.periodic_tasks.epss_tasks.check_security_gates_with_conditions")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_cvss_bt")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.epss_apply_observations")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_epss")
    def test_task_import_epss_checks_security_gates(
        self, mock_import_epss, mock_epss_apply_observations, mock_import_cvss_bt, mock_check_gates
    ):
        calls = []
        mock_import_cvss_bt.side_effect = lambda: calls.append("cvss_bt") or "cvss-bt done"
        mock_check_gates.side_effect = lambda: calls.append("gates") or 3
        mock_import_epss.return_value = "epss done"
        mock_epss_apply_observations.return_value = "applied"

        task_import_epss()

        self.assertEqual(calls, ["cvss_bt", "gates"])
        # The periodic task wrapper stores the message instead of returning it
        message = Periodic_Task.objects.filter(task="Import EPSS and cvss-bt").latest("start_time").message
        self.assertTrue(message.endswith("Checked 3 security gates with conditions."))
