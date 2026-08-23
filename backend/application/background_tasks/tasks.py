# Importing necessary modules for background tasks in Django, needed for auto-discovery of huey
import application.background_tasks.periodic_tasks.core_tasks  # noqa: F401 pylint: disable=unused-import
import application.background_tasks.periodic_tasks.epss_tasks  # noqa: F401 pylint: disable=unused-import
import application.background_tasks.periodic_tasks.import_observations_tasks  # noqa: F401 pylint: disable=unused-import
import application.background_tasks.periodic_tasks.license_tasks  # noqa: F401 pylint: disable=unused-import
import application.background_tasks.periodic_tasks.metrics_tasks  # noqa: F401 pylint: disable=unused-import
import application.background_tasks.tracked_tasks.general_rule_evaluator  # noqa: F401 pylint: disable=unused-import
