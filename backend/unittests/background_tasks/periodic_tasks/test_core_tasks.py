from unittest.mock import patch

from application.background_tasks.models import Periodic_Task
from application.background_tasks.periodic_tasks.core_tasks import (
    task_expire_risk_acceptances,
    task_housekeeping,
)
from unittests.base_test_case import BaseTestCase


class TestCoreTasks(BaseTestCase):
    # ---------------------------------------------------------------
    # task_branch_housekeeping
    # ---------------------------------------------------------------

    @patch("application.background_tasks.periodic_tasks.core_tasks.delete_old_webhook_deliveries")
    @patch("application.background_tasks.periodic_tasks.core_tasks.delete_orphaned_product_notifications")
    @patch("application.background_tasks.periodic_tasks.core_tasks.housekeeping")
    def test_task_branch_housekeeping(
        self, mock_delete_inactive_branches, mock_delete_product_notifications, mock_delete_webhook_deliveries
    ):
        # Setup
        mock_delete_inactive_branches.return_value = "Deleted 1 inactive branches in 2 products."
        mock_delete_product_notifications.return_value = 3
        mock_delete_webhook_deliveries.return_value = 4

        # Execute
        task_housekeeping()

        # Assert
        mock_delete_inactive_branches.assert_called_once()
        mock_delete_product_notifications.assert_called_once()
        periodic_task = Periodic_Task.objects.get(task="Housekeeping")
        self.assertEqual(
            "Deleted 1 inactive branches in 2 products.\nDeleted 3 orphaned product notifications."
            "\nDeleted 4 old webhook deliveries.",
            periodic_task.message,
        )

    # ---------------------------------------------------------------
    # task_expire_risk_acceptances
    # ---------------------------------------------------------------

    @patch("application.background_tasks.periodic_tasks.core_tasks.expire_risk_acceptances")
    def test_task_expire_risk_acceptances(self, mock_expire_risk_acceptances):
        # Execute
        task_expire_risk_acceptances()

        # Assert
        mock_expire_risk_acceptances.assert_called_once()
