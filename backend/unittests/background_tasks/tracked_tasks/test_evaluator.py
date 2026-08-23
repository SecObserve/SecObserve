import unittest
from unittest.mock import ANY, MagicMock, patch

from application.background_tasks.tracked_tasks.general_rule_evaluator import (
    TASK_NAME,
    _process_general_rule_evaluation,
)
from application.background_tasks.types import Status
from application.rules.models import Rule
from application.rules.services.evaluator import EvaluationResult
from application.rules.types import Rule_Type


class TestProcessGeneralRuleEvaluation(unittest.TestCase):
    def setUp(self):
        self.rule = Rule(id=1, name="rule", type=Rule_Type.RULE_TYPE_FIELDS)

        self.mock_periodic_task = self._patch("application.background_tasks.tracked_tasks.evaluator.Periodic_Task")
        self.task_record = self.mock_periodic_task.return_value
        self.mock_delete_older_task_entries = self._patch(
            "application.background_tasks.tracked_tasks.evaluator.delete_older_task_entries"
        )
        self.mock_rule_objects = self._patch("application.background_tasks.tracked_tasks.evaluator.Rule.objects")
        self.mock_evaluate = self._patch("application.background_tasks.tracked_tasks.evaluator.evaluate_general_rule")
        self.mock_handle_task_exception = self._patch(
            "application.background_tasks.tracked_tasks.evaluator.handle_task_exception"
        )

    def _patch(self, target: str) -> MagicMock:
        patcher = patch(target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_success(self):
        self.mock_rule_objects.filter.return_value.first.return_value = self.rule
        self.mock_evaluate.return_value = EvaluationResult(observations_processed=5, observations_changed=2)

        _process_general_rule_evaluation(1)

        self.mock_periodic_task.assert_called_once_with(task=TASK_NAME, start_time=ANY, status=Status.STATUS_RUNNING)
        self.mock_delete_older_task_entries.assert_called_once_with(TASK_NAME)
        self.mock_rule_objects.filter.assert_called_once_with(pk=1, product__isnull=True)
        self.mock_evaluate.assert_called_once_with(self.rule)
        self.assertEqual(self.task_record.status, Status.STATUS_SUCCESS)
        self.assertEqual(self.task_record.message, "Rule 'rule': 5 observations processed, 2 changed")
        self.assertEqual(self.task_record.save.call_count, 2)
        self.mock_handle_task_exception.assert_not_called()

    def test_rule_not_found(self):
        self.mock_rule_objects.filter.return_value.first.return_value = None

        _process_general_rule_evaluation(1)

        self.mock_evaluate.assert_not_called()
        self.assertEqual(self.task_record.status, Status.STATUS_SUCCESS)
        self.assertEqual(self.task_record.message, "General rule 1 not found, nothing to evaluate")

    def test_exception(self):
        self.mock_rule_objects.filter.return_value.first.return_value = self.rule
        exception = Exception("something went wrong")
        self.mock_evaluate.side_effect = exception

        _process_general_rule_evaluation(1)

        self.assertEqual(self.task_record.status, Status.STATUS_FAILURE)
        self.assertEqual(self.task_record.message, "something went wrong")
        self.assertEqual(self.task_record.save.call_count, 2)
        self.mock_handle_task_exception.assert_called_once_with(exception)
