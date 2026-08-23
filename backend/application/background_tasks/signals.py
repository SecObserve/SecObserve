from typing import Any

from django.dispatch import receiver

from application.background_tasks.tracked_tasks.general_rule_evaluator import (
    evaluate_general_rule_task,
)
from application.rules.services.evaluator import general_rule_evaluation_requested


@receiver(general_rule_evaluation_requested)
def general_rule_evaluation_requested_handler(  # pylint: disable=unused-argument
    sender: Any, rule_id: int, **kwargs: Any
) -> None:
    # application.rules must not import application.background_tasks, so the API view requests the
    # evaluation through a signal instead of calling the task directly.
    evaluate_general_rule_task(rule_id)
