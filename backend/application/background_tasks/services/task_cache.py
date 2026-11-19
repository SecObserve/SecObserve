from typing import Any, Optional

from huey.api import Task
from huey.contrib.djhuey import post_execute, pre_execute

from application.commons.services.request_cache import (
    activate_task_cache,
    deactivate_task_cache,
)

# Background tasks have no request, so functions decorated with cache_for_request (e.g. Settings.load())
# would hit the database for each call. These hooks give every task execution its own cache instead.


@pre_execute(name="activate_task_cache")
def activate_cache(task: Task) -> None:  # pylint: disable=unused-argument
    activate_task_cache()


@post_execute(name="deactivate_task_cache")
def deactivate_cache(task: Task, task_value: Any, exc: Optional[Exception]) -> None:  # pylint: disable=unused-argument
    deactivate_task_cache()
