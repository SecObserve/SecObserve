from application.background_tasks.services.registry import (
    PERIODIC_TASKS,
    get_periodic_task,
)
from application.background_tasks.services.task_base import PERIODIC_TASK_NAMES
from unittests.base_test_case import BaseTestCase


class TestRegistry(BaseTestCase):
    def test_registry_is_complete(self):
        # resolving imports the task modules, which populates PERIODIC_TASK_NAMES
        for name in PERIODIC_TASKS:
            self.assertIsNotNone(get_periodic_task(name))

        self.assertEqual(PERIODIC_TASK_NAMES, set(PERIODIC_TASKS.keys()))

    def test_get_periodic_task_unknown(self):
        self.assertIsNone(get_periodic_task("Unknown task"))
