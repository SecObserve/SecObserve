from importlib import import_module
from typing import Any, Callable, Optional

# Maps the name of a periodic task to the dotted path of its Huey task wrapper.
# The tasks are resolved lazily because importing the task modules reads the
# settings from the database, which fails on a not yet migrated database.
PERIODIC_TASKS: dict[str, str] = {
    "Import observations from API configurations, OSV and VulnerableCode": (
        "application.background_tasks.periodic_tasks.import_observations_tasks.task_api_import"
    ),
    "Import EPSS and cvss-bt": "application.background_tasks.periodic_tasks.epss_tasks.task_import_epss",
    "Import SPDX licenses": "application.background_tasks.periodic_tasks.license_tasks.task_spdx_license_import",
    "Branch housekeeping": "application.background_tasks.periodic_tasks.core_tasks.task_branch_housekeeping",
    "Expire risk acceptances": "application.background_tasks.periodic_tasks.core_tasks.task_expire_risk_acceptances",
    "Calculate product metrics": (
        "application.background_tasks.periodic_tasks.metrics_tasks.task_calculate_product_metrics"
    ),
}


def get_periodic_task(name: str) -> Optional[Callable[[], Any]]:
    dotted_path = PERIODIC_TASKS.get(name)
    if dotted_path is None:
        return None

    module_name, _, function_name = dotted_path.rpartition(".")
    return getattr(import_module(module_name), function_name)
