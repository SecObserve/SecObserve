from unittest.mock import patch

from application.background_tasks.models import Periodic_Task
from application.background_tasks.periodic_tasks.epss_tasks import task_import_epss
from application.rules.services.evaluator import EvaluationResult
from unittests.base_test_case import BaseTestCase


class TestEpssTasks(BaseTestCase):
    # ---------------------------------------------------------------
    # task_import_epss
    # ---------------------------------------------------------------

    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_cvss_bt")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.epss_apply_observations")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_epss")
    def test_task_import_epss(self, mock_import_epss, mock_epss_apply_observations, mock_import_cvss_bt):
        mock_import_cvss_bt.return_value = ("", [])

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
        mock_import_cvss_bt.return_value = ("", [])

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

    @patch("application.background_tasks.periodic_tasks.epss_tasks.apply_rules_to_enriched_observations")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_cvss_bt")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.epss_apply_observations")
    @patch("application.background_tasks.periodic_tasks.epss_tasks.import_epss")
    def test_task_import_epss_applies_rules(
        self, mock_import_epss, mock_epss_apply_observations, mock_import_cvss_bt, mock_apply_rules
    ):
        mock_import_epss.return_value = "Imported 4 EPSS scores."
        mock_epss_apply_observations.return_value = [1, 2]
        mock_import_cvss_bt.return_value = ("cvss-bt done", [2, 3])
        mock_apply_rules.return_value = EvaluationResult(observations_processed=3, observations_changed=1)

        task_import_epss()

        mock_apply_rules.assert_called_once_with({1, 2, 3})
        periodic_task = Periodic_Task.objects.get(task="Import EPSS and cvss-bt")
        self.assertEqual(
            "Imported 4 EPSS scores.\n"
            "Applied EPSS scores to 2 observations.\n"
            "cvss-bt done\n"
            "Rules applied to 3 observations, 1 changed.",
            periodic_task.message,
        )
