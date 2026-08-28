from datetime import timedelta

from django.utils import timezone
from huey.contrib.djhuey import on_commit_task

from application.background_tasks.models import Periodic_Task
from application.background_tasks.services.task_base import delete_older_task_entries
from application.background_tasks.types import Status
from application.notifications.services.tasks import handle_task_exception
from application.rules.models import Rule
from application.rules.services.evaluator import evaluate_general_rule

TASK_NAME = "Evaluate general rule"


@on_commit_task()
def evaluate_general_rule_task(rule_id: int) -> None:
    _process_general_rule_evaluation(rule_id)


def _process_general_rule_evaluation(rule_id: int) -> None:
    task_record = Periodic_Task(
        task=TASK_NAME,
        start_time=timezone.now(),
        status=Status.STATUS_RUNNING,
    )
    task_record.save()

    delete_older_task_entries(TASK_NAME)

    try:
        rule = Rule.objects.filter(pk=rule_id, product__isnull=True).first()
        if rule:
            result = evaluate_general_rule(rule)
            message = (
                f"Rule '{rule.name}': {result.observations_processed} observations processed, "
                f"{result.observations_changed} changed"
            )
        else:
            message = f"General rule {rule_id} not found, nothing to evaluate"

        task_record.status = Status.STATUS_SUCCESS
        task_record.duration = (timezone.now() - task_record.start_time) / timedelta(milliseconds=1)
        task_record.message = message[:255]
        task_record.save()
    except Exception as e:
        task_record.status = Status.STATUS_FAILURE
        task_record.duration = (timezone.now() - task_record.start_time) / timedelta(milliseconds=1)
        task_record.message = str(e)[:255]
        task_record.save()

        handle_task_exception(e)
