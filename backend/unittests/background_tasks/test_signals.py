import unittest
from unittest.mock import patch

from application.rules.services.evaluator import request_general_rule_evaluation


class TestGeneralRuleEvaluationRequested(unittest.TestCase):
    """
    application.rules must not import application.background_tasks, so the API view requests an
    evaluation through a signal. Nothing statically links the two sides, which is why the receiver
    connected in BackgroundTasksConfig.ready() is verified here.
    """

    @patch("application.background_tasks.signals.evaluate_general_rule_task")
    def test_receiver_enqueues_the_task(self, mock_evaluate_general_rule_task):
        request_general_rule_evaluation(42)

        mock_evaluate_general_rule_task.assert_called_once_with(42)
