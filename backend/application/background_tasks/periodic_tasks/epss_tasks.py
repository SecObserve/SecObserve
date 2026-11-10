from huey.contrib.djhuey import db_periodic_task

from application.background_tasks.services.crontab import crontab_in_time_zone
from application.background_tasks.services.task_base import so_periodic_task
from application.commons import settings_static
from application.commons.models import Settings
from application.epss.services.cvss_bt import import_cvss_bt
from application.epss.services.epss import epss_apply_observations, import_epss
from application.rules.services.evaluator import apply_rules_to_enriched_observations


@db_periodic_task(
    crontab_in_time_zone(
        minute=settings_static.background_epss_import_crontab_minute,
        hour=settings_static.background_epss_import_crontab_hour,
    )
)
@so_periodic_task("Import EPSS and cvss-bt")
def task_import_epss() -> str:
    settings = Settings.load()
    message = import_epss() + "\n"
    num_changed, crossed = epss_apply_observations(settings.apply_rules_epss_step)
    message += f"Applied EPSS scores to {num_changed} observations.\n"
    changed_exploit: list[int] = []
    try:
        cvss_bt_message, changed_exploit = import_cvss_bt()
        message += cvss_bt_message + "\n"
    finally:
        result = apply_rules_to_enriched_observations(set(crossed) | set(changed_exploit))
    message += f"Rules applied to {result.observations_processed} observations, {result.observations_changed} changed."
    return message
